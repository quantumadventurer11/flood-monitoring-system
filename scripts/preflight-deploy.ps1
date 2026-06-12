param(
  [string]$BackendUrl = "",
  [string]$VercelUrl = "",
  [switch]$SkipBackendTests,
  [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ExpectedBranch = "codex/gloc-2026-validation-fixes"
$BannedPattern = "plain language|Plain-language|non-technical|nontechnical|simple|friendly|explainable|SpacexAI member|aerospace-grade"

function Invoke-Checked {
  param(
    [string]$Name,
    [scriptblock]$Script
  )
  Write-Host "`n==> $Name" -ForegroundColor Cyan
  & $Script
  Write-Host "OK: $Name" -ForegroundColor Green
}

function Test-CommandAvailable {
  param([string]$CommandName)
  if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
    throw "Required command '$CommandName' was not found on PATH."
  }
}

function Test-Url {
  param([string]$Url)
  return Invoke-RestMethod -Uri $Url -TimeoutSec 30
}

Push-Location $RepoRoot
try {
  Invoke-Checked "Required tools" {
    Test-CommandAvailable git
    Test-CommandAvailable npm
    Test-CommandAvailable python
    Test-CommandAvailable rg
  }

  Invoke-Checked "Git branch and secret hygiene" {
    $branch = (git branch --show-current).Trim()
    if ($branch -ne $ExpectedBranch) {
      throw "Expected branch '$ExpectedBranch', currently on '$branch'."
    }
    $trackedEnv = git ls-files .env
    if ($trackedEnv) {
      throw ".env is tracked by git; remove it before deploying."
    }
    git status --short
  }

  Invoke-Checked "Banned wording scan" {
    $matches = rg -n $BannedPattern frontend/src backend/app README.md DEPLOYMENT.md 2>$null
    if ($LASTEXITCODE -eq 0) {
      Write-Output $matches
      throw "Banned wording found."
    }
    if ($LASTEXITCODE -gt 1) {
      throw "rg failed while scanning for banned wording."
    }
  }

  if (-not $SkipBackendTests) {
    Invoke-Checked "Backend tests" {
      Push-Location (Join-Path $RepoRoot "backend")
      try {
        pytest
      } finally {
        Pop-Location
      }
    }
  }

  if (-not $SkipFrontendBuild) {
    Invoke-Checked "Frontend production build" {
      Push-Location (Join-Path $RepoRoot "frontend")
      try {
        if ($BackendUrl) {
          $previous = $env:VITE_API_URL
          $env:VITE_API_URL = $BackendUrl.TrimEnd("/")
          npm run build
          $env:VITE_API_URL = $previous
        } else {
          npm run build
        }
      } finally {
        Pop-Location
      }
    }
  }

  if ($BackendUrl) {
    $api = $BackendUrl.TrimEnd("/")
    Invoke-Checked "Managed backend health" {
      $health = Test-Url "$api/health"
      if ($health.status -ne "ok") {
        throw "Backend health returned unexpected payload: $($health | ConvertTo-Json -Compress)"
      }
    }

    Invoke-Checked "Managed backend model status" {
      $status = Test-Url "$api/model-status"
      if ($status.backend_status -ne "ok") {
        throw "Model status returned unexpected payload: $($status | ConvertTo-Json -Compress)"
      }
      if (-not $status.model_artifact_present -and -not $status.model_loaded) {
        throw "Model status did not report an available XGBoost model."
      }
      if ($status.fallback_active) {
        Write-Host "Warning: hosted backend is in fallback proxy mode. Set COPERNICUS_USER and COPERNICUS_PASSWORD in Render for Sentinel-backed inference." -ForegroundColor Yellow
      }
    }

    Invoke-Checked "Bangladesh local validation scenario" {
      $scenario = Test-Url "$api/validation/scenarios/bangladesh-2024"
      if ($scenario.prediction.data_source -ne "local_unosat_ground_truth") {
        throw "Unexpected scenario data_source: $($scenario.prediction.data_source)"
      }
      if ($scenario.model_hotspots.Count -ne 0) {
        throw "Expected model_hotspots to be empty for the local-data scenario."
      }
      if (-not $scenario.ground_truth_hotspots[0].flood_class) {
        throw "Missing flood_class on first flood coordinate."
      }
      if (-not $scenario.ground_truth_hotspots[0].details -or -not $scenario.ground_truth_hotspots[0].data) {
        throw "Missing details/data on first flood coordinate."
      }
    }
  } else {
    Write-Host "`nSkipping managed backend smoke checks because -BackendUrl was not provided." -ForegroundColor Yellow
  }

  if ($VercelUrl) {
    $site = $VercelUrl.TrimEnd("/")
    Invoke-Checked "Vercel frontend health" {
      $response = Invoke-WebRequest -Uri $site -UseBasicParsing -TimeoutSec 30
      if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "Vercel site returned HTTP $($response.StatusCode)."
      }
    }
  }
} finally {
  Pop-Location
}

Write-Host "`nPreflight complete." -ForegroundColor Green

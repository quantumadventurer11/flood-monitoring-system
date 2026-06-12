param(
  [Parameter(Mandatory = $true)]
  [string]$BackendUrl,
  [switch]$Production,
  [switch]$InstallVercelCli,
  [switch]$SkipPreflight
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendRoot = Join-Path $RepoRoot "frontend"
$BackendApi = $BackendUrl.TrimEnd("/")

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
  return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

Push-Location $RepoRoot
try {
  if (-not $SkipPreflight) {
    Invoke-Checked "Deployment preflight" {
      & (Join-Path $RepoRoot "scripts\preflight-deploy.ps1") -BackendUrl $BackendApi
    }
  }

  Invoke-Checked "Vercel CLI availability" {
    if (-not (Test-CommandAvailable vercel)) {
      if ($InstallVercelCli) {
        npm install -g vercel
      } else {
        throw "Vercel CLI is not installed. Run 'npm install -g vercel' or rerun with -InstallVercelCli."
      }
    }
  }

  Push-Location $FrontendRoot
  try {
    Invoke-Checked "Link Vercel project" {
      vercel link
    }

    Invoke-Checked "Set production VITE_API_URL" {
      $envList = vercel env ls production
      if ($envList -match "VITE_API_URL") {
        Write-Host "VITE_API_URL already exists in Vercel production. Updating it."
        vercel env rm VITE_API_URL production --yes
      }
      $BackendApi | vercel env add VITE_API_URL production
    }

    Invoke-Checked "Deploy frontend to Vercel" {
      if ($Production) {
        vercel --prod
      } else {
        vercel
      }
    }
  } finally {
    Pop-Location
  }
} finally {
  Pop-Location
}

Write-Host "`nVercel deployment command completed. Copy the deployment URL printed by Vercel, then set Render ALLOWED_ORIGINS to that URL." -ForegroundColor Green

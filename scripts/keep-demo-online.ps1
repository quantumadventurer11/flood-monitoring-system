param(
  [int]$IntervalSeconds = 60,
  [switch]$Once
)

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $RepoRoot
$LogPath = Join-Path $WorkspaceRoot "demo-watchdog.log"
$ServerLog = Join-Path $WorkspaceRoot "public-demo-server-3005.log"
$ServerErr = Join-Path $WorkspaceRoot "public-demo-server-3005.err.log"
$TunnelSubdomain = "gloc2026-flood-monitor"
$TunnelLog = Join-Path $WorkspaceRoot "tunnel-$TunnelSubdomain.log"
$TunnelErr = Join-Path $WorkspaceRoot "tunnel-$TunnelSubdomain.err.log"
$PublicUrl = "https://$TunnelSubdomain.loca.lt"

function Write-WatchLog([string]$Message) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  Add-Content -Path $LogPath -Value $line
  Write-Output $line
}

function Test-Url([string]$Url) {
  try {
    $headers = @{ "bypass-tunnel-reminder" = "true" }
    $response = Invoke-WebRequest $Url -Headers $headers -TimeoutSec 15
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
  } catch {
    return $false
  }
}

function Wait-Url([string]$Url, [int]$Attempts = 6, [int]$DelaySeconds = 5) {
  for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    if (Test-Url $Url) { return $true }
    Start-Sleep -Seconds $DelaySeconds
  }
  return $false
}

function Ensure-Docker {
  docker info *> $null
  if ($LASTEXITCODE -eq 0) { return $true }

  Write-WatchLog "Docker is not reachable. Attempting to start Docker Desktop."
  $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dockerDesktop) {
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    Start-Sleep -Seconds 25
  }

  docker info *> $null
  if ($LASTEXITCODE -eq 0) { return $true }
  Write-WatchLog "Docker is still unavailable; backend cannot be restarted until Docker Desktop is ready."
  return $false
}

function Ensure-Backend {
  if (Test-Url "http://localhost:8000/health") { return }
  if (-not (Ensure-Docker)) { return }
  Write-WatchLog "Backend health check failed. Starting Docker backend stack."
  Push-Location $RepoRoot
  try {
    docker compose -f docker-compose.local.yml up -d --build backend
  } finally {
    Pop-Location
  }
}

function Ensure-DemoServer {
  if (Test-Url "http://localhost:3005/api/health") { return }
  Write-WatchLog "Public demo server is down. Starting static/proxy server on port 3005."
  Start-Process -FilePath node -ArgumentList "scripts/public-demo-server.mjs" -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $ServerLog -RedirectStandardError $ServerErr
  Start-Sleep -Seconds 3
}

function Get-TunnelProcesses {
  Get-CimInstance Win32_Process -Filter "name = 'node.exe'" |
    Where-Object { $_.CommandLine -match "localtunnel" -and $_.CommandLine -match $TunnelSubdomain }
}

function Restart-Tunnel {
  Get-TunnelProcesses | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force } catch {}
  }
  Write-WatchLog "Starting named localtunnel at $PublicUrl."
  Start-Process -FilePath npx.cmd -ArgumentList "localtunnel","--port","3005","--local-host","127.0.0.1","--subdomain",$TunnelSubdomain -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $TunnelLog -RedirectStandardError $TunnelErr
  $null = Wait-Url "$PublicUrl/api/health" 6 5
}

function Ensure-Tunnel {
  if (Test-Url "$PublicUrl/api/health") { return }
  $processes = @(Get-TunnelProcesses)
  if ($processes.Count -eq 0) {
    Restart-Tunnel
    return
  }
  Write-WatchLog "Named tunnel process exists but public health failed. Restarting tunnel."
  Restart-Tunnel
}

function Invoke-WatchdogCycle {
  Ensure-Backend
  Ensure-DemoServer
  Ensure-Tunnel
  if (Wait-Url "$PublicUrl/api/health" 3 4) {
    Write-WatchLog "Public demo healthy: $PublicUrl"
  } else {
    Write-WatchLog "Public demo is still unhealthy after recovery attempt."
  }
}

do {
  Invoke-WatchdogCycle
  if ($Once) { break }
  Start-Sleep -Seconds $IntervalSeconds
} while ($true)

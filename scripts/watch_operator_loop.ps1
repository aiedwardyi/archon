$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$stopFile = Join-Path $repoRoot "operator-loop.stop"
$watchdogLog = Join-Path $repoRoot "eval\results\operator_watchdog.log"
$loopLog = Join-Path $repoRoot "eval\results\operator_loop_live.log"

function Write-WatchdogLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $watchdogLog -Value "[$timestamp] $Message"
}

Write-WatchdogLog "watchdog starting"

while ($true) {
    if (Test-Path $stopFile) {
        Write-WatchdogLog "stop file detected, watchdog exiting"
        Remove-Item $stopFile -Force
        break
    }

    Write-WatchdogLog "starting operator loop child"
    & $pythonExe `
        "eval\operator_loop.py" `
        "--expected-branch" "eval/loops" `
        "--archetypes" "dashboard" "game" "saas_landing" "ecommerce" "portfolio" "fintech" "editor" "form" `
        "--max-cycles" "0" *>> $loopLog

    $exitCode = $LASTEXITCODE
    Write-WatchdogLog "operator loop child exited with code $exitCode"

    if (Test-Path $stopFile) {
        Write-WatchdogLog "stop file detected after child exit, watchdog exiting"
        Remove-Item $stopFile -Force
        break
    }

    Start-Sleep -Seconds 15
}

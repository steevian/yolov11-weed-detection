param()

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$backendProcess = $null
$frontendProcess = $null

try {
    $rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $backendDir = Join-Path $rootDir 'yolo_weed_detection_flask'
    $frontendDir = Join-Path $rootDir 'yolo_weed_detection_vue'

    if (-not (Test-Path $backendDir)) {
        throw "Backend directory not found: $backendDir"
    }

    if (-not (Test-Path $frontendDir)) {
        throw "Frontend directory not found: $frontendDir"
    }

    if (-not (Test-Path (Join-Path $backendDir 'main.py'))) {
        throw "Backend entry not found: $(Join-Path $backendDir 'main.py')"
    }

    if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
        throw "Frontend entry not found: $(Join-Path $frontendDir 'package.json')"
    }

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Command not found: python. Install Python and add it to PATH."
    }

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "Command not found: npm. Install Node.js and add npm to PATH."
    }

    $env:PORT = '8080'
    $env:VITE_FLASK_BASE_URL = 'http://localhost:8080'

    Write-Host 'Starting backend...'
    $backendCmd = "Set-Location -LiteralPath '$backendDir'; `$env:PORT='8080'; python main.py"
    $backendProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $backendCmd) -PassThru

    if ($null -eq $backendProcess) {
        throw 'Failed to start backend process.'
    }

    Write-Host 'Waiting 3 seconds before starting frontend...'
    Start-Sleep -Seconds 3

    Write-Host 'Starting frontend...'
    $frontendCmd = "Set-Location -LiteralPath '$frontendDir'; `$env:VITE_FLASK_BASE_URL='http://localhost:8080'; npm run dev"
    $frontendProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $frontendCmd) -PassThru

    if ($null -eq $frontendProcess) {
        throw 'Failed to start frontend process.'
    }

    Write-Host ''
    Write-Host '=== Access URLs ==='
    Write-Host 'Backend: http://192.168.0.102:8080'
    Write-Host 'Frontend (HTTPS): https://192.168.0.102:5173/'
    Write-Host '===================='
    Write-Host 'Services are running. Press Ctrl+C to stop.'
    Write-Host ''

    while ($true) {
        Start-Sleep -Seconds 1
    }
}
catch {
    Write-Error $_.Exception.Message
    Write-Host 'Troubleshooting:'
    Write-Host '1) Check Python: python --version'
    Write-Host '2) Check npm: npm -v'
    Write-Host '3) Check directories and entry files'
    exit 1
}
finally {
    foreach ($proc in @($frontendProcess, $backendProcess)) {
        if ($null -ne $proc) {
            try {
                if (-not $proc.HasExited) {
                    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                    Write-Host "Stopped process PID=$($proc.Id)"
                }
            }
            catch {
                Write-Warning "Failed to stop PID=$($proc.Id): $($_.Exception.Message)"
            }
        }
    }

    Write-Host 'Shutdown complete.'
}

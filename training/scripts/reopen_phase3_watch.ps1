$ErrorActionPreference = 'Stop'

$repo = 'D:\cyd\Desktop\yolo_web-main'
Set-Location $repo

$stdoutLog = Join-Path $repo 'experiments\logs\phase3_resilient_stdout.log'
$stderrLog = Join-Path $repo 'experiments\logs\phase3_resilient_stderr.log'

Write-Host '[WATCH] Phase3 reopen watch started.'
Write-Host "[WATCH] stdout: $stdoutLog"
Write-Host "[WATCH] stderr: $stderrLog"

if (Test-Path $stdoutLog) {
    Write-Host '[WATCH] tail stdout...'
    Get-Content $stdoutLog -Tail 80
}

if (Test-Path $stderrLog) {
    Write-Host '[WATCH] tail stderr...'
    Get-Content $stderrLog -Tail 80
}

Write-Host '[WATCH] following stderr (active progress)...'
while ($true) {
    if (Test-Path $stderrLog) {
        Get-Content $stderrLog -Wait -Tail 120
        break
    }
    Start-Sleep -Seconds 2
}

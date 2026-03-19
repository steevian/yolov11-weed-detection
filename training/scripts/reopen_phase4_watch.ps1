param(
    [switch]$IncludeHistory,
    [int]$HistoryLines = 80
)

$ErrorActionPreference = 'Stop'

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
chcp 65001 > $null

$repo = 'D:\cyd\Desktop\yolo_web-main'
Set-Location $repo

$stdoutLog = Join-Path $repo 'experiments\logs\phase4_resilient_stdout.log'
$stderrLog = Join-Path $repo 'experiments\logs\phase4_resilient_stderr.log'

Write-Host '[WATCH] Phase4 reopen watch started.'
Write-Host "[WATCH] stdout: $stdoutLog"
Write-Host "[WATCH] stderr: $stderrLog"

if ($IncludeHistory.IsPresent -and (Test-Path $stdoutLog)) {
    Write-Host "[WATCH] history tail stdout ($HistoryLines lines)..."
    Get-Content $stdoutLog -Encoding UTF8 -Tail $HistoryLines
}

Write-Host '[WATCH] following stdout (real-time progress from now)...'
while ($true) {
    if (Test-Path $stdoutLog) {
        Get-Content $stdoutLog -Encoding UTF8 -Wait -Tail 0
        break
    }
    Start-Sleep -Seconds 2
}

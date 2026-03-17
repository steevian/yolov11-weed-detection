param(
    # 功能简介：默认只显示“从现在开始”的实时训练进度，避免先刷一屏历史日志。
    [switch]$IncludeHistory,
    [int]$HistoryLines = 80
)

$ErrorActionPreference = 'Stop'

# 强制UTF-8，尽量避免PowerShell终端中的中文和进度条乱码。
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
chcp 65001 > $null

$repo = 'D:\cyd\Desktop\yolo_web-main'
Set-Location $repo

$stdoutLog = Join-Path $repo 'experiments\logs\phase3_resilient_stdout.log'
$stderrLog = Join-Path $repo 'experiments\logs\phase3_resilient_stderr.log'

Write-Host '[WATCH] Phase3 reopen watch started.'
Write-Host "[WATCH] stdout: $stdoutLog"
Write-Host "[WATCH] stderr: $stderrLog"

if ($IncludeHistory.IsPresent -and (Test-Path $stdoutLog)) {
    Write-Host "[WATCH] history tail stdout ($HistoryLines lines)..."
    Get-Content $stdoutLog -Encoding UTF8 -Tail $HistoryLines
}

Write-Host '[WATCH] following stdout (real-time progress from now)...'
while ($true) {
    if (Test-Path $stdoutLog) {
        # -Tail 0 表示不回放历史，只跟踪新增行。
        Get-Content $stdoutLog -Encoding UTF8 -Wait -Tail 0
        break
    }
    Start-Sleep -Seconds 2
}

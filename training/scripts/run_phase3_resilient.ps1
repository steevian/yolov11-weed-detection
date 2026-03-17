<#
功能简介：
1) 守护式启动 Phase3 训练，异常自动重试并保留失败记录；
2) 支持 fresh/resume 两种模式，确保可续训与抗中断；
3) 将关键事件写入 docs/trianlog.md，便于实验追踪与审计。
#>

param(
    [string]$Repo = 'D:\cyd\Desktop\yolo_web-main',
    [string]$PythonExe = 'C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe',
    [ValidateSet('fresh','resume')]
    [string]$Mode = 'fresh',
    [string]$Checkpoint = '',
    [int]$MaxRestarts = 500,
    [int]$Epochs = 200,
    [int]$Workers = 1,
    [int]$Batch = 6,
    [string]$CacheMode = 'disk',
    [string]$Device = '0',
    [int]$RetryDelaySeconds = 20,
    [int]$GpuFailureCooldownSeconds = 60,
    [string]$FailureLogDir = 'D:/cyd/Desktop/yolo_web-main/experiments/logs/phase3_failures',
    [switch]$Amp
)

$ErrorActionPreference = 'Stop'

# 尽量统一为UTF-8输出，减少日志在不同终端下的乱码问题。
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
chcp 65001 > $null
$env:PYTHONUTF8 = '1'

$env:KMP_DUPLICATE_LIB_OK = 'TRUE'
Set-Location $Repo

$trianlog = Join-Path $Repo 'docs/trianlog.md'
if (-not (Test-Path $trianlog)) {
    New-Item -ItemType File -Path $trianlog -Force | Out-Null
}

New-Item -ItemType Directory -Force $FailureLogDir | Out-Null

function Write-Trianlog {
    param([string]$Title, [string[]]$Lines)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $trianlog -Encoding UTF8 -Value "## $ts | $Title"
    Add-Content -Path $trianlog -Encoding UTF8 -Value ""
    foreach ($line in $Lines) {
        Add-Content -Path $trianlog -Encoding UTF8 -Value "- $line"
    }
    Add-Content -Path $trianlog -Encoding UTF8 -Value ""
}

function Get-GpuSnapshot {
    try {
        return (nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | Out-String).Trim()
    }
    catch {
        return 'N/A'
    }
}

function Resolve-LatestCheckpoint {
    $latest = Get-ChildItem -Path (Join-Path $Repo 'experiments/YOLOv11-S-MBV3') -Filter last.pt -Recurse -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $latest) {
        return $null
    }
    return $latest.FullName.Replace('\\', '/')
}

if ($Mode -eq 'resume') {
    if ([string]::IsNullOrWhiteSpace($Checkpoint)) {
        $Checkpoint = Resolve-LatestCheckpoint
        if ([string]::IsNullOrWhiteSpace($Checkpoint)) {
            throw 'No resumable checkpoint found under experiments/YOLOv11-S-MBV3'
        }
    }

    if (-not (Test-Path $Checkpoint)) {
        throw "Checkpoint not found: $Checkpoint"
    }
}

Write-Host '[RESILIENT] Phase3 resilient resume started.'
Write-Host "[RESILIENT] mode=$Mode"
Write-Host "[RESILIENT] checkpoint=$Checkpoint"
Write-Host "[RESILIENT] epochs=$Epochs, workers=$Workers, batch=$Batch, cache=$CacheMode, device=$Device, maxRestarts=$MaxRestarts"
Write-Trianlog -Title 'Phase3 watchdog start' -Lines @(
    "mode=$Mode",
    "checkpoint=$Checkpoint",
    "epochs=$Epochs, batch=$Batch, workers=$Workers, cache=$CacheMode, device=$Device"
)

for ($attempt = 1; $attempt -le $MaxRestarts; $attempt++) {
    Write-Host "[RESILIENT] attempt $attempt/$MaxRestarts"

    $cmdArgs = @(
        "$Repo\training\scripts\phase3_train_yolo11s_mbv3.py",
        '--epochs', $Epochs,
        '--workers', $Workers,
        '--batch', $Batch,
        '--cache', $CacheMode,
        '--device', $Device
    )

    if ($Amp.IsPresent) {
        $cmdArgs += '--amp'
    }

    if ($Mode -eq 'resume') {
        $cmdArgs += '--resume'
        $cmdArgs += '--checkpoint'
        $cmdArgs += $Checkpoint
    }

    & $PythonExe @cmdArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host '[RESILIENT] training completed successfully.'
        Write-Trianlog -Title 'Phase3 watchdog completed' -Lines @("attempt=$attempt", 'exit_code=0')
        exit 0
    }

    if ($Mode -eq 'resume' -and -not (Test-Path $Checkpoint)) {
        throw "[RESILIENT] checkpoint disappeared after failure, cannot resume: $Checkpoint"
    }

    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $failureFile = Join-Path $FailureLogDir "attempt_${attempt}_${ts}.log"
    if ($Mode -eq 'resume' -and (Test-Path $Checkpoint)) {
        $checkpointInfo = Get-Item $Checkpoint | Select-Object FullName, LastWriteTime, Length
    }
    else {
        $checkpointInfo = [PSCustomObject]@{
            FullName = 'N/A'
            LastWriteTime = 'N/A'
            Length = 'N/A'
        }
    }
    @(
        "exit_code=$exitCode"
        "attempt=$attempt"
        "mode=$Mode"
        "timestamp=$ts"
        "gpu_snapshot=$(Get-GpuSnapshot)"
        "checkpoint_path=$($checkpointInfo.FullName)"
        "checkpoint_last_write=$($checkpointInfo.LastWriteTime)"
        "checkpoint_size=$($checkpointInfo.Length)"
    ) | Set-Content -Path $failureFile -Encoding UTF8

    $delay = $RetryDelaySeconds
    $retryTitle = 'Phase3 watchdog retry'
    if ($exitCode -eq 12) {
        $delay = [Math]::Max($RetryDelaySeconds, $GpuFailureCooldownSeconds)
        $retryTitle = 'Phase3 watchdog gpu-memory retry'
    }

    Write-Warning "[RESILIENT] training exited with code $exitCode, retrying in $delay seconds... details: $failureFile"
    Write-Trianlog -Title $retryTitle -Lines @(
        "attempt=$attempt",
        "exit_code=$exitCode",
        "failure_file=$failureFile",
        "retry_delay_seconds=$delay"
    )

    # 关键修复：fresh 首次失败后自动切到 resume，后续重试沿用同一 run 的 checkpoint。
    if ($Mode -eq 'fresh') {
        $resumeCkpt = Resolve-LatestCheckpoint
        if (-not [string]::IsNullOrWhiteSpace($resumeCkpt) -and (Test-Path $resumeCkpt)) {
            $Mode = 'resume'
            $Checkpoint = $resumeCkpt
            Write-Host "[RESILIENT] switched to resume mode after failure. checkpoint=$Checkpoint"
            Write-Trianlog -Title 'Phase3 watchdog switched to resume' -Lines @(
                "attempt=$attempt",
                "checkpoint=$Checkpoint"
            )
        }
    }

    Start-Sleep -Seconds $delay
}

Write-Trianlog -Title 'Phase3 watchdog failed' -Lines @("max_restarts=$MaxRestarts")
throw "[RESILIENT] exceeded max restart attempts: $MaxRestarts"

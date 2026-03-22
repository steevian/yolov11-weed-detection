<#
功能简介：
1) 先等待 ECA2 中断 smoke50 续训收口（恢复链路验证）；
2) 再自动启动 ECA2 公平口径 full200 训练（抗中断守护）；
3) full200 完成后自动评测并更新 firstmemory。
#>

param(
    [string]$Repo = 'D:\cyd\Desktop\yolo_web-main',
    [string]$SmokeRunDir = 'D:/cyd/Desktop/yolo_web-main/runs/detect/experiments/YOLOv11-S-MBV3-ECA2/mbv3_eca2_smoke50_20260319_184000',
    [int]$SmokeTargetEpochs = 50,
    [int]$FullEpochs = 200,
    [int]$Workers = 1,
    [int]$Batch = 6,
    [string]$CacheMode = 'disk',
    [string]$Device = '0',
    [int]$MaxRestarts = 500,
    [int]$RetryDelaySeconds = 20,
    [string]$UltralyticsRoot = 'D:/cyd/Desktop/yolo_web-main/training/ultralytics_custom',
    [string]$OldEcaWeights = 'D:/cyd/Desktop/yolo_web-main/experiments/YOLOv11-S-MBV3-ECA/mbv3_eca_20260317_114514/weights/best.pt'
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
chcp 65001 > $null
$env:PYTHONUTF8 = '1'
$env:KMP_DUPLICATE_LIB_OK = 'TRUE'

$pythonExe = 'C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe'
$smokeSummary = Join-Path $SmokeRunDir 'run_summary.json'
$smokeBest = Join-Path $SmokeRunDir 'weights/best.pt'
$smokeResults = Join-Path $SmokeRunDir 'results.csv'

Write-Host '[PIPELINE] wait smoke resume completion...'
while ($true) {
    $status = $null
    if (Test-Path $smokeSummary) {
        try {
            $status = (Get-Content $smokeSummary -Raw | ConvertFrom-Json).status
        }
        catch {
            $status = $null
        }
    }

    $epochsDone = 0
    if (Test-Path $smokeResults) {
        $lines = (Get-Content $smokeResults | Measure-Object -Line).Lines
        if ($lines -gt 1) {
            $epochsDone = $lines - 1
        }
    }

    Write-Host "[PIPELINE] smoke status=$status epochs_done=$epochsDone/$SmokeTargetEpochs"

    if (($status -eq 'completed' -and (Test-Path $smokeBest)) -or ((Test-Path $smokeBest) -and $epochsDone -ge $SmokeTargetEpochs)) {
        break
    }

    Start-Sleep -Seconds 30
}

Write-Host '[PIPELINE] smoke stage completed. start full200 resilient training...'

powershell -NoProfile -ExecutionPolicy Bypass -File "$Repo/training/scripts/run_phase4_resilient.ps1" `
    -Repo $Repo `
    -Mode fresh `
    -Epochs $FullEpochs `
    -Workers $Workers `
    -Batch $Batch `
    -CacheMode $CacheMode `
    -Device $Device `
    -MaxRestarts $MaxRestarts `
    -RetryDelaySeconds $RetryDelaySeconds `
    -UltralyticsRoot $UltralyticsRoot

if ($LASTEXITCODE -ne 0) {
    throw "[PIPELINE] full200 resilient training failed with exit code $LASTEXITCODE"
}

$fullRoot = Join-Path $Repo 'experiments/YOLOv11-S-MBV3-ECA2'
$latestFull = Get-ChildItem -Path $fullRoot -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $latestFull) {
    throw '[PIPELINE] no full200 run directory found in experiments/YOLOv11-S-MBV3-ECA2'
}

Write-Host "[PIPELINE] full200 completed run_dir=$($latestFull.FullName)"

& $pythonExe "$Repo/training/scripts/phase4_eca2_smoke50_postprocess.py" `
    --new-run-dir "$($latestFull.FullName.Replace('\\','/'))" `
    --old-eca-weights "$OldEcaWeights" `
    --data "$Repo/training/configs/data_3seasonweeddet10.yaml" `
    --imgsz 640 `
    --batch 1 `
    --workers 0 `
    --warmup 10 `
    --iters 100 `
    --target-epochs 200 `
    --poll-seconds 20 `
    --wait-timeout-hours 24 `
    --ultralytics-root "$UltralyticsRoot" `
    --plan-label resumed_50_to_200

if ($LASTEXITCODE -ne 0) {
    throw "[PIPELINE] postprocess failed with exit code $LASTEXITCODE"
}

Write-Host '[PIPELINE] ECA2 resume50->full200->postprocess completed.'

param(
    [ValidateSet('baseline', 'mbv3', 'eca')]
    [string]$Model = 'baseline',
    [string]$RunDir = '',
    [int]$RefreshSeconds = 5
)

if ([string]::IsNullOrWhiteSpace($RunDir)) {
    $RunDir = "D:/cyd/Desktop/yolo_web-main/exp1/runs/$Model"
}

$resultsCsv = Join-Path $RunDir 'results.csv'
$argsYaml = Join-Path $RunDir 'args.yaml'
$weightsDir = Join-Path $RunDir 'weights'

function Get-TrainProcess {
    param([string]$TargetModel)
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match 'python' -and
            $_.CommandLine -match 'exp1/train.py' -and
            $_.CommandLine -match "--model\s+$TargetModel($|\s)"
        } |
        Select-Object -First 1
}

function Get-LastCsvRow {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $lines = Get-Content $Path
    if ($lines.Count -lt 2) { return $null }
    return $lines[-1]
}

function Get-EpochProgress {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 'N/A' }
    $lines = Get-Content $Path
    if ($lines.Count -lt 2) { return 'N/A' }
    $last = $lines[-1]
    $parts = $last -split ','
    if ($parts.Count -lt 1) { return 'N/A' }
    $epoch = $parts[0]
    return "$epoch/200"
}

function Get-RecentWriteSeconds {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $item = Get-Item $Path
    $delta = (New-TimeSpan -Start $item.LastWriteTime -End (Get-Date)).TotalSeconds
    return [int][Math]::Round($delta)
}

while ($true) {
    Clear-Host
    Write-Host ('=' * 80)
    Write-Host ('Train Progress Watch  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
    Write-Host ('Model: ' + $Model)
    Write-Host ('RunDir: ' + $RunDir)
    Write-Host ('=' * 80)

    $proc = Get-TrainProcess -TargetModel $Model
    $csvAge = Get-RecentWriteSeconds -Path $resultsCsv
    if ($null -ne $proc) {
        Write-Host ('Status: TRAINING  PID=' + $proc.ProcessId)
    }
    else {
        if ($null -ne $csvAge -and $csvAge -le ($RefreshSeconds * 3)) {
            Write-Host ('Status: PROCESS NOT FOUND, BUT METRICS UPDATED ' + $csvAge + 's AGO')
        }
        elseif ($null -ne $csvAge) {
            Write-Host ('Status: NOT TRAINING (last metrics update ' + $csvAge + 's ago)')
        }
        else {
            Write-Host 'Status: NOT TRAINING'
        }
    }

    Write-Host ('Epoch Progress: ' + (Get-EpochProgress -Path $resultsCsv))

    if (Test-Path $argsYaml) {
        Write-Host ''
        Write-Host 'Args Snapshot:'
        Get-Content $argsYaml | Select-Object -First 20
    }

    Write-Host ''
    Write-Host 'Checkpoints:'
    if (Test-Path $weightsDir) {
        Get-ChildItem $weightsDir -File |
            Sort-Object LastWriteTime -Descending |
            Select-Object Name,Length,LastWriteTime |
            Format-Table -AutoSize
    }
    else {
        Write-Host 'weights dir not found yet.'
    }

    Write-Host ''
    Write-Host 'Latest Metrics Row:'
    $last = Get-LastCsvRow -Path $resultsCsv
    if ($null -ne $last) {
        Write-Host $last
    }
    else {
        Write-Host 'results.csv not ready yet.'
    }

    Write-Host ''
    Write-Host ('Refresh in ' + $RefreshSeconds + 's, press Ctrl+C to stop watching...')
    Start-Sleep -Seconds $RefreshSeconds
}

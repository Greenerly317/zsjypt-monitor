# PowerShell 脚本：创建 Windows 定时任务
# 每天下午 3 点自动运行中山平台监测

param(
    [switch]$Create,
    [switch]$Delete,
    [switch]$Test,
    [switch]$Status
)

$TaskName = "中山平台每日监测"
$TaskDescription = "每天下午3点自动监测中山平台新项目和变化，发送结果到飞书"
$ScriptPath = "C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor\daily_scheduler.py"
$WorkingDir = "C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor"
$Action = New-ScheduledTaskAction `
    -Execute "python.exe" `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# 时间触发器：每天下午 3 点 (15:00)
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At 15:00

# 任务设置
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

function Create-Task {
    Write-Host "[创建定时任务]" -ForegroundColor Green
    
    # 检查是否已存在
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "[WARN] 任务 '$TaskName' 已存在，将删除并重新创建" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 创建新任务
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Settings $Settings `
            -Description $TaskDescription `
            -RunLevel Highest `
            -Force
        
        Write-Host "[OK] 定时任务创建成功" -ForegroundColor Green
        Write-Host "  任务名称: $TaskName" -ForegroundColor White
        Write-Host "  执行时间: 每天下午 3 点 (15:00)" -ForegroundColor White
        Write-Host "  执行脚本: $ScriptPath" -ForegroundColor White
        Write-Host "  工作目录: $WorkingDir" -ForegroundColor White
    } catch {
        Write-Host "[ERROR] 创建任务失败: $_" -ForegroundColor Red
        exit 1
    }
}

function Delete-Task {
    Write-Host "[删除定时任务]" -ForegroundColor Green
    
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "[OK] 定时任务已删除" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] 删除任务失败: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[INFO] 任务 '$TaskName' 不存在" -ForegroundColor Yellow
    }
}

function Test-Task {
    Write-Host "[测试定时任务]" -ForegroundColor Green
    Write-Host "  执行脚本: python.exe `"$ScriptPath`"" -ForegroundColor White
    Write-Host "  工作目录: $WorkingDir" -ForegroundColor White
    Write-Host ""
    
    # 手动执行一次
    try {
        Push-Location $WorkingDir
        & python.exe $ScriptPath
        Pop-Location
        Write-Host ""
        Write-Host "[OK] 测试执行完成" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] 测试执行失败: $_" -ForegroundColor Red
        exit 1
    }
}

function Show-Status {
    Write-Host "[查看定时任务状态]" -ForegroundColor Green
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "  任务名称: $($task.TaskName)" -ForegroundColor White
        Write-Host "  状态: $($task.State)" -ForegroundColor White
        Write-Host "  执行时间: 每天下午 3 点 (15:00)" -ForegroundColor White
        Write-Host "  说明: $($task.Description)" -ForegroundColor White
        
        # 显示最后一次执行时间
        $lastRun = (Get-ScheduledTaskInfo -TaskName $TaskName).LastRunTime
        if ($lastRun) {
            Write-Host "  最后执行: $lastRun" -ForegroundColor White
        }
    } else {
        Write-Host "  任务不存在，请使用 -Create 参数创建" -ForegroundColor Yellow
    }
}

# 执行相应的操作
if ($Create) {
    Create-Task
} elseif ($Delete) {
    Delete-Task
} elseif ($Test) {
    Test-Task
} elseif ($Status) {
    Show-Status
} else {
    Write-Host ""
    Write-Host "Windows 定时任务管理脚本" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Create"
    Write-Host "    创建每天下午 3 点的定时任务" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Test"
    Write-Host "    测试任务执行" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Status"
    Write-Host "    查看任务状态" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Delete"
    Write-Host "    删除定时任务" -ForegroundColor Gray
    Write-Host ""
}

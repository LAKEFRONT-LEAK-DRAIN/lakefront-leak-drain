param(
    [string]$TaskName = "LakefrontPendingTasksAutoSync",
    [string]$RepoPath,
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
    $RepoPath = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$watchScript = (Resolve-Path (Join-Path $PSScriptRoot "watch_pending_tasks_sync.ps1")).Path

$argList = @(
    "-NoProfile"
    "-WindowStyle"
    "Hidden"
    "-ExecutionPolicy"
    "Bypass"
    "-File"
    "`"$watchScript`""
    "-RepoPath"
    "`"$RepoPath`""
    "-Branch"
    "`"$Branch`""
)

$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument ($argList -join " ")
$trigger = New-ScheduledTaskTrigger -AtLogOn

function Install-StartupLauncher {
    param(
        [string]$ScriptPath,
        [string]$Repo,
        [string]$TargetBranch
    )

    $startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
    $launcherPath = Join-Path $startupDir "LakefrontPendingTasksAutoSync.cmd"

    $launcherContent = @(
        "@echo off"
        "pwsh -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`" -RepoPath `"$Repo`" -Branch `"$TargetBranch`""
    ) -join [Environment]::NewLine

    Set-Content -Path $launcherPath -Value $launcherContent -Encoding ASCII
    Write-Host "Created Startup launcher: $launcherPath"
}

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}
catch {
}

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "Auto-sync hcp-automation/pending-tasks changes to GitHub"
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Registered and started scheduled task: $TaskName"
}
catch {
    if ($_.Exception.Message -like "*Access is denied*") {
        Write-Warning "Scheduled task registration was denied. Falling back to Startup launcher."
        Install-StartupLauncher -ScriptPath $watchScript -Repo $RepoPath -TargetBranch $Branch
    }
    else {
        throw
    }
}

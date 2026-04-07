param(
    [string]$RepoPath,
    [string]$RelativeWatchPath = "hcp-automation/pending-tasks",
    [string]$Branch = "main",
    [int]$DebounceSeconds = 2
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
    $RepoPath = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$repoResolved = (Resolve-Path $RepoPath).Path
$watchPath = Join-Path $repoResolved $RelativeWatchPath

if (-not (Test-Path $watchPath)) {
    throw "Watch path not found: $watchPath"
}

function Invoke-PendingTasksSync {
    param(
        [string]$Repo,
        [string]$RelativePath,
        [string]$TargetBranch
    )

    Push-Location $Repo
    try {
        git add -- "$RelativePath"
        if ($LASTEXITCODE -ne 0) {
            throw "git add failed"
        }

        $staged = git diff --cached --name-only -- "$RelativePath"
        if (-not $staged) {
            return
        }

        $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "auto-sync pending-tasks $stamp"
        if ($LASTEXITCODE -ne 0) {
            throw "git commit failed"
        }

        git pull --rebase origin "$TargetBranch"
        if ($LASTEXITCODE -ne 0) {
            throw "git pull --rebase failed"
        }

        git push origin "$TargetBranch"
        if ($LASTEXITCODE -ne 0) {
            throw "git push failed"
        }

        Write-Host "[$(Get-Date -Format o)] Synced pending-tasks changes to origin/$TargetBranch"
    }
    finally {
        Pop-Location
    }
}

Write-Host "Watching $watchPath"
Write-Host "Repo: $repoResolved | Branch: $Branch"

$fsw = New-Object System.IO.FileSystemWatcher
$fsw.Path = $watchPath
$fsw.Filter = "*.json"
$fsw.IncludeSubdirectories = $false
$fsw.NotifyFilter = [System.IO.NotifyFilters]'FileName, LastWrite, CreationTime, Size'
$fsw.EnableRaisingEvents = $true

$script:pendingSync = $false
$script:lastEventAt = Get-Date

$eventAction = {
    $script:pendingSync = $true
    $script:lastEventAt = Get-Date
}

$subscriptions = @(
    Register-ObjectEvent -InputObject $fsw -EventName Created -Action $eventAction
    Register-ObjectEvent -InputObject $fsw -EventName Changed -Action $eventAction
    Register-ObjectEvent -InputObject $fsw -EventName Deleted -Action $eventAction
    Register-ObjectEvent -InputObject $fsw -EventName Renamed -Action $eventAction
)

try {
    while ($true) {
        if ($script:pendingSync) {
            $age = (Get-Date) - $script:lastEventAt
            if ($age.TotalSeconds -ge $DebounceSeconds) {
                $script:pendingSync = $false
                try {
                    Invoke-PendingTasksSync -Repo $repoResolved -RelativePath $RelativeWatchPath -TargetBranch $Branch
                }
                catch {
                    Write-Warning "Sync failed: $($_.Exception.Message)"
                }
            }
        }

        Start-Sleep -Milliseconds 500
    }
}
finally {
    foreach ($sub in $subscriptions) {
        Unregister-Event -SourceIdentifier $sub.Name -ErrorAction SilentlyContinue
        Remove-Job -Id $sub.Id -Force -ErrorAction SilentlyContinue
    }

    $fsw.Dispose()
}

#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Syncs modified files to Raspberry Pi using SCP

.DESCRIPTION
    This script identifies modified files in the project and copies them to the Raspberry Pi
    using SCP. It can detect changes since last commit or within a specified time period.

.PARAMETER PiHost
    Raspberry Pi hostname or IP address (default: raspberrypi.local)

.PARAMETER PiUser
    Username for SSH connection (default: pi)

.PARAMETER RemotePath
    Remote path on Pi where files should be copied (default: ~/secret-project)

.PARAMETER SinceCommit
    Copy files modified since specific git commit (default: HEAD~1)

.PARAMETER SinceHours
    Copy files modified within last N hours (alternative to SinceCommit)

.PARAMETER All
    Copy all project files (excluding build/cache directories)

.PARAMETER Compare
    Compare local and remote files before syncing

.PARAMETER DryRun
    Show what would be copied without actually copying

.PARAMETER Verbose
    Show detailed output

.EXAMPLE
    .\sync-modified-files.ps1
    Syncs files modified since the last commit

.EXAMPLE
    .\sync-modified-files.ps1 -SinceHours 2
    Syncs files modified in the last 2 hours

.EXAMPLE
    .\sync-modified-files.ps1 -All
    Syncs all project files (excluding build/cache directories)

.EXAMPLE
    .\sync-modified-files.ps1 -Compare
    Compares local and remote files before syncing

.EXAMPLE
    .\sync-modified-files.ps1 -All -Compare
    Syncs all files but shows differences first

.EXAMPLE
    .\sync-modified-files.ps1 -DryRun
    Shows what files would be synced without actually copying them

.EXAMPLE
    .\sync-modified-files.ps1 -SinceCommit "HEAD~3"
    Syncs files modified since 3 commits ago

.EXAMPLE
    .\sync-modified-files.ps1 -PiHost 192.168.1.100 -DryRun
    Show what would be synced to specific Pi IP without actually copying

.EXAMPLE
    .\sync-modified-files.ps1 -SinceHours 2 -Verbose
    Sync files modified in last 2 hours with verbose output
#>

param(
    [string]$PiHost = "192.168.1.225",
    [string]$PiUser = "pi",
    [string]$RemotePath = "~/Secret-Project",
    [string]$SinceCommit = "HEAD~1",
    [int]$SinceHours = 0,
    [switch]$All,
    [switch]$Compare,
    [switch]$DryRun,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    $actualColor = if ($Colors.ContainsKey($Color)) { $Colors[$Color] } else { $Color }
    Write-Host $Message -ForegroundColor $actualColor
}

function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." "Info"
    
    # Check if git is available
    try {
        git --version | Out-Null
    } catch {
        throw "Git is not installed or not in PATH"
    }
    
    # Check if scp is available
    try {
        scp 2>&1 | Out-Null
    } catch {
        throw "SCP is not installed or not in PATH. Install OpenSSH client."
    }
    
    # Check if we're in a git repository
    if (-not (Test-Path ".git")) {
        throw "Not in a git repository"
    }
    
    Write-ColorOutput "✓ Prerequisites check passed" "Success"
}

function Get-ModifiedFiles {
    param(
        [string]$SinceCommit,
        [int]$SinceHours,
        [switch]$All
    )
    
    $modifiedFiles = @()
    
    if ($All) {
        Write-ColorOutput "Finding all project files..." "Info"
        
        # Get all files excluding build/cache directories
        $modifiedFiles = Get-ChildItem -Recurse -File | Where-Object {
            $_.FullName -notmatch '\\.git\\' -and
            $_.FullName -notmatch '\\node_modules\\' -and
            $_.FullName -notmatch '\\__pycache__\\' -and
            $_.FullName -notmatch '\\.pytest_cache\\' -and
            $_.FullName -notmatch '\\dist\\' -and
            $_.FullName -notmatch '\\build\\' -and
            $_.FullName -notmatch '\\.svelte-kit\\' -and
            $_.FullName -notmatch '\\.vscode\\' -and
            $_.FullName -notmatch '\\.bmad-core\\' -and
            $_.FullName -notmatch '\\.trae\\' -and
            $_.FullName -notmatch '\\docs\\' -and
            -not $_.Name.StartsWith('.')
        } | ForEach-Object { 
            $relativePath = $_.FullName.Replace((Get-Location).Path, "").TrimStart('\\').Replace("\\", "/")
            $relativePath
        }
    } elseif ($SinceHours -gt 0) {
        Write-ColorOutput "Finding files modified in last $SinceHours hours..." "Info"
        $sinceTime = (Get-Date).AddHours(-$SinceHours)
        $modifiedFiles = Get-ChildItem -Recurse -File | Where-Object {
            $_.LastWriteTime -gt $sinceTime -and
            $_.FullName -notmatch '\\.git\\' -and
            $_.FullName -notmatch '\\node_modules\\' -and
            $_.FullName -notmatch '\\__pycache__\\' -and
            $_.FullName -notmatch '\\.pytest_cache\\' -and
            $_.FullName -notmatch '\\dist\\' -and
            $_.FullName -notmatch '\\build\\' -and
            $_.FullName -notmatch '\\.svelte-kit\\' -and
            $_.FullName -notmatch '\\.vscode\\' -and
            $_.FullName -notmatch '\\.bmad-core\\' -and
            $_.FullName -notmatch '\\.trae\\' -and
            $_.FullName -notmatch '\\docs\\' -and
            -not $_.Name.StartsWith('.')
        } | ForEach-Object { 
            $relativePath = $_.FullName.Replace((Get-Location).Path, "").TrimStart('\\').Replace("\\", "/")
            $relativePath
        }
    } else {
        Write-ColorOutput "Finding files modified since commit $SinceCommit..." "Info"
        try {
            $gitOutput = git diff --name-only $SinceCommit
            if ($LASTEXITCODE -eq 0) {
                $modifiedFiles = $gitOutput | Where-Object { $_ -and $_.Trim() }
            }
        } catch {
            Write-ColorOutput "Warning: Could not get git diff, falling back to git status" "Warning"
            $gitOutput = git status --porcelain
            $modifiedFiles = $gitOutput | ForEach-Object {
                if ($_ -match '^[AM]\s+(.+)$') {
                    $matches[1]
                }
            }
        }
    }
    
    return $modifiedFiles | Where-Object { $_ }
}

function Test-PiConnection {
    param(
        [string]$PiHost,
        [string]$PiUser
    )
    
    Write-ColorOutput "Testing connection to $PiUser@$PiHost..." "Info"
    
    try {
        $result = ssh -o ConnectTimeout=10 -o BatchMode=yes "$PiUser@$PiHost" "echo 'Connection test successful'"
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Connection successful" "Success"
            return $true
        }
    } catch {
        # Ignore exception, will handle below
    }
    
    Write-ColorOutput "⚠ Could not connect to Pi. Make sure:" "Warning"
    Write-ColorOutput "  - Pi is powered on and connected to network" "Warning"
    Write-ColorOutput "  - SSH is enabled on Pi" "Warning"
    Write-ColorOutput "  - SSH key is set up or you'll be prompted for password" "Warning"
    
    $continue = Read-Host "Continue anyway? (y/N)"
    return $continue -eq 'y' -or $continue -eq 'Y'
}

function Compare-Files {
    param(
        [string[]]$Files,
        [string]$PiUser,
        [string]$PiHost,
        [string]$RemotePath
    )
    
    Write-ColorOutput "Comparing local and remote files..." "Info"
    
    $differences = @()
    
    foreach ($file in $Files) {
        $localFile = $file
        $remoteFile = "$PiUser@${PiHost}:$RemotePath/$file"
        
        # Check if remote file exists
        $remoteExists = ssh "$PiUser@$PiHost" "test -f '$RemotePath/$file' && echo 'exists'" 2>$null
        
        if ($remoteExists -eq "exists") {
            # Compare file checksums
            $localHash = (Get-FileHash $localFile -Algorithm MD5).Hash
            $remoteHash = ssh "$PiUser@$PiHost" "md5sum '$RemotePath/$file' | cut -d' ' -f1" 2>$null
            
            if ($localHash.ToLower() -ne $remoteHash.ToLower()) {
                $differences += [PSCustomObject]@{
                    File = $file
                    Status = "Modified"
                    LocalHash = $localHash
                    RemoteHash = $remoteHash
                }
            }
        } else {
            $differences += [PSCustomObject]@{
                File = $file
                Status = "New"
                LocalHash = (Get-FileHash $localFile -Algorithm MD5).Hash
                RemoteHash = "N/A"
            }
        }
    }
    
    if ($differences.Count -gt 0) {
        Write-ColorOutput "File differences found ($($differences.Count)):" "Header"
        foreach ($diff in $differences) {
            $color = if ($diff.Status -eq "New") { "Success" } else { "Warning" }
            Write-ColorOutput "  [$($diff.Status)] $($diff.File)" $color
        }
        
        $proceed = Read-Host "Proceed with sync? (Y/n)"
        return ($proceed -ne 'n' -and $proceed -ne 'N')
    } else {
        Write-ColorOutput "No differences found - all files are up to date" "Success"
        return $false
    }
}

function Copy-FilesToPi {
    param(
        [string[]]$Files,
        [string]$PiHost,
        [string]$PiUser,
        [string]$RemotePath,
        [bool]$DryRun
    )
    
    if ($Files.Count -eq 0) {
        Write-ColorOutput "No modified files found" "Info"
        return
    }
    
    Write-ColorOutput "Files to sync ($($Files.Count)):" "Header"
    foreach ($file in $Files) {
        Write-ColorOutput "  $file" "Info"
    }
    
    if ($DryRun) {
        Write-ColorOutput "DRY RUN - No files were actually copied" "Warning"
        return
    }
    
    Write-ColorOutput "Copying files to $PiUser@${PiHost}:$RemotePath..." "Cyan"
    
    $successCount = 0
    $errorCount = 0
    
    foreach ($file in $Files) {
        try {
            # Create remote directory structure if needed
            $fileUnix = $file.Replace('\\', '/')
            $remoteDir = Split-Path "$RemotePath/$fileUnix" -Parent
            # Always ensure the full directory path exists
            ssh "$PiUser@$PiHost" "mkdir -p '$remoteDir'" 2>$null
            
            # Copy the file
            if ($Verbose) {
                Write-ColorOutput "Copying: $file" "Info"
            }
            
            scp "$file" "$PiUser@${PiHost}:$RemotePath/$fileUnix"
            
            if ($LASTEXITCODE -eq 0) {
                $successCount++
                if ($Verbose) {
                    Write-ColorOutput "✓ Copied: $file" "Success"
                }
            } else {
                $errorCount++
                Write-ColorOutput "✗ Failed to copy: $file" "Error"
            }
        } catch {
            $errorCount++
            Write-ColorOutput "✗ Error copying $file : $($_.Exception.Message)" "Error"
        }
    }
    
    Write-ColorOutput "" "Info"
    Write-ColorOutput "Sync completed:" "Header"
    Write-ColorOutput "  ✓ Successfully copied: $successCount files" "Success"
    if ($errorCount -gt 0) {
        Write-ColorOutput "  ✗ Failed to copy: $errorCount files" "Error"
    }
}

# Main execution
try {
    Write-ColorOutput "=== Raspberry Pi File Sync ==="  "Header"
    Write-ColorOutput "" "Info"
    
    Test-Prerequisites
    
    $modifiedFiles = Get-ModifiedFiles -SinceCommit $SinceCommit -SinceHours $SinceHours -All:$All
    
    if ($modifiedFiles.Count -eq 0) {
        Write-ColorOutput "No modified files found to sync" "Info"
        exit 0
    }
    
    if (-not $DryRun) {
        $connectionOk = Test-PiConnection -PiHost $PiHost -PiUser $PiUser
        if (-not $connectionOk) {
            Write-ColorOutput "Aborting due to connection issues" "Error"
            exit 1
        }
        
        # Compare files if requested
        if ($Compare) {
            $shouldProceed = Compare-Files -Files $modifiedFiles -PiUser $PiUser -PiHost $PiHost -RemotePath $RemotePath
            if (-not $shouldProceed) {
                Write-ColorOutput "Sync cancelled or no changes needed" "Info"
                exit 0
            }
        }
    }
    
    Copy-FilesToPi -Files $modifiedFiles -PiHost $PiHost -PiUser $PiUser -RemotePath $RemotePath -DryRun $DryRun
    
    Write-ColorOutput "" "Info"
    Write-ColorOutput "Sync operation completed successfully!" "Success"
        
    Write-Host "🚀 Restarting services..." -ForegroundColor Yellow
    Invoke-PiCommand "sudo systemctl daemon-reload"
    Invoke-PiCommand "sudo systemctl restart piano-led-visualizer.service"
    Invoke-PiCommand "sudo systemctl restart nginx"

} catch {
    Write-ColorOutput "" "Info"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Error"
    exit 1
}
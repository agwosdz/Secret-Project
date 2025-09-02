# Raspberry Pi Sync Scripts

This directory contains scripts to sync modified files to a Raspberry Pi using SCP.

## Scripts

### sync-modified-files.ps1 (PowerShell)
Windows PowerShell script for syncing files to Raspberry Pi.

### sync-modified-files.sh (Bash)
Cross-platform bash script for syncing files to Raspberry Pi.

## Prerequisites

1. **SSH Access**: Ensure SSH is enabled on your Raspberry Pi
2. **SSH Key Setup** (recommended): Set up SSH key authentication to avoid password prompts
3. **Git Repository**: Scripts must be run from within a git repository
4. **SCP**: Ensure SCP is available in your system PATH

## Quick Start

### Windows (PowerShell)
```powershell
# Make script executable (first time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Sync files modified since last commit
.\scripts\sync-modified-files.ps1

# Sync files from last 2 hours with verbose output
.\scripts\sync-modified-files.ps1 -SinceHours 2 -Verbose

# Sync ALL project files (excluding build/cache directories)
.\scripts\sync-modified-files.ps1 -All

# Compare local and remote files before syncing
.\scripts\sync-modified-files.ps1 -Compare

# Sync all files with comparison first
.\scripts\sync-modified-files.ps1 -All -Compare

# Dry run to see what would be copied
.\scripts\sync-modified-files.ps1 -DryRun
```

### Linux/macOS (Bash)
```bash
# Make script executable (first time only)
chmod +x scripts/sync-modified-files.sh

# Sync files modified since last commit
./scripts/sync-modified-files.sh

# Sync files from last 2 hours with verbose output
./scripts/sync-modified-files.sh -t 2 -v

# Sync ALL project files (excluding build/cache directories)
./scripts/sync-modified-files.sh -a

# Compare local and remote files before syncing
./scripts/sync-modified-files.sh --compare

# Sync all files with comparison first
./scripts/sync-modified-files.sh -a --compare

# Dry run to see what would be copied
./scripts/sync-modified-files.sh -d
```

## Configuration Options

### Common Parameters
- **Host**: Raspberry Pi hostname or IP address (default: `raspberrypi.local`)
- **User**: SSH username (default: `pi`)
- **Remote Path**: Target directory on Pi (default: `~/secret-project`)
- **Commit**: Sync files modified since specific commit (default: `HEAD~1`)
- **Hours**: Sync files modified in last N hours (alternative to commit-based)
- **All**: Sync ALL project files (excludes build/cache directories like node_modules, dist, .svelte-kit)
- **Compare**: Compare local and remote files before syncing (shows differences and prompts to continue)
- **Dry Run**: Preview what would be copied without actually copying
- **Verbose**: Show detailed output during sync

### PowerShell Examples
```powershell
# Sync to specific IP with custom user
.\scripts\sync-modified-files.ps1 -Host "192.168.1.100" -User "myuser"

# Sync files from last 4 hours to custom path
.\scripts\sync-modified-files.ps1 -Hours 4 -RemotePath "/home/pi/myproject"

# Sync files since 3 commits ago
.\scripts\sync-modified-files.ps1 -SinceCommit "HEAD~3"
```

### Bash Examples
```bash
# Sync to specific IP with custom user
./scripts/sync-modified-files.sh -h "192.168.1.100" -u "myuser"

# Sync files from last 4 hours to custom path
./scripts/sync-modified-files.sh -t 4 -p "/home/pi/myproject"

# Sync files since 3 commits ago
./scripts/sync-modified-files.sh -c "HEAD~3"
```

## SSH Key Setup (Recommended)

To avoid password prompts, set up SSH key authentication:

### Generate SSH Key (if you don't have one)
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### Copy Key to Raspberry Pi
```bash
ssh-copy-id pi@raspberrypi.local
```

### Test Connection
```bash
ssh pi@raspberrypi.local
```

## File Filtering

The scripts automatically exclude:
- Hidden files and directories (starting with `.`)
- `node_modules/` directories
- `__pycache__/` directories
- `.pytest_cache/` directories
- `dist/` directories (build output)
- `build/` directories (build output)
- `.svelte-kit/` directories (SvelteKit cache)
- `.vscode/` directories (VS Code settings)
- `.bmad-core/` directories (BMAD framework files)
- `.trae/` directories (Trae IDE files)
- `.git/` directory contents

## Troubleshooting

### Connection Issues
1. Verify Pi is powered on and connected to network
2. Check if SSH is enabled: `sudo systemctl status ssh`
3. Verify hostname resolution: `ping raspberrypi.local`
4. Try using IP address instead of hostname

### Permission Issues
1. Ensure SSH key is properly set up
2. Check remote directory permissions
3. Verify user has write access to remote path

### Git Issues
1. Ensure you're in a git repository root
2. Check if specified commit exists: `git log --oneline`
3. Verify git is in your PATH

## Advanced Usage

### Custom File Selection
Modify the scripts to add custom file filtering logic in the `get_modified_files` function.

### Integration with CI/CD
These scripts can be integrated into build processes or automated deployment pipelines.

### Multiple Pi Deployment
Create wrapper scripts to deploy to multiple Raspberry Pi devices in sequence.

## Security Notes

- Always use SSH key authentication in production
- Consider using SSH config files for complex setups
- Regularly update SSH keys and review access
- Use firewall rules to restrict SSH access if needed
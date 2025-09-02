#!/bin/bash

# Raspberry Pi File Sync Script
# Syncs modified files to Raspberry Pi using SCP

# Default configuration
PI_HOST="raspberrypi.local"
PI_USER="pi"
REMOTE_PATH="~/secret-project"
SINCE_COMMIT="HEAD~1"
SINCE_HOURS=0
DRY_RUN=false
VERBOSE=false
ALL_FILES=false
COMPARE_FILES=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Sync modified files to Raspberry Pi using SCP"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST        Pi hostname or IP (default: raspberrypi.local)"
    echo "  -u, --user USER        SSH username (default: pi)"
    echo "  -p, --path PATH        Remote path (default: ~/secret-project)"
    echo "  -c, --commit COMMIT    Files modified since commit (default: HEAD~1)"
    echo "  -t, --hours HOURS      Files modified in last N hours"
    echo "  -a, --all              Copy all project files"
    echo "  --compare              Compare local and remote files before syncing"
    echo "  -d, --dry-run          Show what would be copied"
    echo "  -v, --verbose          Verbose output"
    echo "  --help                 Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Sync files since last commit"
    echo "  $0 -t 2 -v                          # Sync files from last 2 hours"
    echo "  $0 -a                                # Sync all project files"
    echo "  $0 --compare                         # Compare files before syncing"
    echo "  $0 -a --compare                      # Sync all files with comparison"
    echo "  $0 -h 192.168.1.100 -d              # Dry run to specific IP"
    echo "  $0 -c HEAD~3                        # Sync files since 3 commits ago"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            PI_HOST="$2"
            shift 2
            ;;
        -u|--user)
            PI_USER="$2"
            shift 2
            ;;
        -p|--path)
            REMOTE_PATH="$2"
            shift 2
            ;;
        -c|--commit)
            SINCE_COMMIT="$2"
            shift 2
            ;;
        -t|--hours)
            SINCE_HOURS="$2"
            shift 2
            ;;
        -a|--all)
            ALL_FILES=true
            shift
            ;;
        --compare)
            COMPARE_FILES=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    print_color "$CYAN" "Checking prerequisites..."
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_color "$RED" "Error: Git is not installed or not in PATH"
        exit 1
    fi
    
    # Check if scp is available
    if ! command -v scp &> /dev/null; then
        print_color "$RED" "Error: SCP is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        print_color "$RED" "Error: Not in a git repository"
        exit 1
    fi
    
    print_color "$GREEN" "✓ Prerequisites check passed"
}

# Function to get modified files
get_modified_files() {
    local files=()
    
    if [ "$ALL_FILES" = true ]; then
        print_color "$CYAN" "Finding all project files..."
        
        # Get all files excluding build/cache directories
        while IFS= read -r -d '' file; do
            # Convert absolute path to relative and normalize separators
            rel_path=$(realpath --relative-to="." "$file" 2>/dev/null || echo "$file")
            # Skip hidden directories and common build/cache directories
            if [[ ! "$rel_path" =~ ^\. ]] && \
               [[ ! "$rel_path" =~ node_modules ]] && \
               [[ ! "$rel_path" =~ __pycache__ ]] && \
               [[ ! "$rel_path" =~ \.pytest_cache ]] && \
               [[ ! "$rel_path" =~ dist/ ]] && \
               [[ ! "$rel_path" =~ build/ ]] && \
               [[ ! "$rel_path" =~ \.svelte-kit/ ]] && \
               [[ ! "$rel_path" =~ \.vscode/ ]] && \
               [[ ! "$rel_path" =~ \.bmad-core/ ]] && \
               [[ ! "$rel_path" =~ \.trae/ ]] && \
               [[ ! "$rel_path" =~ \.git/ ]]; then
                files+=("$rel_path")
            fi
        done < <(find . -type f -print0 2>/dev/null)
    elif [ "$SINCE_HOURS" -gt 0 ] 2>/dev/null; then
        print_color "$CYAN" "Finding files modified in last $SINCE_HOURS hours..."
        
        # Find files modified within the specified hours
        while IFS= read -r -d '' file; do
            # Convert absolute path to relative and normalize separators
            rel_path=$(realpath --relative-to="." "$file" 2>/dev/null || echo "$file")
            # Skip hidden directories and common build/cache directories
            if [[ ! "$rel_path" =~ ^\. ]] && \
               [[ ! "$rel_path" =~ node_modules ]] && \
               [[ ! "$rel_path" =~ __pycache__ ]] && \
               [[ ! "$rel_path" =~ \.pytest_cache ]] && \
               [[ ! "$rel_path" =~ dist/ ]] && \
               [[ ! "$rel_path" =~ build/ ]] && \
               [[ ! "$rel_path" =~ \.svelte-kit/ ]] && \
               [[ ! "$rel_path" =~ \.vscode/ ]] && \
               [[ ! "$rel_path" =~ \.git/ ]]; then
                files+=("$rel_path")
            fi
        done < <(find . -type f -mmin -$((SINCE_HOURS * 60)) -print0 2>/dev/null)
    else
        print_color "$CYAN" "Finding files modified since commit $SINCE_COMMIT..."
        
        # Get files from git diff
        if git rev-parse "$SINCE_COMMIT" >/dev/null 2>&1; then
            while IFS= read -r file; do
                [ -n "$file" ] && files+=("$file")
            done < <(git diff --name-only "$SINCE_COMMIT" 2>/dev/null)
        else
            print_color "$YELLOW" "Warning: Invalid commit, using git status instead"
            while IFS= read -r line; do
                if [[ "$line" =~ ^[AM][[:space:]]+(.+)$ ]]; then
                    files+=("${BASH_REMATCH[1]}")
                fi
            done < <(git status --porcelain 2>/dev/null)
        fi
    fi
    
    printf '%s\n' "${files[@]}"
}

# Function to test Pi connection
test_pi_connection() {
    print_color "$CYAN" "Testing connection to $PI_USER@$PI_HOST..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$PI_USER@$PI_HOST" "echo 'Connection test successful'" >/dev/null 2>&1; then
        print_color "$GREEN" "✓ Connection successful"
        return 0
    else
        print_color "$YELLOW" "⚠ Could not connect to Pi. Make sure:"
        print_color "$YELLOW" "  - Pi is powered on and connected to network"
        print_color "$YELLOW" "  - SSH is enabled on Pi"
        print_color "$YELLOW" "  - SSH key is set up or you'll be prompted for password"
        
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]]
    fi
}

# Function to compare local and remote files
compare_files() {
    local files=("$@")
    local differences=()
    
    print_color "$CYAN" "Comparing local and remote files..."
    
    for file in "${files[@]}"; do
        # Check if remote file exists
        if ssh "$PI_USER@$PI_HOST" "test -f '$REMOTE_PATH/$file'" 2>/dev/null; then
            # Compare file checksums
            local_hash=$(md5sum "$file" 2>/dev/null | cut -d' ' -f1)
            remote_hash=$(ssh "$PI_USER@$PI_HOST" "md5sum '$REMOTE_PATH/$file' 2>/dev/null | cut -d' ' -f1" 2>/dev/null)
            
            if [ "$local_hash" != "$remote_hash" ]; then
                differences+=("[Modified] $file")
            fi
        else
            differences+=("[New] $file")
        fi
    done
    
    if [ ${#differences[@]} -gt 0 ]; then
        print_color "$MAGENTA" "File differences found (${#differences[@]}):"
        for diff in "${differences[@]}"; do
            if [[ "$diff" =~ \[New\] ]]; then
                print_color "$GREEN" "  $diff"
            else
                print_color "$YELLOW" "  $diff"
            fi
        done
        
        read -p "Proceed with sync? (Y/n): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Nn]$ ]]
    else
        print_color "$GREEN" "No differences found - all files are up to date"
        return 1
    fi
}

# Function to copy files to Pi
copy_files_to_pi() {
    local files=("$@")
    
    if [ ${#files[@]} -eq 0 ]; then
        print_color "$CYAN" "No modified files found"
        return 0
    fi
    
    print_color "$MAGENTA" "Files to sync (${#files[@]}):"
    for file in "${files[@]}"; do
        print_color "$CYAN" "  $file"
    done
    
    if [ "$DRY_RUN" = true ]; then
        print_color "$YELLOW" "DRY RUN - No files were actually copied"
        return 0
    fi
    
    print_color "$CYAN" "Copying files to $PI_USER@$PI_HOST:$REMOTE_PATH..."
    
    local success_count=0
    local error_count=0
    
    for file in "${files[@]}"; do
        # Create remote directory structure if needed
        remote_dir=$(dirname "$REMOTE_PATH/$file")
        # Always ensure the full directory path exists
        ssh "$PI_USER@$PI_HOST" "mkdir -p '$remote_dir'" 2>/dev/null
        
        # Copy the file
        if [ "$VERBOSE" = true ]; then
            print_color "$CYAN" "Copying: $file"
        fi
        
        if scp "$file" "$PI_USER@$PI_HOST:$REMOTE_PATH/$file" >/dev/null 2>&1; then
            ((success_count++))
            if [ "$VERBOSE" = true ]; then
                print_color "$GREEN" "✓ Copied: $file"
            fi
        else
            ((error_count++))
            print_color "$RED" "✗ Failed to copy: $file"
        fi
    done
    
    echo
    print_color "$MAGENTA" "Sync completed:"
    print_color "$GREEN" "  ✓ Successfully copied: $success_count files"
    if [ $error_count -gt 0 ]; then
        print_color "$RED" "  ✗ Failed to copy: $error_count files"
    fi
}

# Main execution
main() {
    print_color "$MAGENTA" "=== Raspberry Pi File Sync ==="
    echo
    
    check_prerequisites
    
    # Get modified files
    mapfile -t modified_files < <(get_modified_files)
    
    if [ ${#modified_files[@]} -eq 0 ]; then
        print_color "$CYAN" "No modified files found to sync"
        exit 0
    fi
    
    # Test connection if not dry run
    if [ "$DRY_RUN" != true ]; then
        if ! test_pi_connection; then
            print_color "$RED" "Aborting due to connection issues"
            exit 1
        fi
        
        # Compare files if requested
        if [ "$COMPARE_FILES" = true ]; then
            if ! compare_files "${modified_files[@]}"; then
                print_color "$CYAN" "Sync cancelled or no changes needed"
                exit 0
            fi
        fi
    fi
    
    # Copy files
    copy_files_to_pi "${modified_files[@]}"
    
    echo
    print_color "$GREEN" "Sync operation completed successfully!"
}

# Run main function
main "$@"
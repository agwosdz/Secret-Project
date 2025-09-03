#!/bin/bash

# Piano LED Visualizer - Raspberry Pi Update Script
# This script updates the project on the Raspberry Pi by:
# 1. Pulling the latest changes from git
# 2. Checking if frontend files were changed, and if so, rebuilding the frontend
# 3. Checking if backend files were changed, and if so, restarting the service
# 4. Restarting services/reloading daemons as needed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/pi/Secret-Project"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
SERVICE_NAME="piano-led-visualizer.service"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if files in a directory have changed
check_changes() {
    local dir=$1
    local changes=$(git diff --name-only HEAD@{1} HEAD | grep -c "^${dir#$PROJECT_DIR/}" || true)
    return $([[ $changes -gt 0 ]] && echo 0 || echo 1)
}

# Navigate to project directory
cd "$PROJECT_DIR"

# Store current git HEAD for comparison
git rev-parse HEAD > /tmp/prev_head

# Step 1: Pull latest changes
print_color "$BLUE" "📥 Pulling latest changes..."
git pull

# Check if there were any changes
if [ "$(git rev-parse HEAD)" == "$(cat /tmp/prev_head)" ]; then
    print_color "$YELLOW" "ℹ️ No new changes to apply."
    exit 0
fi

# Step 2: Check if frontend files changed
if check_changes "$FRONTEND_DIR"; then
    print_color "$BLUE" "🔄 Frontend changes detected. Rebuilding..."
    cd "$FRONTEND_DIR"
    npm install
    npm run build
    print_color "$GREEN" "✅ Frontend rebuilt successfully."
fi

# Step 3: Check if backend files changed
backend_changed=false
if check_changes "$BACKEND_DIR"; then
    print_color "$BLUE" "🔄 Backend changes detected."
    backend_changed=true
    
    # Update Python dependencies if requirements.txt changed
    if git diff --name-only HEAD@{1} HEAD | grep -q "^backend/requirements.txt$"; then
        print_color "$BLUE" "📦 Updating Python dependencies..."
        cd "$BACKEND_DIR"
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
    fi
fi

# Step 4: Restart services if needed
if [ "$backend_changed" = true ]; then
    print_color "$BLUE" "🔄 Restarting backend service..."
    sudo systemctl restart "$SERVICE_NAME"
    print_color "$GREEN" "✅ Backend service restarted."
fi

# Reload nginx in case frontend was updated
if check_changes "$FRONTEND_DIR"; then
    print_color "$BLUE" "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    print_color "$GREEN" "✅ Nginx reloaded."
fi

# Verify services are running
print_color "$BLUE" "🔍 Verifying services..."

# Check backend service
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_color "$GREEN" "✅ Backend service is running."
else
    print_color "$RED" "❌ Backend service is not running! Check logs with: sudo journalctl -u $SERVICE_NAME -n 50"
fi

# Check nginx service
if systemctl is-active --quiet nginx; then
    print_color "$GREEN" "✅ Nginx service is running."
else
    print_color "$RED" "❌ Nginx service is not running! Check logs with: sudo journalctl -u nginx -n 50"
fi

print_color "$GREEN" "🎉 Update completed successfully!"
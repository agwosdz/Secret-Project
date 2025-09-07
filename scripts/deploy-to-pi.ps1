# Piano LED Visualizer - Raspberry Pi Deployment Script (PowerShell)
# Usage: .\deploy-to-pi.ps1 [pi-ip-address] [backend-port]
# Example: .\deploy-to-pi.ps1 192.168.1.225 5001

param(
    [string]$PiIP = "192.168.1.225",
    [string]$BackendPort = "5001"
)

$PI_USER = "pi"
$PROJECT_DIR = "/home/pi/Secret-Project"
$REPO_URL = "https://github.com/agwosdz/Secret-Project.git"

Write-Host "🚀 Deploying Piano LED Visualizer to Raspberry Pi at $PiIP" -ForegroundColor Green

# Function to run commands on Pi via SSH
function Invoke-PiCommand {
    param([string]$Command)
    ssh "$PI_USER@$PiIP" $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Command failed: $Command" -ForegroundColor Red
        exit 1
    }
}

# Function to copy files to Pi
function Copy-ToPi {
    param([string]$Source, [string]$Destination)
    scp -r $Source "$PI_USER@${PiIP}:$Destination"
}

try {
    Write-Host "📋 Step 1: Updating system packages..." -ForegroundColor Yellow
    Invoke-PiCommand "sudo apt update && sudo apt upgrade -y"

    Write-Host "📦 Step 2: Installing required packages..." -ForegroundColor Yellow
    Invoke-PiCommand "sudo apt install python3 python3-pip python3-venv git nginx build-essential python3-dev -y"

    Write-Host "📦 Installing Node.js..." -ForegroundColor Yellow
    Invoke-PiCommand "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install nodejs -y"

    Write-Host "📁 Step 3: Setting up project directory..." -ForegroundColor Yellow
    Invoke-PiCommand "rm -rf $PROJECT_DIR"
    Invoke-PiCommand "git clone $REPO_URL $PROJECT_DIR"

    Write-Host "🐍 Step 4: Setting up Python backend..." -ForegroundColor Yellow
    Invoke-PiCommand "cd $PROJECT_DIR/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

    Write-Host "⚛️ Step 5: Building frontend..." -ForegroundColor Yellow
    Invoke-PiCommand "cd $PROJECT_DIR/frontend && npm install && npm run build"

    Write-Host "🔐 Step 6: Fixing file permissions for nginx..." -ForegroundColor Yellow
    # Fix home directory permissions to allow nginx to traverse
    Invoke-PiCommand "chmod 755 /home/pi"
    # Set proper ownership for frontend build files
    Invoke-PiCommand "sudo chown -R www-data:www-data $PROJECT_DIR/frontend/build"
    # Ensure parent directories have proper permissions
    Invoke-PiCommand "chmod 755 $PROJECT_DIR $PROJECT_DIR/frontend"

    Write-Host "⚙️ Step 7: Creating environment configuration..." -ForegroundColor Yellow
    $envConfig = @"
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=$BackendPort
"@
    Invoke-PiCommand "cat > $PROJECT_DIR/.env << 'EOF'`n$envConfig`nEOF"

    Write-Host "🔧 Step 8: Setting up systemd service..." -ForegroundColor Yellow
    $serviceConfig = @"
[Unit]
Description=Piano LED Visualizer Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=$PROJECT_DIR/backend/venv/bin
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/backend/venv/bin/python start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"@
    Invoke-PiCommand "sudo tee /etc/systemd/system/piano-led-visualizer.service > /dev/null << 'EOF'`n$serviceConfig`nEOF"

    Write-Host "🌐 Step 9: Configuring nginx..." -ForegroundColor Yellow
    $nginxConfig = @"
server {
    listen 80;
    server_name _;
    
    location / {
        root $PROJECT_DIR/frontend/build;
        try_files `$uri `$uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:$BackendPort;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
    }
    
    location /health {
        proxy_pass http://localhost:$BackendPort/health;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
    }
    
    location /socket.io/ {
        proxy_pass http://localhost:$BackendPort;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
}
"@
    Invoke-PiCommand "sudo tee /etc/nginx/sites-available/piano-led-visualizer > /dev/null << 'EOF'`n$nginxConfig`nEOF"
    Invoke-PiCommand "sudo ln -sf /etc/nginx/sites-available/piano-led-visualizer /etc/nginx/sites-enabled/"
    Invoke-PiCommand "sudo rm -f /etc/nginx/sites-enabled/default"

    Write-Host "🚀 Step 10: Starting services..." -ForegroundColor Yellow
    Invoke-PiCommand "sudo systemctl daemon-reload"
    Invoke-PiCommand "sudo systemctl enable piano-led-visualizer.service"
    Invoke-PiCommand "sudo systemctl start piano-led-visualizer.service"
    Invoke-PiCommand "sudo systemctl restart nginx"

    Write-Host "✅ Step 11: Verifying deployment..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    # Test the health endpoint
    try {
        Invoke-PiCommand "curl -f http://${PiIP}:$BackendPort/health > /dev/null 2>&1"
        Write-Host "✅ Backend health check: PASSED" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Backend health check: FAILED" -ForegroundColor Red
        Write-Host "Check logs with: ssh $PI_USER@$PiIP 'sudo journalctl -u piano-led-visualizer.service -f'" -ForegroundColor Yellow
    }

    try {
        Invoke-PiCommand "curl -f http://$PiIP/health > /dev/null 2>&1"
        Write-Host "✅ Nginx proxy health check: PASSED" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Nginx proxy health check: FAILED" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "🎉 Deployment complete!" -ForegroundColor Green
    Write-Host "📱 Access your app at: http://$PiIP" -ForegroundColor Cyan
    Write-Host "🔍 Health check: http://$PiIP/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 Management commands:" -ForegroundColor Yellow
    Write-Host "  View logs: ssh $PI_USER@$PiIP 'sudo journalctl -u piano-led-visualizer.service -f'" -ForegroundColor White
    Write-Host "  Restart:   ssh $PI_USER@$PiIP 'sudo systemctl restart piano-led-visualizer.service'" -ForegroundColor White
    Write-Host "  Status:    ssh $PI_USER@$PiIP 'sudo systemctl status piano-led-visualizer.service'" -ForegroundColor White
}
catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
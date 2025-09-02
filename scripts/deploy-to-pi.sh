#!/bin/bash

# Piano LED Visualizer - Raspberry Pi Deployment Script
# Usage: ./deploy-to-pi.sh [pi-ip-address]

set -e

PI_IP=${1:-"raspberrypi.local"}
PI_USER="pi"
PROJECT_DIR="/home/pi/Secret-Project"
REPO_URL="https://github.com/agwosdz/Secret-Project.git"

echo "🚀 Deploying Piano LED Visualizer to Raspberry Pi at $PI_IP"

# Function to run commands on Pi via SSH
run_on_pi() {
    ssh $PI_USER@$PI_IP "$1"
}

# Function to copy files to Pi
copy_to_pi() {
    scp -r "$1" $PI_USER@$PI_IP:"$2"
}

echo "📋 Step 1: Updating system packages..."
run_on_pi "sudo apt update && sudo apt upgrade -y"

echo "📦 Step 2: Installing required packages..."
run_on_pi "sudo apt install python3 python3-pip python3-venv git nginx -y"

# Install Node.js
echo "📦 Installing Node.js..."
run_on_pi "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install nodejs -y"

echo "📁 Step 3: Setting up project directory..."
run_on_pi "rm -rf $PROJECT_DIR"
run_on_pi "git clone $REPO_URL $PROJECT_DIR"

echo "🐍 Step 4: Setting up Python backend..."
run_on_pi "cd $PROJECT_DIR/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "⚛️ Step 5: Building frontend..."
run_on_pi "cd $PROJECT_DIR/frontend && npm install && npm run build"

echo "⚙️ Step 6: Creating environment configuration..."
run_on_pi "cat > $PROJECT_DIR/.env << EOF
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF"

echo "🔧 Step 7: Setting up systemd service..."
run_on_pi "sudo tee /etc/systemd/system/piano-led-visualizer.service > /dev/null << 'EOF'
[Unit]
Description=Piano LED Visualizer Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=$PROJECT_DIR/backend/venv/bin
Environment=BLINKA_USE_GPIOMEM=1
Environment=BLINKA_FORCEBOARD=RASPBERRY_PI_ZERO_2_W
Environment=BLINKA_FORCECHIP=BCM2XXX
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/backend/venv/bin/python start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

echo "🌐 Step 8: Configuring nginx..."
run_on_pi "sudo tee /etc/nginx/sites-available/piano-led-visualizer > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        root $PROJECT_DIR/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /health {
        proxy_pass http://localhost:5000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /socket.io/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

run_on_pi "sudo ln -sf /etc/nginx/sites-available/piano-led-visualizer /etc/nginx/sites-enabled/"
run_on_pi "sudo rm -f /etc/nginx/sites-enabled/default"

echo "🚀 Step 9: Starting services..."
run_on_pi "sudo systemctl daemon-reload"
run_on_pi "sudo systemctl enable piano-led-visualizer.service"
run_on_pi "sudo systemctl start piano-led-visualizer.service"
run_on_pi "sudo systemctl restart nginx"

echo "✅ Step 10: Verifying deployment..."
sleep 5

# Test the health endpoint
if run_on_pi "curl -f http://localhost:5000/health > /dev/null 2>&1"; then
    echo "✅ Backend health check: PASSED"
else
    echo "❌ Backend health check: FAILED"
    echo "Check logs with: ssh $PI_USER@$PI_IP 'sudo journalctl -u piano-led-visualizer.service -f'"
fi

if run_on_pi "curl -f http://localhost/health > /dev/null 2>&1"; then
    echo "✅ Nginx proxy health check: PASSED"
else
    echo "❌ Nginx proxy health check: FAILED"
fi

echo ""
echo "🎉 Deployment complete!"
echo "📱 Access your app at: http://$PI_IP"
echo "🔍 Health check: http://$PI_IP/health"
echo ""
echo "📊 Management commands:"
echo "  View logs: ssh $PI_USER@$PI_IP 'sudo journalctl -u piano-led-visualizer.service -f'"
echo "  Restart:   ssh $PI_USER@$PI_IP 'sudo systemctl restart piano-led-visualizer.service'"
echo "  Status:    ssh $PI_USER@$PI_IP 'sudo systemctl status piano-led-visualizer.service'"
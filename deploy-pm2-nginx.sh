#!/bin/bash
# PM2 + Nginx Deployment Script for JemFinder
# Run this script to deploy your project

set -e

echo "🚀 Starting JemFinder Deployment with PM2 + Nginx..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo -e "${YELLOW}Project Directory: $PROJECT_DIR${NC}"

# Step 1: Check if running as root for certain operations
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Don't run as root. Use sudo only when needed."
   exit 1
fi

# Step 2: Install Node.js if not installed
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "✅ Node.js already installed: $(node --version)"
fi

# Step 3: Install PM2 globally if not installed
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2..."
    sudo npm install -g pm2
else
    echo "✅ PM2 already installed"
fi

# Step 4: Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
else
    echo "✅ Nginx already installed"
fi

# Step 5: Setup Backend
echo -e "\n${GREEN}📦 Setting up Backend...${NC}"
cd "$PROJECT_DIR/backend"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    cp env.example .env
    echo -e "${YELLOW}⚠️  Please edit backend/.env and add your API keys!${NC}"
fi

# Step 6: Setup Frontend
echo -e "\n${GREEN}📦 Setting up Frontend...${NC}"
cd "$PROJECT_DIR/frontend"

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "Frontend dependencies already installed"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cat > .env << EOF
VITE_API_URL=http://localhost:9000/api/v1
EOF
    echo -e "${YELLOW}⚠️  Please edit frontend/.env and update VITE_API_URL with your server IP/domain!${NC}"
fi

# Step 7: Stop existing PM2 processes
echo -e "\n${GREEN}🔄 Managing PM2 processes...${NC}"
pm2 stop jemfinder-backend 2>/dev/null || true
pm2 stop jemfinder-frontend 2>/dev/null || true
pm2 delete jemfinder-backend 2>/dev/null || true
pm2 delete jemfinder-frontend 2>/dev/null || true

# Step 8: Start Backend with PM2
echo "Starting Backend with PM2..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
pm2 start "uvicorn main:app --host 0.0.0.0 --port 9000" \
    --name jemfinder-backend \
    --interpreter venv/bin/python \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z"

# Step 9: Start Frontend with PM2
echo "Starting Frontend with PM2..."
cd "$PROJECT_DIR/frontend"
pm2 start "npm run dev -- --host 0.0.0.0" \
    --name jemfinder-frontend \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z"

# Step 10: Save PM2 configuration
pm2 save

# Step 11: Setup PM2 startup script
echo "Setting up PM2 startup..."
pm2 startup | grep "sudo" | bash || true

# Step 12: Setup Nginx
echo -e "\n${GREEN}🌐 Setting up Nginx...${NC}"

# Get server IP or domain
read -p "Enter your server IP or domain (e.g., 192.168.1.100 or yourdomain.com): " SERVER_NAME

# Create Nginx config
sudo tee /etc/nginx/sites-available/jemfinder > /dev/null << EOF
# JemFinder Nginx Configuration

# Backend API
upstream jemfinder-backend {
    server 127.0.0.1:9000;
}

# Frontend Dev Server
upstream jemfinder-frontend {
    server 127.0.0.1:5173;
}

server {
    listen 4000;
    server_name $SERVER_NAME;

    # Increase body size for file uploads
    client_max_body_size 10M;

    # Frontend - Proxy to Vite dev server
    location / {
        proxy_pass http://jemfinder-frontend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for Vite HMR
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Backend API
    location /api/ {
        proxy_pass http://jemfinder-backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for stock prices
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts for long-running requests (Gemini AI)
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://jemfinder-backend/api/v1/health;
        access_log off;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/jemfinder /etc/nginx/sites-enabled/

# Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Start Nginx if not running, then reload
echo "Starting/Reloading Nginx..."
if ! sudo systemctl is-active --quiet nginx; then
    echo "Starting Nginx service..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
else
    echo "Reloading Nginx service..."
    sudo systemctl reload nginx
fi

# Step 13: Setup Firewall
echo -e "\n${GREEN}🔥 Setting up Firewall...${NC}"
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 4000/tcp  # JemFinder HTTP
sudo ufw allow 80/tcp    # HTTP (for other services)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable || true

# Step 14: Show status
echo -e "\n${GREEN}✅ Deployment Complete!${NC}"
echo -e "\n📊 PM2 Status:"
pm2 status

echo -e "\n🌐 Access your application:"
echo "   Frontend: http://$SERVER_NAME:4000"
echo "   Backend API: http://$SERVER_NAME:4000/api/v1"
echo "   API Docs: http://$SERVER_NAME:4000/api/v1/docs"

echo -e "\n📝 Useful Commands:"
echo "   PM2 Logs: pm2 logs"
echo "   PM2 Status: pm2 status"
echo "   PM2 Restart: pm2 restart all"
echo "   Nginx Logs: sudo tail -f /var/log/nginx/error.log"
echo "   Nginx Reload: sudo systemctl reload nginx"

echo -e "\n${YELLOW}⚠️  Don't forget to:${NC}"
echo "   1. Update backend/.env with your API keys"
echo "   2. Update frontend/.env with correct VITE_API_URL"
echo "   3. Configure MongoDB connection"
echo "   4. Setup SSL with Let's Encrypt (optional but recommended)"

echo -e "\n${GREEN}🎉 Done!${NC}"


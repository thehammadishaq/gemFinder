# PM2 + Nginx Setup Guide - JemFinder

Complete step-by-step guide to deploy JemFinder using PM2 and Nginx.

---

## 📋 Prerequisites

- Ubuntu/Debian server
- SSH access
- Sudo privileges
- Project files on server

---

## 🚀 Quick Setup (Automated)

Run the deployment script:

```bash
cd /path/to/jemFinder
chmod +x deploy-pm2-nginx.sh
./deploy-pm2-nginx.sh
```

---

## 📝 Manual Setup (Step by Step)

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update

# Install Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -g pm2

# Install Nginx
sudo apt install -y nginx

# Install Python and pip (if not installed)
sudo apt install -y python3 python3-pip python3-venv
```

---

### Step 2: Setup Backend

```bash
# Navigate to backend directory
cd /path/to/jemFinder/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Setup environment variables
cp env.example .env
nano .env
```

**Edit `.env` file:**
```env
HOST=0.0.0.0
PORT=9000
DEBUG=True

MONGODB_URL=mongodb://localhost:27017
# OR MongoDB Atlas:
# MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/db

DATABASE_NAME=company_profiles_db

# CORS - Add your server IP/domain
CORS_ORIGINS=http://your-server-ip,http://your-domain.com

# API Keys
FINNHUB_API_KEY=your_finnhub_key_here
POLYGON_API_KEY=your_polygon_key_here

# Gemini (auto headless on server)
GEMINI_HEADLESS=true
```

---

### Step 3: Setup Frontend

```bash
# Navigate to frontend directory
cd /path/to/jemFinder/frontend

# Install dependencies
npm install

# Create .env file
nano .env
```

**Create `.env` file:**
```env
VITE_API_URL=http://your-server-ip:9000/api/v1
# OR with domain:
# VITE_API_URL=http://your-domain.com/api/v1
```

---

### Step 4: Start Services with PM2

#### Start Backend:

```bash
cd /path/to/jemFinder/backend
source venv/bin/activate

pm2 start "uvicorn main:app --host 0.0.0.0 --port 9000" \
    --name jemfinder-backend \
    --interpreter venv/bin/python \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z"
```

#### Start Frontend:

```bash
cd /path/to/jemFinder/frontend

pm2 start "npm run dev -- --host 0.0.0.0" \
    --name jemfinder-frontend \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z"
```

#### Save PM2 Configuration:

```bash
pm2 save
```

#### Setup PM2 Auto-start on Reboot:

```bash
pm2 startup
# Run the command it outputs (usually with sudo)
```

---

### Step 5: Configure Nginx

#### Create Nginx Configuration:

```bash
sudo nano /etc/nginx/sites-available/jemfinder
```

**Paste this configuration:**

```nginx
# Backend API
upstream backend {
    server 127.0.0.1:9000;
}

# Frontend Dev Server
upstream frontend {
    server 127.0.0.1:5173;
}

server {
    listen 80;
    server_name your-server-ip;  # Replace with your IP or domain

    # Increase body size for file uploads
    client_max_body_size 10M;

    # Frontend - Proxy to Vite dev server
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Vite HMR
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for stock prices
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts for long-running requests (Gemini AI)
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
    }

    # Health check
    location /health {
        proxy_pass http://backend/api/v1/health;
        access_log off;
    }
}
```

**Important:** Replace `your-server-ip` with your actual server IP address or domain name.

#### Enable Site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/jemfinder /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

### Step 6: Setup Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (if using SSL)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

### Step 7: Verify Everything Works

#### Check PM2 Status:

```bash
pm2 status
pm2 logs
```

#### Check Nginx Status:

```bash
sudo systemctl status nginx
```

#### Test Backend:

```bash
curl http://localhost:9000/api/v1/health
```

#### Test Frontend:

```bash
curl http://localhost:5173
```

#### Test via Nginx:

```bash
curl http://your-server-ip
curl http://your-server-ip/api/v1/health
```

---

## 🔧 Useful PM2 Commands

```bash
# View all processes
pm2 status

# View logs
pm2 logs
pm2 logs jemfinder-backend
pm2 logs jemfinder-frontend

# Restart services
pm2 restart all
pm2 restart jemfinder-backend
pm2 restart jemfinder-frontend

# Stop services
pm2 stop all
pm2 stop jemfinder-backend

# Delete services
pm2 delete jemfinder-backend

# Monitor (real-time)
pm2 monit

# Save current process list
pm2 save

# View process info
pm2 info jemfinder-backend
```

---

## 🔧 Useful Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx

# View logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## 🔒 Setup SSL (Optional but Recommended)

### Using Let's Encrypt:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

**Note:** SSL requires a domain name. For IP-only access, SSL setup is more complex.

---

## 🐛 Troubleshooting

### Backend not starting?

```bash
# Check PM2 logs
pm2 logs jemfinder-backend

# Check if port is in use
sudo lsof -i :9000

# Restart backend
pm2 restart jemfinder-backend
```

### Frontend not starting?

```bash
# Check PM2 logs
pm2 logs jemfinder-frontend

# Check if port is in use
sudo lsof -i :5173

# Restart frontend
pm2 restart jemfinder-frontend
```

### Nginx errors?

```bash
# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t

# Check if Nginx is running
sudo systemctl status nginx
```

### WebSocket not working?

- Ensure Nginx config has WebSocket headers
- Check firewall allows connections
- Verify backend is running on port 9000
- Check browser console for WebSocket errors

### CORS errors?

- Update `CORS_ORIGINS` in backend `.env`
- Include your server IP/domain
- Restart backend: `pm2 restart jemfinder-backend`

---

## 📊 Monitoring

### View PM2 Dashboard:

```bash
pm2 monit
```

### View Logs:

```bash
# All logs
pm2 logs

# Specific service
pm2 logs jemfinder-backend --lines 100

# Error logs only
pm2 logs jemfinder-backend --err
```

### System Resources:

```bash
# CPU and Memory usage
pm2 list
htop
```

---

## 🔄 Updating the Application

### Update Backend:

```bash
cd /path/to/jemFinder/backend
source venv/bin/activate
git pull  # If using git
pip install -r requirements.txt
pm2 restart jemfinder-backend
```

### Update Frontend:

```bash
cd /path/to/jemFinder/frontend
git pull  # If using git
npm install
pm2 restart jemfinder-frontend
```

---

## ✅ Checklist

- [ ] Node.js installed
- [ ] PM2 installed
- [ ] Nginx installed
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend .env configured
- [ ] Frontend .env configured
- [ ] Backend running with PM2
- [ ] Frontend running with PM2
- [ ] Nginx configured
- [ ] Firewall configured
- [ ] Services accessible via IP/domain
- [ ] WebSocket working
- [ ] SSL configured (optional)

---

## 🎉 Done!

Your application should now be accessible at:
- **Frontend**: `http://your-server-ip`
- **Backend API**: `http://your-server-ip/api/v1`
- **API Docs**: `http://your-server-ip/api/v1/docs`

---

**Need help?** Check logs and ensure all services are running!


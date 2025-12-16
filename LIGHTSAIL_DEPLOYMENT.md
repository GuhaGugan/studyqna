# Complete AWS Lightsail Deployment Guide - StudyQnA

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Lightsail Setup](#aws-lightsail-setup)
3. [Server Initial Configuration](#server-initial-configuration)
4. [Database Setup (PostgreSQL)](#database-setup-postgresql)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL Certificate Setup](#ssl-certificate-setup)
9. [Systemd Services](#systemd-services)
10. [Environment Variables](#environment-variables)
11. [Security Configuration](#security-configuration)
12. [Monitoring & Maintenance](#monitoring--maintenance)
13. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### **What You Need:**
- AWS Account
- Domain name (optional, but recommended)
- SSH client (PuTTY for Windows, Terminal for Mac/Linux)
- Basic Linux command knowledge

### **Estimated Costs:**
- Lightsail Instance: $5-10/month (1GB RAM, 1 vCPU)
- Static IP: Free (if attached to instance)
- Domain: ₹500-1,000/year (optional)
- SSL Certificate: Free (Let's Encrypt)

---

## 2. AWS Lightsail Setup

### **Step 1: Create Lightsail Instance**

1. **Login to AWS Console**
   - Go to https://lightsail.aws.amazon.com
   - Sign in with your AWS account

2. **Create Instance**
   - Click "Create instance"
   - **Instance location**: Choose closest to your users
   - **Platform**: Linux/Unix
   - **Blueprint**: Ubuntu 22.04 LTS
   - **Instance plan**: 
     - **Minimum**: $5/month (512MB RAM, 1 vCPU) - For testing
     - **Recommended**: $10/month (1GB RAM, 1 vCPU) - For production
     - **Better**: $20/month (2GB RAM, 1 vCPU) - For high traffic

3. **Instance Name**
   - Enter: `studyqna-server`
   - Click "Create instance"

4. **Wait for Instance to Start**
   - Status will change to "Running" (2-3 minutes)

### **Step 2: Create Static IP**

1. **Go to Networking Tab**
   - Click "Networking" in left sidebar
   - Click "Create static IP"

2. **Attach to Instance**
   - Select your instance: `studyqna-server`
   - Name: `studyqna-static-ip`
   - Click "Create"

3. **Note the IP Address**
   - Copy the static IP (e.g., `54.123.45.67`)
   - You'll need this for domain DNS

### **Step 3: Connect to Instance**

1. **Get SSH Key**
   - Click on your instance
   - Go to "Account" tab
   - Click "Download default key" (or use your own)
   - Save the `.pem` file securely

2. **Connect via SSH**

   **Windows (PuTTY):**
   ```bash
   # Convert .pem to .ppk using PuTTYgen
   # Then connect using PuTTY with the .ppk file
   ```

   **Mac/Linux:**
   ```bash
   chmod 400 /path/to/your-key.pem
   ssh -i /path/to/your-key.pem ubuntu@YOUR_STATIC_IP
   ```

   **Windows (WSL/Git Bash):**
   ```bash
   chmod 400 /path/to/your-key.pem
   ssh -i /path/to/your-key.pem ubuntu@YOUR_STATIC_IP
   ```

---

## 3. Server Initial Configuration

### **Step 1: Update System**

```bash
# Update package list
sudo apt update

# Upgrade system
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git build-essential software-properties-common
```

### **Step 2: Create Application User**

```bash
# Create dedicated user for application
sudo adduser --disabled-password --gecos "" studyqna
sudo usermod -aG sudo studyqna

# Switch to application user
sudo su - studyqna
```

### **Step 3: Setup Firewall**

```bash
# Install UFW (Uncomplicated Firewall)
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### **Step 4: Setup Swap (Optional but Recommended)**

```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make it permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 4. Database Setup (PostgreSQL)

### **Step 1: Install PostgreSQL**

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

### **Step 2: Configure PostgreSQL**

```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL prompt:
CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD 'YOUR_STRONG_PASSWORD_HERE';
ALTER ROLE studyqna_user SET client_encoding TO 'utf8';
ALTER ROLE studyqna_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE studyqna_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;
\q
```

**Important:** Replace `YOUR_STRONG_PASSWORD_HERE` with a strong password (save it securely!)

### **Step 3: Configure PostgreSQL for Remote Access (Optional)**

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/14/main/postgresql.conf

# Find and uncomment:
# listen_addresses = 'localhost'

# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add at the end:
# host    studyqna    studyqna_user    127.0.0.1/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## 5. Backend Deployment

### **Step 1: Install Python 3.11+**

```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install additional dependencies
sudo apt install -y libpq-dev pkg-config

# Verify installation
python3.11 --version
```

### **Step 2: Install System Dependencies**

```bash
# Install dependencies for OCR and image processing
sudo apt install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y poppler-utils

# Install Playwright dependencies (for PDF generation)
sudo apt install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2
```

### **Step 3: Clone Repository**

```bash
# Navigate to home directory
cd ~

# Clone your repository (replace with your repo URL)
git clone https://github.com/yourusername/studyqna.git

# Or upload files via SCP
# scp -i /path/to/key.pem -r /local/path/to/studyqna ubuntu@YOUR_IP:~/

# Navigate to backend
cd ~/studyqna/backend
```

### **Step 4: Setup Python Virtual Environment**

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### **Step 5: Install Playwright Browser**

```bash
# Install Chromium for Playwright
playwright install chromium

# Or install all browsers
playwright install
```

### **Step 6: Download Fonts (for Multilingual Support)**

```bash
# Create fonts directory
mkdir -p ~/studyqna/backend/app/fonts

# Download fonts (if not already in repo)
cd ~/studyqna/backend/app/fonts

# Download Google Noto fonts
wget https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf
```

### **Step 7: Create Storage Directory**

```bash
# Create storage directory
mkdir -p ~/studyqna/backend/storage
chmod 755 ~/studyqna/backend/storage
```

### **Step 8: Initialize Database**

```bash
# Activate virtual environment
source ~/studyqna/backend/venv/bin/activate

# Run database initialization
cd ~/studyqna/backend
python init_db.py
```

---

## 6. Frontend Deployment

### **Step 1: Install Node.js 18+**

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

### **Step 2: Build Frontend**

```bash
# Navigate to frontend directory
cd ~/studyqna/frontend

# Install dependencies
npm install

# Create production build
npm run build

# The build will be in: ~/studyqna/frontend/dist
```

### **Step 3: Test Build**

```bash
# Install serve globally (for testing)
sudo npm install -g serve

# Test the build
serve -s dist -l 3000

# Visit http://YOUR_IP:3000 to test
# Press Ctrl+C to stop
```

---

## 7. Nginx Configuration

### **Step 1: Install Nginx**

```bash
# Install Nginx
sudo apt install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### **Step 2: Configure Nginx for Backend**

```bash
# Create backend configuration
sudo nano /etc/nginx/sites-available/studyqna-backend
```

**Add this configuration:**

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for AI processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Frontend
    location / {
        root /home/studyqna/studyqna/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        root /home/studyqna/studyqna/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload size limit
    client_max_body_size 10M;
}
```

**Save and exit (Ctrl+X, Y, Enter)**

### **Step 3: Enable Site**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/studyqna-backend /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## 8. SSL Certificate Setup

### **Step 1: Install Certbot**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### **Step 2: Obtain SSL Certificate**

**If you have a domain:**

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose redirect HTTP to HTTPS (option 2)
```

**If you don't have a domain:**

- You can use the static IP, but SSL won't work
- Consider using Cloudflare or similar for free SSL

### **Step 3: Auto-Renewal**

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up renewal
# Check with:
sudo systemctl status certbot.timer
```

---

## 9. Systemd Services

### **Step 1: Create Backend Service**

```bash
# Create service file
sudo nano /etc/systemd/system/studyqna-backend.service
```

**Add this configuration:**

```ini
[Unit]
Description=StudyQnA Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=studyqna
Group=studyqna
WorkingDirectory=/home/studyqna/studyqna/backend
Environment="PATH=/home/studyqna/studyqna/backend/venv/bin"
ExecStart=/home/studyqna/studyqna/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save and exit**

### **Step 2: Enable and Start Service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable studyqna-backend

# Start service
sudo systemctl start studyqna-backend

# Check status
sudo systemctl status studyqna-backend

# View logs
sudo journalctl -u studyqna-backend -f
```

---

## 10. Environment Variables

### **Step 1: Create .env File**

```bash
# Navigate to backend
cd ~/studyqna/backend

# Create .env file
nano .env
```

### **Step 2: Add Environment Variables**

```bash
# Database
DATABASE_URL=postgresql://studyqna_user:YOUR_PASSWORD@localhost:5432/studyqna

# JWT Secret (generate a strong secret)
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Admin
ADMIN_EMAIL=admin@yourdomain.com

# Storage
STORAGE_PATH=/home/studyqna/studyqna/backend/storage
ENCRYPT_STORAGE=true

# Email - Brevo (Recommended)
BREVO_API_KEY=your-brevo-api-key
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=StudyQnA
EMAIL_PROVIDER=brevo

# Email - SMTP (Alternative)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=StudyQnA <noreply@yourdomain.com>

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# App
APP_NAME=StudyQnA Generator
APP_URL=https://yourdomain.com

# CORS (add your domain)
CORS_ORIGINS=["https://yourdomain.com","http://localhost:3000"]

# Limits
MAX_PDF_SIZE_MB=5
MAX_IMAGE_SIZE_MB=10
MAX_PDF_PAGES=40
MAX_FREE_PDF_PAGES=10
MAX_QUESTIONS_PER_GENERATE=20
PREMIUM_PDF_QUOTA=15
PREMIUM_IMAGE_QUOTA=20
PREMIUM_VALIDITY_DAYS=30

# AI Usage
AI_USAGE_THRESHOLD_TOKENS=1000000
AI_USAGE_ALERT_EMAIL=admin@yourdomain.com
```

**Important:** Replace all placeholder values with your actual credentials!

### **Step 3: Secure .env File**

```bash
# Set proper permissions
chmod 600 ~/studyqna/backend/.env

# Verify
ls -la ~/studyqna/backend/.env
```

### **Step 4: Update Systemd Service to Use .env**

The service will automatically read `.env` from the working directory.

---

## 11. Security Configuration

### **Step 1: Setup Fail2Ban**

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create local config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit config
sudo nano /etc/fail2ban/jail.local

# Set:
# bantime = 3600
# findtime = 600
# maxretry = 5

# Start Fail2Ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### **Step 2: Disable Root Login**

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Set:
# PermitRootLogin no
# PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### **Step 3: Setup Automatic Security Updates**

```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades

# Configure
sudo dpkg-reconfigure -plow unattended-upgrades

# Enable
sudo systemctl enable unattended-upgrades
```

### **Step 4: Setup Log Rotation**

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/studyqna
```

**Add:**

```
/home/studyqna/studyqna/backend/storage/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 12. Monitoring & Maintenance

### **Step 1: Setup Log Monitoring**

```bash
# View backend logs
sudo journalctl -u studyqna-backend -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View system logs
sudo journalctl -xe
```

### **Step 2: Setup Disk Space Monitoring**

```bash
# Check disk usage
df -h

# Check storage directory
du -sh ~/studyqna/backend/storage

# Setup cleanup script (optional)
nano ~/cleanup-storage.sh
```

**Add cleanup script:**

```bash
#!/bin/bash
# Delete files older than 90 days
find /home/studyqna/studyqna/backend/storage -type f -mtime +90 -delete
```

```bash
# Make executable
chmod +x ~/cleanup-storage.sh

# Add to crontab (run weekly)
crontab -e
# Add: 0 2 * * 0 /home/studyqna/cleanup-storage.sh
```

### **Step 3: Setup Backup**

```bash
# Create backup script
nano ~/backup-database.sh
```

**Add backup script:**

```bash
#!/bin/bash
BACKUP_DIR="/home/studyqna/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U studyqna_user studyqna > $BACKUP_DIR/db_$DATE.sql

# Backup storage (optional)
tar -czf $BACKUP_DIR/storage_$DATE.tar.gz ~/studyqna/backend/storage

# Delete backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

```bash
# Make executable
chmod +x ~/backup-database.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/studyqna/backup-database.sh
```

### **Step 4: Monitor Resources**

```bash
# Install monitoring tools
sudo apt install -y htop iotop

# Check CPU and memory
htop

# Check disk I/O
iotop
```

---

## 13. Troubleshooting

### **Backend Not Starting**

```bash
# Check service status
sudo systemctl status studyqna-backend

# Check logs
sudo journalctl -u studyqna-backend -n 50

# Common issues:
# 1. Database connection error - Check DATABASE_URL in .env
# 2. Port already in use - Check: sudo lsof -i :8000
# 3. Missing dependencies - Reinstall: pip install -r requirements.txt
```

### **Nginx Not Working**

```bash
# Check Nginx status
sudo systemctl status nginx

# Check configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Common issues:
# 1. Port 80/443 already in use
# 2. Configuration syntax error
# 3. Permission issues
```

### **Database Connection Issues**

```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "SELECT version();"

# Check if database exists
sudo -u postgres psql -l | grep studyqna

# Test connection with user
psql -U studyqna_user -d studyqna -h localhost
```

### **SSL Certificate Issues**

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Check Nginx SSL config
sudo nginx -t
```

### **High Memory Usage**

```bash
# Check memory usage
free -h

# Check what's using memory
ps aux --sort=-%mem | head

# Reduce backend workers in systemd service
# Change --workers 2 to --workers 1
```

### **Storage Full**

```bash
# Check disk usage
df -h

# Find large files
du -sh ~/studyqna/backend/storage/* | sort -h

# Clean old files
find ~/studyqna/backend/storage -type f -mtime +90 -delete
```

---

## 14. Post-Deployment Checklist

### **✅ Verification Steps**

- [ ] Backend service is running: `sudo systemctl status studyqna-backend`
- [ ] Nginx is running: `sudo systemctl status nginx`
- [ ] Database is accessible: `psql -U studyqna_user -d studyqna`
- [ ] Frontend loads: Visit `https://yourdomain.com`
- [ ] API works: Visit `https://yourdomain.com/api/docs`
- [ ] SSL certificate is valid: Check browser padlock
- [ ] File upload works: Test PDF/image upload
- [ ] Q/A generation works: Generate test questions
- [ ] Downloads work: Download PDF/DOCX/TXT
- [ ] Email OTP works: Request OTP
- [ ] Admin dashboard accessible: Login as admin

### **✅ Security Checklist**

- [ ] Firewall is enabled: `sudo ufw status`
- [ ] SSH key authentication only
- [ ] Root login disabled
- [ ] Fail2Ban is running: `sudo systemctl status fail2ban`
- [ ] SSL certificate is valid
- [ ] .env file has correct permissions (600)
- [ ] Strong passwords for database
- [ ] Regular backups configured

### **✅ Performance Checklist**

- [ ] Swap is configured (if needed)
- [ ] Log rotation is setup
- [ ] Storage cleanup is scheduled
- [ ] Backups are running
- [ ] Monitoring is in place

---

## 15. Quick Reference Commands

### **Service Management**

```bash
# Backend
sudo systemctl start studyqna-backend
sudo systemctl stop studyqna-backend
sudo systemctl restart studyqna-backend
sudo systemctl status studyqna-backend
sudo journalctl -u studyqna-backend -f

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo nginx -t

# PostgreSQL
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
```

### **Logs**

```bash
# Backend logs
sudo journalctl -u studyqna-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -xe
```

### **Updates**

```bash
# Update application code
cd ~/studyqna
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart studyqna-backend

# Update frontend
cd ~/studyqna/frontend
npm install
npm run build
sudo systemctl reload nginx
```

---

## 16. Domain Setup (Optional)

### **Step 1: Point Domain to Lightsail IP**

1. **Go to your domain registrar** (GoDaddy, Namecheap, etc.)
2. **Add A Record:**
   - Type: A
   - Name: @ (or www)
   - Value: Your Lightsail static IP
   - TTL: 3600

3. **Wait for DNS propagation** (5 minutes to 48 hours)

### **Step 2: Update Nginx Configuration**

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/studyqna-backend

# Replace YOUR_DOMAIN_OR_IP with your domain
# server_name yourdomain.com www.yourdomain.com;

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### **Step 3: Get SSL Certificate**

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 17. Scaling Considerations

### **If You Need More Resources:**

1. **Upgrade Lightsail Instance**
   - Go to Lightsail console
   - Click on instance
   - Click "Change plan"
   - Choose higher plan

2. **Add Load Balancer** (for multiple instances)
   - Create multiple instances
   - Setup Lightsail load balancer
   - Distribute traffic

3. **Use RDS for Database** (for production)
   - Create AWS RDS PostgreSQL instance
   - Update DATABASE_URL
   - Better performance and backups

---

## 18. Support & Resources

### **Useful Links:**
- AWS Lightsail Documentation: https://lightsail.aws.amazon.com/ls/docs/
- Nginx Documentation: https://nginx.org/en/docs/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Let's Encrypt: https://letsencrypt.org/

### **Common Issues:**
- Check logs first: `sudo journalctl -u studyqna-backend -n 50`
- Verify environment variables: `cat ~/studyqna/backend/.env`
- Test database connection: `psql -U studyqna_user -d studyqna`
- Check Nginx config: `sudo nginx -t`

---

**🎉 Deployment Complete!**

Your StudyQnA application should now be running on AWS Lightsail!

Visit: `https://yourdomain.com` or `http://YOUR_STATIC_IP`

For API docs: `https://yourdomain.com/api/docs`

---

*Last Updated: Complete Lightsail deployment guide for Ubuntu 22.04*



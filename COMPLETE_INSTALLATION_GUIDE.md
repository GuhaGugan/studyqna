# 🚀 Complete AWS Lightsail Installation Guide
## StudyQnA Assistant - Step-by-Step Deployment with SSL Certificate

**Version:** 1.0  
**Last Updated:** January 2025  
**Estimated Time:** 2-3 hours (first time)  
**Difficulty:** Beginner to Intermediate

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Part 1: AWS Lightsail Setup](#part-1-aws-lightsail-setup)
4. [Part 2: Connect to Your Server](#part-2-connect-to-your-server)
5. [Part 3: Initial Server Configuration](#part-3-initial-server-configuration)
6. [Part 4: Database Setup](#part-4-database-setup)
7. [Part 5: Upload Application Files](#part-5-upload-application-files)
8. [Part 6: Backend Installation](#part-6-backend-installation)
9. [Part 7: Frontend Installation](#part-7-frontend-installation)
10. [Part 8: Nginx Web Server Setup](#part-8-nginx-web-server-setup)
11. [Part 9: SSL Certificate Configuration (HTTPS)](#part-9-ssl-certificate-configuration-https)
12. [Part 10: Domain Configuration](#part-10-domain-configuration)
13. [Part 11: Final Testing](#part-11-final-testing)
14. [Part 12: Maintenance & Monitoring](#part-12-maintenance--monitoring)
15. [Troubleshooting](#troubleshooting)
16. [Quick Reference Commands](#quick-reference-commands)

---

## Introduction

This guide will walk you through deploying the StudyQnA Assistant application on AWS Lightsail, including setting up a secure HTTPS connection with SSL certificates. Even if you're new to server management, follow each step carefully, and you'll have your application running in a few hours.

### 🚀 Quick Installation Option

**Want to automate the installation?** Use the automated installation script:

```bash
# Upload script to server
scp -i your-key.pem install.sh ubuntu@YOUR_SERVER_IP:~/

# Make executable and run
chmod +x install.sh
./install.sh
```

The script automates steps 3-10 of this guide. See `INSTALL_SCRIPT_README.md` for details.

**For manual step-by-step installation, continue below.**

### What You'll Learn:
- How to create and configure an AWS Lightsail server
- How to install and configure PostgreSQL database
- How to deploy a Python backend and React frontend
- How to set up Nginx as a web server
- How to obtain and configure SSL certificates for HTTPS
- How to configure your domain name
- How to monitor and maintain your application

### Estimated Costs:
- **AWS Lightsail Instance:** $10/month (1GB RAM, 1 vCPU) - Recommended
- **Static IP:** Free (included with instance)
- **Domain Name:** ₹500-1,000/year (optional but recommended)
- **SSL Certificate:** Free (Let's Encrypt)
- **Total Monthly Cost:** ~$10/month (~₹800/month)

---

## Prerequisites

Before you begin, make sure you have:

### Required:
- ✅ **AWS Account** - Create at [https://aws.amazon.com](https://aws.amazon.com)
- ✅ **Credit Card** - For AWS account (free tier available, but Lightsail is paid)
- ✅ **Domain Name** (optional but recommended) - Purchase from GoDaddy, Namecheap, etc.
- ✅ **OpenAI API Key** - Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- ✅ **Email Service API Key** - Brevo (recommended) or Gmail App Password

### Software Tools:
- ✅ **SSH Client:**
  - **Windows:** [PuTTY](https://www.putty.org/) or [WinSCP](https://winscp.net/)
  - **Mac/Linux:** Built-in Terminal
  - **Windows 10/11:** WSL (Windows Subsystem for Linux) or Git Bash

### Knowledge:
- Basic understanding of command line (we'll guide you through everything)
- Ability to copy and paste commands
- Patience to follow step-by-step instructions

---

## Part 1: AWS Lightsail Setup

### Step 1.1: Create AWS Account

1. Go to [https://aws.amazon.com](https://aws.amazon.com)
2. Click **"Create an AWS Account"**
3. Follow the registration process:
   - Enter your email and password
   - Provide payment information (required, but Lightsail has a free trial)
   - Verify your phone number
4. Wait for account activation (usually instant)

### Step 1.2: Navigate to Lightsail

1. After logging in, search for **"Lightsail"** in the AWS services search bar
2. Click on **"Amazon Lightsail"**
3. You'll see the Lightsail dashboard

### Step 1.3: Create Lightsail Instance

1. Click the **"Create instance"** button (orange button, top right)

2. **Choose your instance location:**
   - Select the region closest to your users (e.g., **Mumbai (ap-south-1)** for Indian users)
   - This affects latency and performance

3. **Choose your platform:**
   - Select **"Linux/Unix"**

4. **Choose your blueprint:**
   - Select **"Ubuntu 22.04 LTS"** (Long Term Support version)

5. **Choose your instance plan:**
   - **Recommended:** **$10/month** plan
     - 1 GB RAM
     - 1 vCPU
     - 40 GB SSD storage
     - 2 TB data transfer
   - **For testing:** $5/month (512 MB RAM) - May be slow
   - **For high traffic:** $20/month (2 GB RAM) - Better performance

6. **Identify your instance:**
   - **Instance name:** Enter `studyqna-server`
   - This is just a label for your reference

7. **Review and create:**
   - Review your selections
   - Click **"Create instance"**

8. **Wait for instance to start:**
   - Status will show "Pending" → "Running"
   - This takes 2-3 minutes
   - You'll see a green checkmark when ready

### Step 1.4: Create Static IP Address

A static IP ensures your server's address doesn't change when you restart it.

1. In the Lightsail dashboard, click **"Networking"** in the left sidebar

2. Click **"Create static IP"**

3. **Attach static IP:**
   - **Attach to an instance:** Select `studyqna-server`
   - **Name:** Enter `studyqna-static-ip`

4. Click **"Create static IP"**

5. **Copy your static IP address:**
   - You'll see an IP address like `54.123.45.67`
   - **Write this down** - You'll need it throughout this guide
   - Example: `54.123.45.67`

### Step 1.5: Download SSH Key

You need an SSH key to securely connect to your server.

1. Click on your instance name (`studyqna-server`)

2. Go to the **"Account"** tab

3. Click **"Download default key"** (or use your own if you have one)

4. **Save the `.pem` file securely:**
   - Windows: Save to `C:\Users\YourName\Downloads\lightsail-key.pem`
   - Mac/Linux: Save to `~/Downloads/lightsail-key.pem`
   - **Important:** Don't lose this file! You'll need it to connect to your server.

---

## Part 2: Connect to Your Server

### Step 2.1: Connect via SSH (Choose Your Method)

#### **Method A: Windows with PuTTY (Recommended for Windows)**

1. **Download PuTTY:**
   - Go to [https://www.putty.org/](https://www.putty.org/)
   - Download and install PuTTY

2. **Download PuTTYgen:**
   - Also download PuTTYgen (comes with PuTTY)
   - This converts `.pem` files to `.ppk` format

3. **Convert your key:**
   - Open **PuTTYgen**
   - Click **"Load"**
   - Select your `lightsail-key.pem` file
   - Change file type filter to **"All Files (*.*)"** if needed
   - Click **"Save private key"**
   - Save as `lightsail-key.ppk` (you can close PuTTYgen now)

4. **Connect with PuTTY:**
   - Open **PuTTY**
   - In the **"Host Name"** field, enter: `ubuntu@YOUR_STATIC_IP`
     - Replace `YOUR_STATIC_IP` with your actual IP (e.g., `ubuntu@54.123.45.67`)
   - **Port:** `22`
   - **Connection type:** `SSH`

5. **Configure authentication:**
   - In the left sidebar, expand **"SSH"**
   - Click **"Auth"**
   - Click **"Browse"** next to "Private key file for authentication"
   - Select your `lightsail-key.ppk` file

6. **Save session (optional):**
   - Go back to **"Session"** in the left sidebar
   - Enter a name like `StudyQnA Server`
   - Click **"Save"** (so you can reuse this connection)

7. **Connect:**
   - Click **"Open"**
   - If you see a security warning, click **"Yes"**
   - You should now see a terminal prompt: `ubuntu@ip-172-26-3-115:~$`

#### **Method B: Mac/Linux Terminal**

1. **Open Terminal** (Applications → Utilities → Terminal on Mac)

2. **Set correct permissions on your key:**
   ```bash
   chmod 400 ~/Downloads/lightsail-key.pem
   ```

3. **Connect to server:**
   ```bash
   ssh -i ~/Downloads/lightsail-key.pem ubuntu@YOUR_STATIC_IP
   ```
   Replace `YOUR_STATIC_IP` with your actual IP address.

4. **If you see a security warning, type `yes` and press Enter**

5. You should now see: `ubuntu@ip-172-26-3-115:~$`

#### **Method C: Windows with WSL or Git Bash**

1. **Open WSL** (Windows Subsystem for Linux) or **Git Bash**

2. **Set permissions:**
   ```bash
   chmod 400 /mnt/c/Users/YourName/Downloads/lightsail-key.pem
   ```

3. **Connect:**
   ```bash
   ssh -i /mnt/c/Users/YourName/Downloads/lightsail-key.pem ubuntu@YOUR_STATIC_IP
   ```

### Step 2.2: Verify Connection

Once connected, you should see:
```
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-...)
...
ubuntu@ip-172-26-3-115:~$
```

**Congratulations!** You're now connected to your server. Keep this terminal window open for the rest of the installation.

---

## Part 3: Initial Server Configuration

### Step 3.1: Update System Packages

Run these commands one by one (copy and paste, press Enter after each):

```bash
# Update package list
sudo apt update
```

Wait for it to finish, then:

```bash
# Upgrade all packages
sudo apt upgrade -y
```

This may take 5-10 minutes. Type `Y` if prompted.

### Step 3.2: Install Essential Tools

```bash
# Install essential development tools
sudo apt install -y curl wget git build-essential software-properties-common
```

### Step 3.3: Create Application User

We'll create a dedicated user for the application (better security):

```bash
# Create user named 'studyqna' (no password login, SSH key only)
sudo adduser --disabled-password --gecos "" studyqna

# Add user to sudo group (allows running admin commands)
sudo usermod -aG sudo studyqna

# Switch to the new user
sudo su - studyqna
```

You should now see: `studyqna@ip-172-26-3-115:~$`

**Note:** If you need to use `sudo` commands, you'll be prompted for the `ubuntu` user's password (if you set one) or you can switch back to `ubuntu` user temporarily.

### Step 3.4: Setup Firewall

```bash
# Install UFW (Uncomplicated Firewall)
sudo apt install -y ufw

# Allow SSH (port 22) - IMPORTANT: Do this first!
sudo ufw allow 22/tcp

# Allow HTTP (port 80) - For web traffic
sudo ufw allow 80/tcp

# Allow HTTPS (port 443) - For secure web traffic
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Type 'y' when prompted

# Check firewall status
sudo ufw status
```

You should see:
```
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

### Step 3.5: Setup Swap Memory (Optional but Recommended)

Swap helps prevent out-of-memory errors:

```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile

# Set correct permissions
sudo chmod 600 /swapfile

# Format as swap
sudo mkswap /swapfile

# Enable swap
sudo swapon /swapfile

# Make it permanent (survives reboots)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap is active
free -h
```

You should see swap listed in the output.

---

## Part 4: Database Setup

### Step 4.1: Install PostgreSQL

```bash
# Install PostgreSQL and additional tools
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql

# Enable PostgreSQL to start on boot
sudo systemctl enable postgresql

# Check status (should show 'active (running)')
sudo systemctl status postgresql
```

Press `q` to exit the status view.

### Step 4.2: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql
```

You should see: `postgres=#`

Now run these SQL commands (one at a time):

```sql
-- Create database
CREATE DATABASE studyqna;

-- Create user with password (REPLACE 'YourSecurePassword123!' with a strong password)
CREATE USER studyqna_user WITH PASSWORD 'YourSecurePassword123!';

-- Set encoding
ALTER ROLE studyqna_user SET client_encoding TO 'utf8';

-- Set transaction isolation
ALTER ROLE studyqna_user SET default_transaction_isolation TO 'read committed';

-- Set timezone
ALTER ROLE studyqna_user SET timezone TO 'UTC';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;

-- Exit PostgreSQL
\q
```

**⚠️ IMPORTANT:** 
- Replace `'YourSecurePassword123!'` with a **strong password**
- **Write this password down** - You'll need it for the `.env` file
- Use a mix of uppercase, lowercase, numbers, and symbols
- Example: `MyStr0ng!P@ssw0rd2024`

### Step 4.3: Test Database Connection

```bash
# Test connection (you'll be prompted for the password)
psql -U studyqna_user -d studyqna -h localhost
```

Enter the password you just created. If successful, you'll see: `studyqna=>`

Type `\q` and press Enter to exit.

---

## Part 5: Upload Application Files

You need to get your application code onto the server. Choose one method:

### Method A: Using Git (Recommended)

If your code is in a Git repository (GitHub, GitLab, etc.):

```bash
# Navigate to home directory
cd ~

# Clone your repository (REPLACE with your actual repository URL)
git clone https://github.com/yourusername/studyqna.git

# OR if using SSH:
# git clone git@github.com:yourusername/studyqna.git

# Navigate into the project
cd studyqna

# Verify files are there
ls -la
```

You should see folders like `backend`, `frontend`, etc.

### Method B: Using SCP (File Transfer)

If your code is on your local machine:

**From your local computer** (open a new terminal/PowerShell window):

**Windows (PowerShell):**
```powershell
# Navigate to your project folder
cd C:\path\to\your\studyqna\project

# Upload all files
scp -i C:\path\to\lightsail-key.pem -r * ubuntu@YOUR_STATIC_IP:/home/studyqna/studyqna/
```

**Mac/Linux:**
```bash
# Navigate to your project folder
cd /path/to/your/studyqna/project

# Upload all files
scp -i ~/Downloads/lightsail-key.pem -r * ubuntu@YOUR_STATIC_IP:/home/studyqna/studyqna/
```

**Then on the server:**
```bash
# Verify files
cd ~/studyqna
ls -la
```

### Method C: Using WinSCP (Windows GUI)

1. Download [WinSCP](https://winscp.net/)
2. Connect using your `.ppk` file (convert `.pem` to `.ppk` first using PuTTYgen)
3. Drag and drop your project folder to `/home/studyqna/`

---

## Part 6: Backend Installation

### Step 6.1: Install Python 3.11

```bash
# Install Python 3.11 and dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL development libraries
sudo apt install -y libpq-dev pkg-config

# Verify installation
python3.11 --version
```

Should show: `Python 3.11.x`

### Step 6.2: Install System Dependencies

```bash
# Install OCR and image processing tools
sudo apt install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y poppler-utils

# Install Playwright dependencies (for PDF generation)
sudo apt install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2
```

### Step 6.3: Setup Python Virtual Environment

```bash
# Navigate to backend directory
cd ~/studyqna/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt now
# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

This may take 5-10 minutes. Wait for it to complete.

### Step 6.4: Install Playwright Browser

```bash
# Make sure you're still in the virtual environment (you should see (venv))
# Install Chromium for Playwright
playwright install chromium

# OR install all browsers (takes longer but more complete)
# playwright install
```

### Step 6.5: Download Fonts (for Multilingual Support)

```bash
# Create fonts directory
mkdir -p ~/studyqna/backend/app/fonts

# Navigate to fonts directory
cd ~/studyqna/backend/app/fonts

# Download Google Noto fonts (for Tamil, Hindi, etc.)
wget https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf

# Go back to backend directory
cd ~/studyqna/backend
```

### Step 6.6: Create Storage Directory

```bash
# Create storage directory
mkdir -p ~/studyqna/backend/storage

# Set permissions
chmod 755 ~/studyqna/backend/storage
```

### Step 6.7: Create Environment Variables File (.env)

```bash
# Make sure you're in the backend directory
cd ~/studyqna/backend

# Create .env file
nano .env
```

This opens the nano text editor. **Copy and paste the following**, then **replace the placeholder values** with your actual credentials:

```env
# ============================================
# DATABASE CONFIGURATION
# ============================================
# Replace 'YourSecurePassword123!' with the password you created in Step 4.2
DATABASE_URL=postgresql://studyqna_user:YourSecurePassword123!@localhost:5432/studyqna

# ============================================
# JWT SECURITY
# ============================================
# Generate a secret key by running this command in another terminal:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and paste it below
SECRET_KEY=your-generated-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# ADMIN CONFIGURATION
# ============================================
# Your email address (will automatically get admin role)
ADMIN_EMAIL=your-email@example.com

# ============================================
# STORAGE CONFIGURATION
# ============================================
STORAGE_PATH=/home/studyqna/studyqna/backend/storage
ENCRYPT_STORAGE=true

# ============================================
# EMAIL CONFIGURATION
# ============================================
# Choose: "brevo" (recommended) or "smtp"
EMAIL_PROVIDER=brevo

# ============================================
# BREVO API (Recommended)
# ============================================
# Get API key from: https://app.brevo.com/settings/keys/api
BREVO_API_KEY=your-brevo-api-key-here
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=StudyQnA

# ============================================
# SMTP CONFIGURATION (Alternative)
# ============================================
# Only needed if EMAIL_PROVIDER=smtp
# For Gmail: Generate App Password from https://myaccount.google.com/apppasswords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=StudyQnA <noreply@yourdomain.com>

# ============================================
# OPENAI CONFIGURATION
# ============================================
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# ============================================
# APPLICATION CONFIGURATION
# ============================================
APP_NAME=StudyQnA Generator
# Replace with your domain or static IP
# If using domain: https://yourdomain.com
# If using IP only: http://YOUR_STATIC_IP
APP_URL=http://YOUR_STATIC_IP

# ============================================
# CORS CONFIGURATION
# ============================================
# Comma-separated list of allowed origins
# If using domain: https://yourdomain.com,https://www.yourdomain.com
# If using IP only: http://YOUR_STATIC_IP
CORS_ORIGINS_LIST=http://YOUR_STATIC_IP

# ============================================
# AI USAGE TRACKING (Optional)
# ============================================
AI_USAGE_THRESHOLD_TOKENS=1000000
AI_USAGE_ALERT_EMAIL=admin@yourdomain.com
```

**To save and exit nano:**
1. Press `Ctrl + X`
2. Press `Y` to confirm
3. Press `Enter` to save

**Generate SECRET_KEY:**
Open a new terminal/SSH session and run:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output and paste it as `SECRET_KEY` in your `.env` file.

### Step 6.8: Secure .env File

```bash
# Set proper permissions (only owner can read/write)
chmod 600 ~/studyqna/backend/.env

# Verify permissions
ls -la ~/studyqna/backend/.env
```

Should show: `-rw-------` (only you can read/write)

### Step 6.9: Initialize Database

```bash
# Make sure you're in the backend directory and virtual environment is activated
cd ~/studyqna/backend
source venv/bin/activate

# Initialize database tables
python init_db.py
```

You should see success messages. If there are errors, check your `DATABASE_URL` in `.env`.

### Step 6.10: Test Backend (Optional)

```bash
# Start backend server (for testing)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Press `Ctrl + C` to stop** (we'll set up a proper service later).

---

## Part 7: Frontend Installation

### Step 7.1: Install Node.js 18

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Install Node.js
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

Should show: `v18.x.x` and `9.x.x` or higher

### Step 7.2: Build Frontend

```bash
# Navigate to frontend directory
cd ~/studyqna/frontend

# Install dependencies
npm install
```

This may take 5-10 minutes. Wait for completion.

```bash
# Create production build
npm run build
```

This may take 2-5 minutes. Wait for completion.

```bash
# Verify build was created
ls -la ~/studyqna/frontend/dist
```

You should see files like `index.html`, `assets/`, etc.

---

## Part 8: Nginx Web Server Setup

Nginx will serve your frontend and route API requests to the backend.

### Step 8.1: Install Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Start Nginx
sudo systemctl start nginx

# Enable Nginx to start on boot
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

Press `q` to exit.

### Step 8.2: Configure Nginx

```bash
# Create Nginx configuration file
sudo nano /etc/nginx/sites-available/studyqna
```

**Copy and paste this configuration:**

```nginx
server {
    listen 80;
    server_name YOUR_STATIC_IP_OR_DOMAIN;

    # Frontend - Serve React app
    location / {
        root /home/studyqna/studyqna/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # Backend API - Proxy to FastAPI
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
        
        # Increase timeouts for AI processing (5 minutes)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # Static files caching (CSS, JS, images)
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        root /home/studyqna/studyqna/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload size limit (100MB for large PDFs and mobile photos)
    client_max_body_size 100M;
}
```

**Important:** Replace `YOUR_STATIC_IP_OR_DOMAIN` with:
- Your static IP (e.g., `54.123.45.67`) if you don't have a domain yet
- Your domain (e.g., `yourdomain.com www.yourdomain.com`) if you have one

**Save and exit:** `Ctrl + X`, then `Y`, then `Enter`

### Step 8.3: Enable Site

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/studyqna /etc/nginx/sites-enabled/

# Remove default Nginx site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration (should show "syntax is ok")
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

### Step 8.4: Create Systemd Service for Backend

This makes the backend start automatically and restart if it crashes.

```bash
# Create service file
sudo nano /etc/systemd/system/studyqna-backend.service
```

**Copy and paste this:**

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

**Save and exit:** `Ctrl + X`, then `Y`, then `Enter`

### Step 8.5: Start Backend Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable studyqna-backend

# Start service
sudo systemctl start studyqna-backend

# Check status (should show "active (running)")
sudo systemctl status studyqna-backend
```

Press `q` to exit.

**View logs:**
```bash
# View real-time logs
sudo journalctl -u studyqna-backend -f

# Press Ctrl+C to stop viewing logs
```

---

## Part 9: SSL Certificate Configuration (HTTPS)

SSL certificates enable HTTPS (secure, encrypted connections). We'll use Let's Encrypt (free).

### Step 9.1: Install Certbot

```bash
# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx
```

### Step 9.2: Obtain SSL Certificate

**Option A: If you have a domain name (Recommended)**

1. **First, configure your domain DNS:**
   - Go to your domain registrar (GoDaddy, Namecheap, etc.)
   - Add an **A Record:**
     - **Type:** A
     - **Name:** @ (or leave blank, or `www`)
     - **Value:** Your static IP (e.g., `54.123.45.67`)
     - **TTL:** 3600 (or default)
   - Save the DNS record
   - **Wait 5-60 minutes** for DNS to propagate (check with: `nslookup yourdomain.com`)

2. **Update Nginx config with your domain:**
   ```bash
   sudo nano /etc/nginx/sites-available/studyqna
   ```
   
   Change the `server_name` line to:
   ```nginx
   server_name yourdomain.com www.yourdomain.com;
   ```
   
   Save and exit, then:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```
   
   **Follow the prompts:**
   - Enter your email address (for renewal notices)
   - Agree to terms (type `A` and press Enter)
   - Choose whether to redirect HTTP to HTTPS (recommended: type `2` and press Enter)
   
   **Success!** You should see:
   ```
   Congratulations! You have successfully enabled https://yourdomain.com
   ```

4. **Test auto-renewal:**
   ```bash
   sudo certbot renew --dry-run
   ```
   
   Should show: "The dry run was successful."

**Option B: If you don't have a domain (IP only)**

Unfortunately, Let's Encrypt doesn't issue certificates for IP addresses. You have two options:

1. **Use Cloudflare (Free SSL with IP):**
   - Sign up at [Cloudflare](https://www.cloudflare.com)
   - Add your site
   - Use Cloudflare's SSL (automatic)

2. **Purchase a domain** (recommended):
   - Domains cost ₹500-1,000/year
   - Makes your site look professional
   - Enables proper SSL

### Step 9.3: Verify SSL Certificate

1. **Check certificate status:**
   ```bash
   sudo certbot certificates
   ```

2. **Visit your site in a browser:**
   - Go to `https://yourdomain.com`
   - You should see a padlock icon in the address bar
   - Click the padlock to see certificate details

3. **Test HTTPS redirect:**
   - Visit `http://yourdomain.com` (HTTP)
   - It should automatically redirect to `https://yourdomain.com` (HTTPS)

### Step 9.4: Update Application URLs

If you got a domain and SSL, update your `.env` file:

```bash
cd ~/studyqna/backend
nano .env
```

Update these lines:
```env
APP_URL=https://yourdomain.com
CORS_ORIGINS_LIST=https://yourdomain.com,https://www.yourdomain.com
```

Save and exit, then restart the backend:
```bash
sudo systemctl restart studyqna-backend
```

---

## Part 10: Domain Configuration

### Step 10.1: Configure DNS Records

If you have a domain, configure DNS at your registrar:

1. **A Record (Main domain):**
   - **Type:** A
   - **Name:** @ (or blank)
   - **Value:** Your static IP
   - **TTL:** 3600

2. **A Record (www subdomain):**
   - **Type:** A
   - **Name:** www
   - **Value:** Your static IP
   - **TTL:** 3600

3. **Wait for DNS propagation:**
   - Check with: `nslookup yourdomain.com`
   - Or use: [https://dnschecker.org](https://dnschecker.org)

### Step 10.2: Update Nginx for Domain

If you haven't already, update Nginx config:

```bash
sudo nano /etc/nginx/sites-available/studyqna
```

Change `server_name` to:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Part 11: Final Testing

### Step 11.1: Test Frontend

1. **Open your browser**
2. **Visit:**
   - `http://YOUR_STATIC_IP` (if no domain)
   - `https://yourdomain.com` (if you have domain/SSL)

3. **You should see:**
   - The StudyQnA login/register page
   - No errors in the browser console (F12 → Console tab)

### Step 11.2: Test Backend API

1. **Visit API documentation:**
   - `http://YOUR_STATIC_IP/api/docs`
   - `https://yourdomain.com/api/docs`

2. **You should see:**
   - Swagger/OpenAPI documentation
   - All API endpoints listed

3. **Test health endpoint:**
   - Visit: `/api/health` or `/health`
   - Should return: `{"status":"healthy"}`

### Step 11.3: Test Application Features

1. **Create an account:**
   - Click "Register"
   - Enter email and password
   - Check your email for OTP (if email is configured)

2. **Login:**
   - Use your credentials
   - Should redirect to dashboard

3. **Test file upload:**
   - Upload a PDF or image
   - Should see success message

4. **Test Q&A generation:**
   - Select an uploaded file
   - Generate questions
   - Should see generated Q&A

5. **Test downloads:**
   - Download as PDF/DOCX/TXT
   - Files should download correctly

### Step 11.4: Check Logs

```bash
# Backend logs
sudo journalctl -u studyqna-backend -n 50

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

Press `Ctrl + C` to stop viewing logs.

---

## Part 12: Maintenance & Monitoring

### Step 12.1: Setup Automatic Backups

```bash
# Create backup script
nano ~/backup-database.sh
```

**Add this script:**

```bash
#!/bin/bash
BACKUP_DIR="/home/studyqna/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U studyqna_user studyqna > $BACKUP_DIR/db_$DATE.sql

# Backup storage (optional, can be large)
# tar -czf $BACKUP_DIR/storage_$DATE.tar.gz ~/studyqna/backend/storage

# Delete backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Make executable and schedule:**
```bash
chmod +x ~/backup-database.sh

# Test backup
~/backup-database.sh

# Schedule daily backup at 2 AM
crontab -e
```

Add this line:
```
0 2 * * * /home/studyqna/backup-database.sh
```

Save and exit.

### Step 12.2: Monitor Disk Space

```bash
# Check disk usage
df -h

# Check storage directory size
du -sh ~/studyqna/backend/storage

# Find large files
du -sh ~/studyqna/backend/storage/* | sort -h
```

### Step 12.3: Monitor Application Status

```bash
# Check all services
sudo systemctl status studyqna-backend
sudo systemctl status nginx
sudo systemctl status postgresql

# Check resource usage
htop
# Press q to exit
```

### Step 12.4: Update Application

When you need to update the code:

```bash
# Navigate to project
cd ~/studyqna

# Pull latest changes (if using Git)
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart studyqna-backend

# Update frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

---

## Troubleshooting

### Problem: Can't connect via SSH

**Solutions:**
1. Check your static IP is correct
2. Verify firewall allows port 22: `sudo ufw status`
3. Check Lightsail instance is running
4. Verify SSH key permissions: `chmod 400 lightsail-key.pem`

### Problem: Backend service not starting

**Check logs:**
```bash
sudo journalctl -u studyqna-backend -n 50
```

**Common issues:**
1. **Database connection error:**
   - Check `DATABASE_URL` in `.env`
   - Verify database is running: `sudo systemctl status postgresql`
   - Test connection: `psql -U studyqna_user -d studyqna`

2. **Port already in use:**
   - Check: `sudo lsof -i :8000`
   - Kill process if needed: `sudo kill -9 <PID>`

3. **Missing dependencies:**
   - Reinstall: `pip install -r requirements.txt`

### Problem: Frontend not loading

**Check Nginx:**
```bash
sudo systemctl status nginx
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**Common issues:**
1. **Build not found:**
   - Rebuild: `cd ~/studyqna/frontend && npm run build`

2. **Permission issues:**
   - Fix: `sudo chown -R studyqna:studyqna ~/studyqna/frontend/dist`

3. **Nginx config error:**
   - Check: `sudo nginx -t`
   - Fix syntax errors in config

### Problem: SSL certificate not working

**Check certificate:**
```bash
sudo certbot certificates
```

**Common issues:**
1. **DNS not propagated:**
   - Wait longer (up to 48 hours)
   - Check: `nslookup yourdomain.com`

2. **Port 80 blocked:**
   - Verify: `sudo ufw allow 80/tcp`
   - Check Lightsail firewall rules

3. **Certificate expired:**
   - Renew: `sudo certbot renew`

### Problem: Database connection error

**Test connection:**
```bash
psql -U studyqna_user -d studyqna -h localhost
```

**Common issues:**
1. **Wrong password:**
   - Reset: `sudo -u postgres psql` → `ALTER USER studyqna_user WITH PASSWORD 'newpassword';`

2. **Database not running:**
   - Start: `sudo systemctl start postgresql`

3. **Wrong DATABASE_URL:**
   - Check `.env` file format

### Problem: High memory usage

**Check memory:**
```bash
free -h
htop
```

**Solutions:**
1. Reduce backend workers in systemd service (change `--workers 2` to `--workers 1`)
2. Add more swap: Increase swap file size
3. Upgrade Lightsail instance plan

### Problem: Application is slow

**Check resources:**
```bash
htop
df -h
```

**Solutions:**
1. Upgrade Lightsail instance (more RAM/CPU)
2. Optimize database queries
3. Enable Nginx caching
4. Reduce backend workers if memory is low

---

## Quick Reference Commands

### Service Management

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
sudo systemctl status postgresql
```

### Logs

```bash
# Backend logs
sudo journalctl -u studyqna-backend -f
sudo journalctl -u studyqna-backend -n 100

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -xe
```

### Database

```bash
# Connect to database
psql -U studyqna_user -d studyqna -h localhost

# Backup database
pg_dump -U studyqna_user studyqna > backup_$(date +%Y%m%d).sql

# Restore database
psql -U studyqna_user studyqna < backup_20240101.sql

# List databases
sudo -u postgres psql -l
```

### SSL Certificate

```bash
# Check certificates
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### System Information

```bash
# Disk usage
df -h

# Memory usage
free -h

# CPU and processes
htop

# Network connections
sudo netstat -tulpn
```

---

## 🎉 Congratulations!

Your StudyQnA Assistant application is now deployed and running on AWS Lightsail!

### Your Application URLs:
- **Frontend:** `https://yourdomain.com` (or `http://YOUR_STATIC_IP`)
- **Backend API:** `https://yourdomain.com/api`
- **API Documentation:** `https://yourdomain.com/api/docs`

### Next Steps:
1. ✅ Test all features (upload, generate, download)
2. ✅ Create your admin account (use the email in `ADMIN_EMAIL`)
3. ✅ Set up monitoring alerts
4. ✅ Schedule regular backups
5. ✅ Share your application with users!

### Support Resources:
- **AWS Lightsail Docs:** [https://lightsail.aws.amazon.com/ls/docs/](https://lightsail.aws.amazon.com/ls/docs/)
- **Nginx Docs:** [https://nginx.org/en/docs/](https://nginx.org/en/docs/)
- **Let's Encrypt Docs:** [https://letsencrypt.org/docs/](https://letsencrypt.org/docs/)

---

**Need Help?** Check the troubleshooting section above or review the logs for error messages.

**Last Updated:** January 2025  
**Version:** 1.0


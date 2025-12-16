# 🚀 AWS Lightsail Quick Start Deployment Guide

## Prerequisites Checklist

Before starting, make sure you have:
- [ ] AWS Account (create at https://aws.amazon.com)
- [ ] Domain name (optional but recommended)
- [ ] OpenAI API key
- [ ] Brevo API key (for emails) OR Gmail App Password
- [ ] SSH client (Windows: PuTTY, Mac/Linux: Terminal)

---

## Step 1: Create Lightsail Instance (5 minutes)

### 1.1 Login to AWS Lightsail
1. Go to https://lightsail.aws.amazon.com
2. Sign in with your AWS account

### 1.2 Create Instance
1. Click **"Create instance"**
2. Choose:
   - **Platform**: Linux/Unix
   - **Blueprint**: Ubuntu 22.04 LTS
   - **Instance plan**: 
     - **$10/month** (1GB RAM, 1 vCPU) - Recommended for production
     - **$20/month** (2GB RAM, 1 vCPU) - Better performance
3. **Instance name**: `studyqna-server`
4. Click **"Create instance"**
5. Wait 2-3 minutes for instance to start

### 1.3 Create Static IP
1. Click **"Networking"** in left sidebar
2. Click **"Create static IP"**
3. Attach to: `studyqna-server`
4. Name: `studyqna-static-ip`
5. Click **"Create"**
6. **Copy the static IP address** (you'll need it later)

### 1.4 Download SSH Key
1. Click on your instance
2. Go to **"Account"** tab
3. Click **"Download default key"**
4. Save the `.pem` file securely

---

## Step 2: Connect to Server (2 minutes)

### Windows (PuTTY):
1. Download PuTTY: https://www.putty.org/
2. Download PuTTYgen: https://www.putty.org/
3. Convert `.pem` to `.ppk`:
   - Open PuTTYgen
   - Click "Load" → Select your `.pem` file
   - Click "Save private key" → Save as `.ppk`
4. Connect:
   - Open PuTTY
   - Host: `ubuntu@YOUR_STATIC_IP`
   - Connection → SSH → Auth → Browse → Select `.ppk` file
   - Click "Open"

### Mac/Linux:
```bash
chmod 400 /path/to/your-key.pem
ssh -i /path/to/your-key.pem ubuntu@YOUR_STATIC_IP
```

### Windows (WSL/Git Bash):
```bash
chmod 400 /path/to/your-key.pem
ssh -i /path/to/your-key.pem ubuntu@YOUR_STATIC_IP
```

---

## Step 3: Initial Server Setup (10 minutes)

Once connected, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv postgresql postgresql-contrib -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install system dependencies for image processing
sudo apt install tesseract-ocr libtesseract-dev poppler-utils -y

# Install Nginx
sudo apt install nginx -y

# Install Certbot (for SSL)
sudo apt install certbot python3-certbot-nginx -y

# Create application directory
sudo mkdir -p /home/ubuntu/studyqna
sudo chown ubuntu:ubuntu /home/ubuntu/studyqna
cd /home/ubuntu/studyqna
```

---

## Step 4: Database Setup (5 minutes)

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell, run:
CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD 'YOUR_SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;
\q

# Test connection
psql -U studyqna_user -d studyqna -h localhost
# Enter password when prompted
# Type \q to exit
```

**⚠️ Important:** Replace `YOUR_SECURE_PASSWORD_HERE` with a strong password!

---

## Step 5: Upload Your Code (5 minutes)

### Option A: Using Git (Recommended)
```bash
cd /home/ubuntu/studyqna

# If your code is in a Git repository:
git clone https://github.com/yourusername/studyqna.git .

# OR if using SSH:
git clone git@github.com:yourusername/studyqna.git .
```

### Option B: Using SCP (File Transfer)
```bash
# From your local machine (Windows/Mac/Linux):
# Navigate to your project directory, then:

# Windows (PowerShell):
scp -i C:\path\to\your-key.pem -r * ubuntu@YOUR_STATIC_IP:/home/ubuntu/studyqna/

# Mac/Linux:
scp -i /path/to/your-key.pem -r * ubuntu@YOUR_STATIC_IP:/home/ubuntu/studyqna/
```

### Option C: Using WinSCP (Windows GUI)
1. Download WinSCP: https://winscp.net/
2. Connect using your `.ppk` file
3. Upload your project files

---

## Step 6: Backend Setup (10 minutes)

```bash
cd /home/ubuntu/studyqna/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create storage directory
mkdir -p storage/uploads
chmod 700 storage

# Create .env file
nano .env
```

### Add this to .env file:

```env
# Database
DATABASE_URL=postgresql://studyqna_user:YOUR_PASSWORD@localhost:5432/studyqna

# JWT Secret (generate a strong key)
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE

# Admin
ADMIN_EMAIL=your-admin-email@example.com

# Storage
STORAGE_PATH=/home/ubuntu/studyqna/backend/storage
ENCRYPT_STORAGE=true

# Email - Brevo (Recommended)
BREVO_API_KEY=your-brevo-api-key
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=StudyQnA
EMAIL_PROVIDER=brevo

# OR Email - SMTP (Alternative)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-gmail-app-password
# SMTP_FROM=StudyQnA <noreply@yourdomain.com>
# EMAIL_PROVIDER=smtp

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# App URL (Update with your domain or static IP)
APP_URL=http://YOUR_STATIC_IP
# OR if you have domain:
# APP_URL=https://yourdomain.com
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output and paste it as `SECRET_KEY` in `.env`

**Save .env file:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

### Initialize Database:
```bash
# Make sure you're in venv
source venv/bin/activate

# Initialize database tables
python init_db.py

# Run any migrations if needed
python run_migration.py
```

### Test Backend:
```bash
# Start server (for testing)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test in another terminal or browser:
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Press Ctrl+C to stop
```

---

## Step 7: Frontend Setup (10 minutes)

```bash
cd /home/ubuntu/studyqna/frontend

# Install dependencies
npm install

# Update API URL (if needed)
# Edit src/utils/api.js and change baseURL to your backend URL

# Build for production
npm run build

# The build output will be in: frontend/dist/
```

---

## Step 8: Configure Nginx (10 minutes)

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/studyqna
```

### Add this configuration:

```nginx
server {
    listen 80;
    server_name YOUR_STATIC_IP_OR_DOMAIN;

    # Frontend
    location / {
        root /home/ubuntu/studyqna/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

**Save and exit:**
- Press `Ctrl+X`, then `Y`, then `Enter`

### Enable site:
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/studyqna /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 9: Create Systemd Service (5 minutes)

```bash
# Create service file
sudo nano /etc/systemd/system/studyqna-backend.service
```

### Add this configuration:

```ini
[Unit]
Description=StudyQnA Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/studyqna/backend
Environment="PATH=/home/ubuntu/studyqna/backend/venv/bin"
ExecStart=/home/ubuntu/studyqna/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save and exit:**
- Press `Ctrl+X`, then `Y`, then `Enter`

### Enable and start service:
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

## Step 10: Configure Firewall (2 minutes)

```bash
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

---

## Step 11: SSL Certificate (If you have a domain) (5 minutes)

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)

# Test auto-renewal
sudo certbot renew --dry-run
```

**If you don't have a domain:**
- You can use the static IP, but SSL won't work
- Consider using Cloudflare for free SSL with IP

---

## Step 12: Update CORS Configuration (2 minutes)

```bash
cd /home/ubuntu/studyqna/backend
source venv/bin/activate
nano app/config.py
```

**Find this line:**
```python
CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
```

**Replace with:**
```python
CORS_ORIGINS: List[str] = [
    "http://YOUR_STATIC_IP",
    "https://yourdomain.com",  # If you have domain
    "https://www.yourdomain.com"  # If you have domain
]
```

**Save and restart backend:**
```bash
sudo systemctl restart studyqna-backend
```

---

## Step 13: Test Your Deployment (5 minutes)

1. **Open browser and go to:**
   - `http://YOUR_STATIC_IP` (or `https://yourdomain.com` if you have SSL)

2. **Test features:**
   - [ ] Can see the login page
   - [ ] Can register/login
   - [ ] Can upload files
   - [ ] Can generate Q&A
   - [ ] Can download files

3. **Check backend logs:**
   ```bash
   sudo journalctl -u studyqna-backend -f
   ```

4. **Check Nginx logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

---

## 🎉 Deployment Complete!

Your application should now be live at:
- **Frontend**: `http://YOUR_STATIC_IP` (or `https://yourdomain.com`)
- **Backend API**: `http://YOUR_STATIC_IP/api` (or `https://yourdomain.com/api`)
- **API Docs**: `http://YOUR_STATIC_IP/api/docs` (or `https://yourdomain.com/api/docs`)

---

## 🔧 Useful Commands

### Backend Service:
```bash
# Start
sudo systemctl start studyqna-backend

# Stop
sudo systemctl stop studyqna-backend

# Restart
sudo systemctl restart studyqna-backend

# View logs
sudo journalctl -u studyqna-backend -f

# Check status
sudo systemctl status studyqna-backend
```

### Nginx:
```bash
# Restart
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# View logs
sudo tail -f /var/log/nginx/error.log
```

### Database:
```bash
# Connect to database
psql -U studyqna_user -d studyqna -h localhost

# Backup database
pg_dump -U studyqna_user studyqna > backup_$(date +%Y%m%d).sql

# Restore database
psql -U studyqna_user studyqna < backup_20240101.sql
```

---

## 🐛 Troubleshooting

### Backend not starting:
```bash
# Check logs
sudo journalctl -u studyqna-backend -n 50

# Common issues:
# 1. Database connection error → Check DATABASE_URL in .env
# 2. Port already in use → Check if another process is using port 8000
# 3. Missing dependencies → Run: pip install -r requirements.txt
```

### Frontend not loading:
```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify build exists
ls -la /home/ubuntu/studyqna/frontend/dist

# Rebuild if needed
cd /home/ubuntu/studyqna/frontend
npm run build
```

### Database connection error:
```bash
# Test connection
psql -U studyqna_user -d studyqna -h localhost

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check .env file
cat /home/ubuntu/studyqna/backend/.env | grep DATABASE_URL
```

---

## 📝 Next Steps

1. **Set up automated backups** (see LIGHTSAIL_DEPLOYMENT.md)
2. **Configure monitoring** (optional)
3. **Add rate limiting** (recommended)
4. **Set up domain DNS** (if you have a domain)
5. **Configure email service** (Brevo or SMTP)

---

## 📚 Additional Resources

- Full deployment guide: `LIGHTSAIL_DEPLOYMENT.md`
- Production checklist: `PRODUCTION_READINESS_CHECKLIST.md`
- Environment template: `backend/ENV_TEMPLATE.txt`

---

**Need help?** Check the logs first, then refer to the troubleshooting section above.


# Deployment Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 12+
- Lightsail instance (or similar server)

## Server Setup (Lightsail)

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv postgresql postgresql-contrib -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install system dependencies for image processing
sudo apt install tesseract-ocr libtesseract-dev poppler-utils -y
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;
\q
```

### 3. Backend Deployment

```bash
# Clone or upload project
cd /home/ubuntu/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
nano .env  # Edit with your settings

# Create storage directory
sudo mkdir -p /home/ubuntu/app/storage/uploads
sudo chmod 700 /home/ubuntu/app/storage
sudo chown -R ubuntu:ubuntu /home/ubuntu/app/storage

# Initialize database
python init_db.py

# Test server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Frontend Deployment

```bash
cd /home/ubuntu/app/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or use a process manager
```

### 5. Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        root /home/ubuntu/app/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Process Management (PM2)

```bash
# Install PM2
npm install -g pm2

# Start backend
cd /home/ubuntu/app/backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name studyqna-api

# Save PM2 configuration
pm2 save
pm2 startup
```

### 7. Security Hardening

```bash
# Set up firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Secure storage directory
sudo chmod 700 /home/ubuntu/app/storage
sudo chown -R ubuntu:ubuntu /home/ubuntu/app/storage

# Set secure file permissions
find /home/ubuntu/app/storage -type f -exec chmod 600 {} \;
find /home/ubuntu/app/storage -type d -exec chmod 700 {} \;
```

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://studyqna_user:password@localhost:5432/studyqna
SECRET_KEY=your-very-secure-secret-key-here
ADMIN_EMAIL=admin@yourdomain.com
STORAGE_PATH=/home/ubuntu/app/storage
ENCRYPT_STORAGE=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=StudyQnA <noreply@yourdomain.com>
OPENAI_API_KEY=your-openai-api-key
APP_URL=https://your-domain.com
```

## SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring

- Set up log rotation
- Monitor disk space for storage directory
- Set up database backups
- Monitor API usage and quotas

## Backup Strategy

```bash
# Database backup script
#!/bin/bash
pg_dump -U studyqna_user studyqna > backup_$(date +%Y%m%d).sql

# Storage backup
tar -czf storage_backup_$(date +%Y%m%d).tar.gz /home/ubuntu/app/storage
```



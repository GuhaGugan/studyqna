# 🚀 Deployment Checklist - AWS Lightsail

Use this checklist to track your deployment progress.

## Pre-Deployment

- [ ] AWS Account created
- [ ] Domain name purchased (optional)
- [ ] OpenAI API key ready
- [ ] Brevo API key ready (or Gmail App Password)
- [ ] SSH client installed (PuTTY for Windows, Terminal for Mac/Linux)

## Step 1: AWS Lightsail Setup

- [ ] Lightsail instance created ($10/month recommended)
- [ ] Static IP created and attached
- [ ] Static IP address copied
- [ ] SSH key downloaded (.pem file)

## Step 2: Server Connection

- [ ] Successfully connected to server via SSH
- [ ] Can run commands on server

## Step 3: Initial Server Setup

- [ ] System updated (`sudo apt update && sudo apt upgrade`)
- [ ] Python 3 installed
- [ ] PostgreSQL installed
- [ ] Node.js 18 installed
- [ ] Tesseract OCR installed
- [ ] Poppler utils installed
- [ ] Nginx installed
- [ ] Certbot installed
- [ ] Application directory created (`/home/ubuntu/studyqna`)

## Step 4: Database Setup

- [ ] PostgreSQL database created (`studyqna`)
- [ ] Database user created (`studyqna_user`)
- [ ] Database password set (strong password)
- [ ] Permissions granted
- [ ] Database connection tested

## Step 5: Code Upload

- [ ] Code uploaded to server (Git/SCP/WinSCP)
- [ ] Files verified in `/home/ubuntu/studyqna/`

## Step 6: Backend Setup

- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Storage directory created
- [ ] `.env` file created with all required variables:
  - [ ] DATABASE_URL
  - [ ] SECRET_KEY (strong, generated)
  - [ ] ADMIN_EMAIL
  - [ ] STORAGE_PATH
  - [ ] BREVO_API_KEY (or SMTP credentials)
  - [ ] OPENAI_API_KEY
  - [ ] APP_URL
- [ ] Database initialized (`python init_db.py`)
- [ ] Migrations run (if any)
- [ ] Backend tested locally (`uvicorn app.main:app --host 0.0.0.0 --port 8000`)

## Step 7: Frontend Setup

- [ ] Dependencies installed (`npm install`)
- [ ] API URL updated in frontend (if needed)
- [ ] Production build created (`npm run build`)
- [ ] Build output verified in `frontend/dist/`

## Step 8: Nginx Configuration

- [ ] Nginx config file created (`/etc/nginx/sites-available/studyqna`)
- [ ] Frontend location configured
- [ ] Backend API proxy configured
- [ ] Site enabled (symlink created)
- [ ] Default site removed
- [ ] Nginx config tested (`sudo nginx -t`)
- [ ] Nginx restarted

## Step 9: Systemd Service

- [ ] Service file created (`/etc/systemd/system/studyqna-backend.service`)
- [ ] Service enabled (starts on boot)
- [ ] Service started
- [ ] Service status checked (running)
- [ ] Logs verified (no errors)

## Step 10: Firewall

- [ ] SSH port allowed (22)
- [ ] HTTP port allowed (80)
- [ ] HTTPS port allowed (443)
- [ ] Firewall enabled
- [ ] Firewall status verified

## Step 11: SSL Certificate (If you have domain)

- [ ] Domain DNS configured (points to static IP)
- [ ] SSL certificate obtained (Certbot)
- [ ] HTTPS redirect configured
- [ ] Auto-renewal tested

## Step 12: CORS Configuration

- [ ] CORS_ORIGINS updated in `.env` or `config.py`
- [ ] Backend restarted after CORS change

## Step 13: Testing

- [ ] Frontend loads in browser
- [ ] Can access login/register page
- [ ] Can create account
- [ ] Can login
- [ ] Can upload files
- [ ] Can generate Q&A
- [ ] Can download files
- [ ] API endpoints working (`/api/docs`)
- [ ] Health check working (`/health`)

## Post-Deployment

- [ ] Automated backups configured
- [ ] Monitoring set up (optional)
- [ ] Error logging verified
- [ ] Email notifications tested
- [ ] Admin account created and tested

## Security Checklist

- [ ] Strong SECRET_KEY set (not default)
- [ ] Database password is strong
- [ ] SSH key secured (not shared)
- [ ] Firewall configured
- [ ] SSL certificate installed (if using domain)
- [ ] CORS origins restricted to production domain
- [ ] Storage directory permissions set (700)
- [ ] `.env` file not committed to Git

## Performance Checklist

- [ ] Systemd service using multiple workers (--workers 2)
- [ ] Database connection pooling configured
- [ ] Nginx caching configured (optional)
- [ ] Static files served efficiently

## Documentation

- [ ] Deployment steps documented
- [ ] Environment variables documented
- [ ] Backup procedures documented
- [ ] Troubleshooting guide reviewed

---

## 🎯 Quick Status Check

Run these commands to verify everything is working:

```bash
# Check backend service
sudo systemctl status studyqna-backend

# Check Nginx
sudo systemctl status nginx

# Check database
sudo systemctl status postgresql

# Check disk space
df -h

# Check memory
free -h

# View backend logs
sudo journalctl -u studyqna-backend -n 50

# Test API
curl http://localhost:8000/health
```

---

## ✅ Deployment Complete When:

1. ✅ Frontend accessible via browser
2. ✅ Can login and use all features
3. ✅ Backend service running and auto-restarting
4. ✅ Database connected and working
5. ✅ SSL certificate installed (if using domain)
6. ✅ All tests passing

---

**Estimated Total Time:** 1-2 hours for first deployment

**Need Help?** Refer to:
- `LIGHTSAIL_QUICK_START.md` - Step-by-step guide
- `LIGHTSAIL_DEPLOYMENT.md` - Detailed guide
- `PRODUCTION_READINESS_CHECKLIST.md` - Production features


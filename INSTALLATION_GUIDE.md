# StudyQnA Generator - Complete Installation Guide

This guide will walk you through installing and setting up the StudyQnA Generator application from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend Installation](#backend-installation)
4. [Frontend Installation](#frontend-installation)
5. [Environment Configuration](#environment-configuration)
6. [Running the Application](#running-the-application)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software

1. **Python 3.9 or higher**
   ```bash
   python --version  # Should show 3.9+
   ```

2. **Node.js 18 or higher**
   ```bash
   node --version  # Should show v18+
   npm --version
   ```

3. **PostgreSQL 12 or higher**
   ```bash
   psql --version
   ```

4. **Git** (optional, for cloning)

### System Dependencies (Linux/Mac)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib
sudo apt install -y tesseract-ocr libtesseract-dev poppler-utils
sudo apt install -y build-essential python3-dev

# macOS (using Homebrew)
brew install postgresql
brew install tesseract
brew install poppler
```

### System Dependencies (Windows)

1. Install PostgreSQL from: https://www.postgresql.org/download/windows/
2. Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
3. Add Tesseract to PATH: `C:\Program Files\Tesseract-OCR`
4. Install Poppler from: https://github.com/oschwartz10612/poppler-windows/releases

---

## Database Setup

### Step 1: Install PostgreSQL

**Windows:**
- Download and install from https://www.postgresql.org/download/windows/
- Remember the password you set for the `postgres` user

**Linux:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### Step 2: Create Database and User

#### Option A: Using pgAdmin (Windows - Recommended)

1. **Open pgAdmin**
   - Launch pgAdmin from Start Menu
   - Enter your master password (set during PostgreSQL installation)

2. **Connect to PostgreSQL Server**
   - In the left panel, expand "Servers"
   - Click on "PostgreSQL [version]" (e.g., "PostgreSQL 15")
   - Enter the postgres user password if prompted
   - Right-click on "PostgreSQL [version]" → "Connect Server"

3. **Create Database**
   - Right-click on "Databases" → "Create" → "Database..."
   - In the "Database" tab:
     - **Database name**: `studyqna`
     - **Owner**: Leave as default (postgres) or select postgres
   - Click "Save"

4. **Create User**
   - Expand "Login/Group Roles" in the left panel
   - Right-click → "Create" → "Login/Group Role..."
   - In the "General" tab:
     - **Name**: `studyqna_user`
   - In the "Definition" tab:
     - **Password**: Enter a strong password (remember this!)
     - **Password expiration**: Leave unchecked
   - In the "Privileges" tab:
     - Enable: "Can login?"
   - Click "Save"

5. **Grant Privileges**
   - Right-click on the `studyqna` database → "Properties"
   - Go to "Security" tab
   - Click "Add" button
   - Select `studyqna_user` from dropdown
   - Check "ALL" privileges
   - Click "Save"

6. **Grant Schema Privileges (Important!)**
   - Expand `studyqna` database → "Schemas" → "public"
   - Right-click on "public" → "Properties"
   - Go to "Security" tab
   - Click "Add" button
   - Select `studyqna_user`
   - Check "ALL" privileges
   - Click "Save"

#### Option B: Using SQL Shell (psql) - Alternative Method

Open PostgreSQL command line:

**Windows:**
- Open "SQL Shell (psql)" from Start Menu
- Press Enter 4 times (accept defaults: Server, Database, Port, Username)
- Enter postgres user password when prompted

**Linux/Mac:**
```bash
sudo -u postgres psql
```

Then run these SQL commands:

```sql
-- Create database
CREATE DATABASE studyqna;

-- Create user (replace 'your_password' with a strong password)
CREATE USER studyqna_user WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;

-- Connect to the database
\c studyqna

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO studyqna_user;

-- Exit
\q
```

### Step 3: Verify Database Connection

**Using pgAdmin (Windows):**
1. Right-click on "studyqna" database → "Query Tool"
2. Type: `SELECT current_database();`
3. Click Execute (▶️) or press F5
4. Should show: `studyqna`

**Using Command Line:**
```bash
psql -U studyqna_user -d studyqna -h localhost
# Enter password when prompted
# Type \q to exit
```

**Note:** For detailed pgAdmin setup instructions, see `WINDOWS_PGADMIN_SETUP.md`

---

## Backend Installation

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Upgrade Pip

```bash
pip install --upgrade pip
```

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI and related packages
- Database drivers (psycopg2)
- OCR libraries (pytesseract, Pillow)
- AI libraries (openai, ultralytics for human detection)
- File processing (PyPDF2, python-docx)
- And other dependencies

**Note:** If you encounter errors:

- **Windows**: You may need Microsoft Visual C++ Build Tools
- **psycopg2 errors**: Install PostgreSQL development libraries
- **Tesseract errors**: Ensure Tesseract is installed and in PATH

### Step 5: Create Storage Directory

```bash
# From project root
mkdir -p storage/uploads
```

**Linux/Mac:**
```bash
chmod 700 storage
```

**Windows:**
- Right-click storage folder → Properties → Security → Remove all users except your account

### Step 6: Initialize Database Tables

```bash
# Make sure virtual environment is activated
python init_db.py
```

This creates all necessary database tables.

---

## Frontend Installation

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Node Dependencies

```bash
npm install
```

This installs:
- React and React DOM
- React Router
- Axios for API calls
- Tailwind CSS
- Vite build tool
- And other dependencies

### Step 3: Verify Installation

```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

Press `Ctrl+C` to stop the server.

---

## Environment Configuration

### Backend .env File

1. **Copy the example file:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit the .env file** with your configuration:

```env
# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL=postgresql://studyqna_user:your_secure_password_here@localhost:5432/studyqna

# ============================================
# JWT SECURITY
# ============================================
# Generate a strong secret key (use: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# ADMIN CONFIGURATION
# ============================================
# Email address that will have admin access
ADMIN_EMAIL=admin@example.com

# ============================================
# STORAGE CONFIGURATION
# ============================================
# Path to storage directory (absolute or relative)
STORAGE_PATH=./storage
ENCRYPT_STORAGE=true

# ============================================
# EMAIL CONFIGURATION (SMTP)
# ============================================
# For Gmail, use App Password (not regular password)
# Enable 2FA, then generate App Password: https://myaccount.google.com/apppasswords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM=StudyQnA <noreply@studyqna.com>

# ============================================
# OPENAI CONFIGURATION
# ============================================
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# ============================================
# APPLICATION CONFIGURATION
# ============================================
APP_NAME=StudyQnA Generator
APP_URL=http://localhost:3000

# Note: CORS_ORIGINS is configured in config.py, not in .env
# To modify, edit backend/app/config.py
```

### Generate Secret Key

To generate a secure JWT secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as `SECRET_KEY` in your `.env` file.

### Email Setup (Gmail Example)

1. Enable 2-Factor Authentication on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"
4. Use this App Password (not your regular password) as `SMTP_PASSWORD`

### OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Create a new API key
3. Copy and paste it as `OPENAI_API_KEY` in your `.env` file

---

## Running the Application

### Step 1: Start Backend Server

**Terminal 1:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python run.py
```

Or:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 2: Start Frontend Server

**Terminal 2:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:3000/
```

### Step 3: Access the Application

1. Open browser: http://localhost:3000
2. You should see the login page
3. Enter your admin email (as configured in `ADMIN_EMAIL`)
4. Click "Send OTP"
5. Check your email for the OTP
6. Enter OTP and login

---

## Verification Checklist

After installation, verify:

- [ ] Backend server starts without errors
- [ ] Frontend server starts without errors
- [ ] Database connection works (check backend logs)
- [ ] Can access http://localhost:3000
- [ ] Can receive OTP emails
- [ ] Can login with admin email
- [ ] Storage directory exists and has correct permissions
- [ ] OpenAI API key is valid (test by generating Q/A)

---

## Troubleshooting

### Backend Issues

**Problem: Database connection error**
```
Solution:
1. Check PostgreSQL is running: sudo systemctl status postgresql
2. Verify DATABASE_URL in .env matches your setup
3. Test connection: psql -U studyqna_user -d studyqna
4. Check firewall settings
```

**Problem: Module not found errors**
```
Solution:
1. Ensure virtual environment is activated
2. Reinstall: pip install -r requirements.txt
3. Check Python version: python --version (need 3.9+)
```

**Problem: Tesseract OCR not found**
```
Solution:
1. Install Tesseract: sudo apt install tesseract-ocr
2. Add to PATH (Windows)
3. Verify: tesseract --version
```

**Problem: Human detection model download fails**
```
Solution:
1. Check internet connection
2. Model downloads automatically on first use
3. Manual download: python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Frontend Issues

**Problem: npm install fails**
```
Solution:
1. Clear cache: npm cache clean --force
2. Delete node_modules and package-lock.json
3. Reinstall: npm install
4. Check Node version: node --version (need 18+)
```

**Problem: Cannot connect to backend API**
```
Solution:
1. Check backend is running on port 8000
2. Verify proxy in vite.config.js
3. Check CORS_ORIGINS in backend .env
4. Test API directly: http://localhost:8000/health
```

**Problem: Build errors**
```
Solution:
1. Update dependencies: npm update
2. Clear build cache: rm -rf dist node_modules/.vite
3. Rebuild: npm run build
```

### Database Issues

**Problem: Permission denied errors**
```
Solution:
1. Grant privileges: GRANT ALL ON SCHEMA public TO studyqna_user;
2. Check user exists: \du in psql
3. Verify database ownership
```

**Problem: Tables not created**
```
Solution:
1. Run: python backend/init_db.py
2. Check database connection
3. Verify user has CREATE privileges
```

### Email Issues

**Problem: OTP emails not sending**
```
Solution:
1. Check SMTP credentials
2. For Gmail, use App Password (not regular password)
3. Check firewall/network settings
4. Test SMTP connection manually
5. Check spam folder
```

### Storage Issues

**Problem: File upload fails**
```
Solution:
1. Check storage directory exists
2. Verify permissions: chmod 700 storage
3. Check disk space: df -h
4. Verify STORAGE_PATH in .env
```

---

## Production Deployment

For production deployment, see `DEPLOYMENT.md` for:
- Nginx configuration
- SSL certificate setup
- Process management (PM2)
- Security hardening
- Backup strategies

---

## Quick Start Commands Summary

```bash
# 1. Database
sudo -u postgres psql
CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env file
python init_db.py
python run.py

# 3. Frontend
cd frontend
npm install
npm run dev

# 4. Access
# Open http://localhost:3000
```

---

## Need Help?

If you encounter issues:
1. Check the error messages carefully
2. Verify all prerequisites are installed
3. Check the Troubleshooting section above
4. Review the logs in terminal output
5. Ensure all environment variables are set correctly

---

## Next Steps

After successful installation:
1. Login with admin email
2. Test file upload
3. Generate sample Q/A
4. Review admin dashboard
5. Configure production settings (see DEPLOYMENT.md)


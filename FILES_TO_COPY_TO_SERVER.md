# 📦 Files to Copy to Lightsail Server

This document lists **exactly** which files and directories need to be copied to your Lightsail server.

---

## ✅ **MUST COPY - Backend Files**

### **Backend Root Directory:**
```
backend/
├── alembic/                    # Database migrations
│   ├── env.py
│   └── script.py.mako
├── alembic.ini                 # Alembic configuration
├── app/                        # Main application code
│   ├── __init__.py
│   ├── ai_service.py
│   ├── config.py
│   ├── content_validation.py
│   ├── database.py
│   ├── download_service.py
│   ├── email_service.py
│   ├── email_validation.py
│   ├── error_logger.py
│   ├── font_manager.py
│   ├── fonts/                  # Font files (IMPORTANT!)
│   │   ├── NotoSans-Regular.ttf
│   │   ├── NotoSansArabic-Regular.ttf
│   │   ├── NotoSansDevanagari-Regular.ttf
│   │   ├── NotoSansKannada-Regular.ttf
│   │   ├── NotoSansMalayalam-Regular.ttf
│   │   ├── NotoSansTamil-Regular.ttf
│   │   └── NotoSansTelugu-Regular.ttf
│   ├── generation_tracker.py
│   ├── human_detection.py
│   ├── main.py
│   ├── models.py
│   ├── ocr_service.py
│   ├── pdf_split_service.py
│   ├── post_process_math.py
│   ├── routers/                # API routes
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── ai_usage.py
│   │   ├── auth.py
│   │   ├── dependencies.py
│   │   ├── qna.py
│   │   ├── reviews.py
│   │   ├── upload.py
│   │   └── user.py
│   ├── schemas.py
│   ├── security.py
│   ├── storage_service.py
│   └── subject_prompts.py
├── migrations/                 # Database migration scripts
│   ├── add_cascade_delete.py
│   ├── add_pdf_split_parts.py
│   ├── add_subject_column_simple.py
│   ├── add_subject_column.py
│   └── add_subject_column.sql
├── init_db.py                  # Database initialization
├── run_migration.py            # Migration runner
├── run.py                      # Alternative run script
├── requirements.txt            # Python dependencies (CRITICAL!)
├── ENV_TEMPLATE.txt            # Environment template
└── yolov8n.pt                  # YOLO model file (for human detection)
```

### **Backend Files to EXCLUDE (DO NOT COPY):**
```
backend/
├── venv/                       # ❌ Virtual environment (create on server)
├── storage/                    # ❌ User uploads (create on server)
├── logs/                       # ❌ Log files (created on server)
├── __pycache__/                # ❌ Python cache (auto-generated)
├── *.pyc                       # ❌ Compiled Python files
├── .env                        # ❌ Environment file (create on server from template)
├── *.bat                       # ❌ Windows batch files
├── *.docx                      # ❌ Documentation files
├── *.md                        # ❌ Markdown docs (optional)
├── test_*.py                   # ❌ Test files
├── check_*.py                  # ❌ Check scripts
├── download_fonts.py           # ❌ Font download script (fonts already included)
├── setup_env.py                # ❌ Setup script (not needed)
└── Dockerfile                  # ❌ Docker file (optional, not needed for manual deployment)
```

---

## ✅ **MUST COPY - Frontend Files**

### **Frontend Root Directory:**
```
frontend/
├── src/                        # Source code
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── components/
│   │   ├── FileUpload.jsx
│   │   ├── HelpTooltip.jsx
│   │   ├── OnboardingTour.jsx
│   │   ├── PdfSplitParts.jsx
│   │   ├── PremiumBanner.jsx
│   │   ├── PremiumWelcome.jsx
│   │   ├── ProfileTab.jsx
│   │   ├── ProtectedRoute.jsx
│   │   ├── QnAGenerator.jsx
│   │   ├── ReviewForm.jsx
│   │   └── SavedSets.jsx
│   ├── contexts/
│   │   └── AuthContext.jsx
│   ├── pages/
│   │   ├── AdminDashboard.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Login.jsx
│   │   └── Profile.jsx
│   └── utils/
│       ├── api.js
│       └── deviceDetection.js
├── index.html                  # HTML entry point
├── package.json                # Node dependencies (CRITICAL!)
├── package-lock.json           # Lock file (recommended)
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
└── postcss.config.js           # PostCSS configuration
```

### **Frontend Files to EXCLUDE (DO NOT COPY):**
```
frontend/
├── node_modules/               # ❌ Node modules (install on server)
├── dist/                       # ❌ Build output (build on server)
├── .env                        # ❌ Environment file (if exists)
├── *.local                     # ❌ Local config files
└── Dockerfile                  # ❌ Docker file (optional)
```

---

## 📋 **Complete Copy Command Examples**

### **Option 1: Using SCP (From Your Local Machine)**

#### **Windows (PowerShell):**
```powershell
# Navigate to project root directory first
cd "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant"

# Copy backend (excluding unnecessary files)
scp -i C:\path\to\your-key.pem -r `
  --exclude="venv" `
  --exclude="storage" `
  --exclude="logs" `
  --exclude="__pycache__" `
  --exclude="*.pyc" `
  --exclude="*.bat" `
  --exclude="*.docx" `
  --exclude="test_*.py" `
  --exclude="check_*.py" `
  --exclude=".env" `
  backend ubuntu@YOUR_STATIC_IP:/home/ubuntu/studyqna/

# Copy frontend (excluding node_modules and dist)
scp -i C:\path\to\your-key.pem -r `
  --exclude="node_modules" `
  --exclude="dist" `
  --exclude=".env" `
  frontend ubuntu@YOUR_STATIC_IP:/home/ubuntu/studyqna/
```

#### **Mac/Linux:**
```bash
# Navigate to project root directory
cd /path/to/StudyQnA\ Assistant

# Copy backend
rsync -avz --exclude='venv' \
  --exclude='storage' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.bat' \
  --exclude='*.docx' \
  --exclude='test_*.py' \
  --exclude='check_*.py' \
  --exclude='.env' \
  -e "ssh -i /path/to/your-key.pem" \
  backend/ ubuntu@YOUR_STATIC_IP:/home/ubuntu/studyqna/backend/

# Copy frontend
rsync -avz --exclude='node_modules' \
  --exclude='dist' \
  --exclude='.env' \
  -e "ssh -i /path/to/your-key.pem" \
  frontend/ ubuntu@YOUR_STATIC_IP:/home/ubuntu/studyqna/frontend/
```

### **Option 2: Using Git (Recommended - Cleanest Method)**

```bash
# On server, clone your repository
cd /home/ubuntu/studyqna
git clone https://github.com/yourusername/studyqna.git .

# Or if repository is private, use SSH:
git clone git@github.com:yourusername/studyqna.git .
```

**Then on server, create necessary directories:**
```bash
# Create storage directory
mkdir -p backend/storage/uploads
chmod 700 backend/storage

# Create logs directory
mkdir -p backend/logs

# Create virtual environment (will be created during setup)
# Create .env file (from ENV_TEMPLATE.txt)
```

### **Option 3: Using WinSCP (Windows GUI)**

1. Download WinSCP: https://winscp.net/
2. Connect using your `.ppk` file
3. Navigate to `/home/ubuntu/studyqna/` on server
4. Copy these directories:
   - `backend/` (but exclude: venv, storage, logs, __pycache__)
   - `frontend/` (but exclude: node_modules, dist)

---

## 📝 **File Summary**

### **Total Files to Copy:**

#### **Backend:**
- ✅ **~50-60 Python files** (.py)
- ✅ **7 font files** (.ttf) - **CRITICAL for PDF generation**
- ✅ **1 YOLO model file** (.pt) - For human detection
- ✅ **requirements.txt** - **CRITICAL**
- ✅ **Database migration files**
- ✅ **Configuration files** (alembic.ini, etc.)

#### **Frontend:**
- ✅ **~20 React component files** (.jsx)
- ✅ **package.json** - **CRITICAL**
- ✅ **Configuration files** (vite.config.js, tailwind.config.js, etc.)

### **Files to Create on Server:**
- `.env` file (from `ENV_TEMPLATE.txt`)
- `venv/` directory (virtual environment)
- `storage/` directory (for user uploads)
- `logs/` directory (for application logs)
- `dist/` directory (frontend build output)
- `node_modules/` (frontend dependencies)

---

## ✅ **Verification Checklist**

After copying files, verify on server:

```bash
# Check backend structure
cd /home/ubuntu/studyqna/backend
ls -la app/                    # Should see all Python files
ls -la app/fonts/              # Should see 7 .ttf files
ls -la app/routers/            # Should see all router files
cat requirements.txt           # Should see dependencies list

# Check frontend structure
cd /home/ubuntu/studyqna/frontend
ls -la src/                    # Should see source files
ls -la src/components/         # Should see all components
cat package.json               # Should see dependencies

# Verify critical files exist
test -f backend/requirements.txt && echo "✅ requirements.txt exists"
test -f backend/app/main.py && echo "✅ main.py exists"
test -f frontend/package.json && echo "✅ package.json exists"
test -f frontend/src/main.jsx && echo "✅ main.jsx exists"
test -d backend/app/fonts && echo "✅ fonts directory exists"
```

---

## 🚨 **Critical Files (Must Have)**

If any of these are missing, the application **will not work**:

### **Backend:**
1. ✅ `backend/requirements.txt`
2. ✅ `backend/app/main.py`
3. ✅ `backend/app/config.py`
4. ✅ `backend/app/database.py`
5. ✅ `backend/app/models.py`
6. ✅ `backend/app/fonts/*.ttf` (all 7 font files)
7. ✅ `backend/app/routers/*.py` (all router files)
8. ✅ `backend/yolov8n.pt` (for human detection)

### **Frontend:**
1. ✅ `frontend/package.json`
2. ✅ `frontend/src/main.jsx`
3. ✅ `frontend/src/App.jsx`
4. ✅ `frontend/index.html`
5. ✅ `frontend/vite.config.js`

---

## 📦 **Recommended Copy Method**

**Best Practice: Use Git**

1. **Push your code to GitHub/GitLab** (if not already)
2. **On server, clone the repository**
3. **Create `.env` file from template**
4. **Install dependencies** (venv, node_modules)
5. **Build frontend** (`npm run build`)

This ensures:
- ✅ Clean code (no cache files)
- ✅ Version control
- ✅ Easy updates
- ✅ No missing files

---

## 🔄 **Updating Files After Initial Deployment**

When you need to update code:

### **Using Git (Recommended):**
```bash
# On server
cd /home/ubuntu/studyqna
git pull origin main

# Restart backend
sudo systemctl restart studyqna-backend

# Rebuild frontend (if frontend changed)
cd frontend
npm run build
sudo systemctl restart nginx
```

### **Using SCP/RSYNC:**
```bash
# From local machine, sync only changed files
rsync -avz --exclude='venv' --exclude='node_modules' \
  -e "ssh -i key.pem" \
  backend/ ubuntu@SERVER_IP:/home/ubuntu/studyqna/backend/
```

---

## ✅ **Final Checklist**

Before starting deployment, ensure you have:

- [ ] Backend source code copied (excluding venv, storage, logs)
- [ ] Frontend source code copied (excluding node_modules, dist)
- [ ] All 7 font files in `backend/app/fonts/`
- [ ] `requirements.txt` present
- [ ] `package.json` present
- [ ] `yolov8n.pt` file present
- [ ] Database migration files present

---

**Total Size Estimate:** ~50-100 MB (excluding dependencies)

**Copy Time:** 2-5 minutes (depending on connection speed)


# 📦 Quick Reference: Files to Copy to Server

## ✅ **COPY THESE:**

### **Backend:**
```
backend/
├── app/                    ✅ ALL Python files and subdirectories
├── alembic/                ✅ Migration files
├── migrations/             ✅ Migration scripts
├── requirements.txt        ✅ CRITICAL
├── init_db.py              ✅
├── run_migration.py        ✅
├── run.py                  ✅
├── ENV_TEMPLATE.txt        ✅
├── alembic.ini             ✅
└── yolov8n.pt              ✅
```

### **Frontend:**
```
frontend/
├── src/                    ✅ ALL source files
├── package.json            ✅ CRITICAL
├── package-lock.json       ✅
├── index.html              ✅
├── vite.config.js          ✅
├── tailwind.config.js      ✅
└── postcss.config.js       ✅
```

---

## ❌ **DO NOT COPY:**

### **Backend:**
- ❌ `venv/` (virtual environment - create on server)
- ❌ `storage/` (user uploads - create on server)
- ❌ `logs/` (log files - create on server)
- ❌ `__pycache__/` (Python cache)
- ❌ `.env` (create from template on server)
- ❌ `*.bat` (Windows files)
- ❌ `*.docx`, `*.md` (documentation)
- ❌ `test_*.py` (test files)
- ❌ `Dockerfile` (optional)

### **Frontend:**
- ❌ `node_modules/` (install on server)
- ❌ `dist/` (build on server)
- ❌ `.env` (if exists)
- ❌ `Dockerfile` (optional)

---

## 🚀 **Quick Copy Commands**

### **Using Git (Best Method):**
```bash
# On server
cd /home/ubuntu/studyqna
git clone YOUR_REPO_URL .
```

### **Using SCP (Windows PowerShell):**
```powershell
# From project root
scp -i key.pem -r backend ubuntu@SERVER_IP:/home/ubuntu/studyqna/
scp -i key.pem -r frontend ubuntu@SERVER_IP:/home/ubuntu/studyqna/
```

### **Using RSYNC (Mac/Linux):**
```bash
# From project root
rsync -avz --exclude='venv' --exclude='storage' --exclude='logs' \
  --exclude='__pycache__' --exclude='*.pyc' \
  -e "ssh -i key.pem" \
  backend/ ubuntu@SERVER_IP:/home/ubuntu/studyqna/backend/

rsync -avz --exclude='node_modules' --exclude='dist' \
  -e "ssh -i key.pem" \
  frontend/ ubuntu@SERVER_IP:/home/ubuntu/studyqna/frontend/
```

---

## ✅ **Critical Files (Must Have):**

**Backend:**
- `requirements.txt`
- `app/main.py`
- `app/fonts/*.ttf` (all 7 fonts)
- `yolov8n.pt`

**Frontend:**
- `package.json`
- `src/main.jsx`
- `index.html`

---

## 📝 **After Copying, Create on Server:**

1. `.env` file (from `ENV_TEMPLATE.txt`)
2. `venv/` directory (run: `python3 -m venv venv`)
3. `storage/` directory (run: `mkdir -p storage/uploads`)
4. `logs/` directory (run: `mkdir -p logs`)

---

**See `FILES_TO_COPY_TO_SERVER.md` for detailed list.**


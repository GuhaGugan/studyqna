# 🧹 Code Cleanup Checklist - Pre-Sale

## ⚠️ CRITICAL: Remove Before Selling

### **1. API Keys & Secrets**

- [ ] **OpenAI API Key**: Remove from `.env` files, use placeholders
- [ ] **Database Credentials**: Remove from code, use `.env.example`
- [ ] **Email Service Keys**: Remove Brevo/SMTP credentials
- [ ] **JWT Secret**: Generate new placeholder
- [ ] **Any other API keys**: Check all `.env` files

**Files to Check:**
```
backend/.env (REMOVE - create .env.example instead)
backend/app/config.py (check for hardcoded values)
frontend/.env (if exists)
```

### **2. Personal Information**

- [ ] **Email addresses**: Replace with placeholders
- [ ] **Personal names**: Remove from comments
- [ ] **Company names**: Replace with placeholders
- [ ] **Phone numbers**: Remove if any
- [ ] **Addresses**: Remove if any

**Files to Check:**
```
All .py files (comments)
All .jsx files (comments)
README.md
Documentation files
```

### **3. Test Data**

- [ ] **Database**: Export schema only, no data
- [ ] **Test files**: Remove from `storage/uploads/`
- [ ] **Log files**: Clear `logs/` directory
- [ ] **Temporary files**: Remove all `.tmp`, `.log` files

**Directories to Clean:**
```
backend/storage/uploads/ (keep structure, remove files)
backend/logs/ (clear all logs)
frontend/dist/ (optional - can keep for reference)
```

### **4. Hardcoded Values**

- [ ] **URLs**: Replace with environment variables
- [ ] **Domain names**: Use placeholders
- [ ] **IP addresses**: Remove if any
- [ ] **Port numbers**: Use environment variables

**Files to Check:**
```
backend/app/config.py
frontend/src/utils/api.js
All configuration files
```

### **5. Git History (Optional but Recommended)**

- [ ] **Remove sensitive commits**: Use `git filter-branch` or `git filter-repo`
- [ ] **Clean commit history**: Remove any commits with secrets
- [ ] **Create fresh repository**: Consider creating new repo for sale

**Commands:**
```bash
# Create new clean repository
git clone --bare <old-repo> <new-repo>
cd <new-repo>
# Remove sensitive files from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## 📝 Documentation Updates

### **1. Environment Variables**

- [ ] **Create `.env.example`**: Template with placeholders
- [ ] **Document all variables**: Explain what each does
- [ ] **Remove real values**: Only placeholders

**Example `.env.example`:**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# JWT
JWT_SECRET_KEY=your_jwt_secret_here

# Email (Brevo)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_brevo_email
SMTP_PASSWORD=your_brevo_password
```

### **2. README Updates**

- [ ] **Remove personal info**: Replace with generic
- [ ] **Update installation steps**: Clear, step-by-step
- [ ] **Add buyer notes**: What they need to configure
- [ ] **Remove test credentials**: If any mentioned

### **3. Code Comments**

- [ ] **Remove personal notes**: Any "TODO for me" type comments
- [ ] **Clean up comments**: Make professional
- [ ] **Remove debug code**: Any console.logs, print statements (optional)

---

## 🔒 Security Checklist

### **1. Secrets Management**

- [ ] **No secrets in code**: All in environment variables
- [ ] **No secrets in git**: Check `.gitignore`
- [ ] **No secrets in logs**: Ensure logs don't contain secrets

### **2. Database**

- [ ] **Export schema only**: No user data
- [ ] **Remove test users**: Keep only admin template
- [ ] **Anonymize if needed**: If keeping sample data

### **3. Files**

- [ ] **Remove uploaded files**: Clear `storage/uploads/`
- [ ] **Remove generated PDFs**: Clear any test outputs
- [ ] **Remove logs**: Clear all log files

---

## 📦 Package Preparation

### **1. Create Clean Package**

- [ ] **Remove node_modules**: Buyer will install
- [ ] **Remove venv**: Buyer will create
- [ ] **Remove __pycache__**: Clean Python cache
- [ ] **Remove .git**: Optional - can include or exclude

**Commands:**
```bash
# Remove dependencies (buyer will install)
rm -rf node_modules/
rm -rf venv/
rm -rf __pycache__/
find . -name "*.pyc" -delete
find . -name ".pytest_cache" -type d -exec rm -r {} +
```

### **2. Create Documentation Package**

- [ ] **Installation guide**: Step-by-step
- [ ] **Deployment guide**: AWS, Docker, etc.
- [ ] **API documentation**: Endpoints, schemas
- [ ] **Database schema**: ER diagram, migrations
- [ ] **Environment setup**: All variables explained

### **3. Create .gitignore (if including .git)**

```gitignore
# Environment
.env
.env.local
.env.*.local

# Dependencies
node_modules/
venv/
__pycache__/

# Logs
*.log
logs/

# Uploads
storage/uploads/*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## ✅ Final Verification

### **Before Packaging:**

- [ ] **Search for secrets**: `grep -r "sk-" .` (OpenAI keys)
- [ ] **Search for emails**: `grep -r "@" . --include="*.py" --include="*.jsx"`
- [ ] **Search for passwords**: `grep -r "password" . --include="*.py" --include="*.env"`
- [ ] **Check .gitignore**: Ensure sensitive files ignored
- [ ] **Test installation**: Fresh install on clean system
- [ ] **Verify documentation**: All steps work

### **Test Fresh Installation:**

```bash
# On clean system
git clone <repository>
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with placeholders
python init_db.py
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📋 Pre-Sale Checklist Summary

### **Must Do:**
- [ ] Remove all API keys
- [ ] Remove personal information
- [ ] Create `.env.example`
- [ ] Clean database (schema only)
- [ ] Remove test files
- [ ] Update README
- [ ] Test fresh installation

### **Should Do:**
- [ ] Clean git history
- [ ] Remove debug code
- [ ] Professionalize comments
- [ ] Create comprehensive docs

### **Nice to Have:**
- [ ] Create demo video
- [ ] Take screenshots
- [ ] Create FAQ
- [ ] Prepare pitch deck

---

## 🚨 Common Mistakes to Avoid

1. **❌ Leaving API keys in code**
2. **❌ Including production database**
3. **❌ Forgetting to update .env.example**
4. **❌ Leaving personal email/name in comments**
5. **❌ Including test user data**
6. **❌ Forgetting to clean logs**
7. **❌ Not testing fresh installation**

---

## ✅ Ready to Package?

Once all items are checked:

1. **Create ZIP/TAR** of cleaned codebase
2. **Include documentation** package
3. **Create .env.example** with all variables
4. **Test on fresh system** to verify
5. **Package and upload** to marketplace

**Good luck with your sale! 🚀**




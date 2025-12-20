# Deploy Latest Features to Production Server

## Issue
Production server is missing:
- "Request More Credits" button
- Updated daily limit (60 instead of 50)
- Latest frontend and backend code

## Solution
Update both frontend and backend code, run database migrations, and restart services.

---

## Step-by-Step Deployment Guide

### Step 1: SSH into Production Server

```bash
ssh studyqna@YOUR_SERVER_IP
# or
ssh ubuntu@YOUR_SERVER_IP
```

### Step 2: Navigate to Project Directory

```bash
cd ~/studyqna-assistant
# or wherever your project is located
# Common locations:
# - /home/studyqna/studyqna-assistant
# - /home/ubuntu/studyqna-assistant
# - /opt/studyqna-assistant
```

### Step 3: Backup Current Code (Optional but Recommended)

```bash
# Create backup directory
mkdir -p ~/backups/studyqna-$(date +%Y%m%d-%H%M%S)

# Copy current code
cp -r backend ~/backups/studyqna-$(date +%Y%m%d-%H%M%S)/backend
cp -r frontend ~/backups/studyqna-$(date +%Y%m%d-%H%M%S)/frontend
```

### Step 4: Update Code Files

#### Option A: Using Git (Recommended)

If your code is in Git:

```bash
# Pull latest changes
git pull origin main
# or
git pull origin master
```

#### Option B: Using SCP/RSYNC (Manual Copy)

If not using Git, copy files from your local machine:

**From your local machine (Windows PowerShell):**
```powershell
# Navigate to project root
cd "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant"

# Copy backend files
scp -r backend/app/* studyqna@YOUR_SERVER_IP:~/studyqna-assistant/backend/app/

# Copy frontend files
scp -r frontend/src/* studyqna@YOUR_SERVER_IP:~/studyqna-assistant/frontend/src/
```

**From your local machine (Mac/Linux):**
```bash
# Navigate to project root
cd /path/to/StudyQnA\ Assistant

# Copy backend files
rsync -avz --exclude='__pycache__' --exclude='*.pyc' \
  -e "ssh" \
  backend/app/ studyqna@YOUR_SERVER_IP:~/studyqna-assistant/backend/app/

# Copy frontend files
rsync -avz --exclude='node_modules' \
  -e "ssh" \
  frontend/src/ studyqna@YOUR_SERVER_IP:~/studyqna-assistant/frontend/src/
```

### Step 5: Update Backend Configuration

```bash
# Navigate to backend
cd ~/studyqna-assistant/backend

# Edit config.py to ensure correct defaults
# The code should already have:
# - PREMIUM_DAILY_GENERATION_LIMIT: 60
# - PREMIUM_TOTAL_QUESTIONS_LIMIT: 700
# - MAX_QUESTIONS_PER_GENERATE: 15

# Verify config.py has correct values
grep -n "PREMIUM_DAILY_GENERATION_LIMIT\|PREMIUM_TOTAL_QUESTIONS_LIMIT\|MAX_QUESTIONS_PER_GENERATE" app/config.py
```

### Step 6: Update .env File (Add Missing Variables)

```bash
# Edit .env file
nano .env
# or
vi .env
```

**Add or update these lines:**
```env
# Daily Generation Limit (Premium Users)
PREMIUM_DAILY_GENERATION_LIMIT=60

# Total Questions Limit (Premium Users)
PREMIUM_TOTAL_QUESTIONS_LIMIT=700
```

**Save and exit:**
- Nano: `Ctrl+X`, then `Y`, then `Enter`
- Vi: `Esc`, type `:wq`, then `Enter`

### Step 7: Run Database Migration for Credit Requests

```bash
# Navigate to backend
cd ~/studyqna-assistant/backend

# Activate virtual environment
source venv/bin/activate
# or if using different venv location:
# source ~/venv/bin/activate

# Run the credit request migration
python migrations/run_credit_request_migration_standalone.py

# Or if that doesn't work, run SQL directly:
psql -U studyqna_user -d studyqna -f migrations/add_credit_request_feature.sql
```

**Expected output:**
```
✅ Migration completed successfully!
✅ Added bonus_questions column to users table
✅ Created credit_requests table
✅ Created indexes
```

### Step 8: Install/Update Backend Dependencies (if needed)

```bash
# Navigate to backend
cd ~/studyqna-assistant/backend

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt
```

### Step 9: Restart Backend Service

```bash
# If using systemd:
sudo systemctl restart studyqna-backend

# Check status
sudo systemctl status studyqna-backend

# If using PM2:
pm2 restart studyqna-backend
pm2 status

# If running manually, stop and restart:
# Stop: Find process and kill it
ps aux | grep uvicorn
kill <PID>

# Start: (in screen/tmux or as service)
cd ~/studyqna-assistant/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 10: Update Frontend Dependencies (if needed)

```bash
# Navigate to frontend
cd ~/studyqna-assistant/frontend

# Install dependencies (if package.json changed)
npm install
```

### Step 11: Rebuild Frontend

```bash
# Navigate to frontend
cd ~/studyqna-assistant/frontend

# Build for production
npm run build

# Wait for build to complete (1-2 minutes)
# You should see: "build completed successfully"
```

### Step 12: Verify Build Output

```bash
# Check if dist folder was created/updated
ls -la dist/

# Check modification time (should be recent)
stat dist/index.html
```

### Step 13: Reload Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx

# Or restart if needed
sudo systemctl restart nginx
```

### Step 14: Verify Backend is Running

```bash
# Check backend logs
sudo journalctl -u studyqna-backend -n 50 --no-pager
# or
pm2 logs studyqna-backend --lines 50

# Check if backend is responding
curl http://localhost:8000/api/health
# or
curl http://localhost:8000/docs
```

---

## Critical Files That Must Be Updated

### Backend Files:
1. ✅ `backend/app/config.py` - Updated limits
2. ✅ `backend/app/models.py` - CreditRequest model
3. ✅ `backend/app/schemas.py` - Credit request schemas
4. ✅ `backend/app/routers/user.py` - Request credits endpoint
5. ✅ `backend/app/routers/admin.py` - Credit request management
6. ✅ `backend/app/routers/qna.py` - Updated generation logic
7. ✅ `backend/app/content_validation.py` - Updated validation rules
8. ✅ `backend/app/ai_service.py` - Single image handling
9. ✅ `backend/app/generation_tracker.py` - Daily count fix

### Frontend Files:
1. ✅ `frontend/src/pages/Dashboard.jsx` - Credit request button
2. ✅ `frontend/src/components/ProfileTab.jsx` - Credit request button
3. ✅ `frontend/src/pages/AdminDashboard.jsx` - Credit requests tab
4. ✅ `frontend/src/utils/api.js` - Credit request API calls
5. ✅ `frontend/src/components/QnAGenerator.jsx` - Updated limits display
6. ✅ `frontend/src/components/FileUpload.jsx` - Toast fix

### Database:
1. ✅ `backend/migrations/add_credit_request_feature.sql` - Migration script
2. ✅ `backend/migrations/run_credit_request_migration_standalone.py` - Migration runner

---

## Verification Checklist

After deployment, verify:

### 1. Backend API Endpoints
```bash
# Test credit request endpoint (should return 401 if not logged in, but endpoint should exist)
curl -X POST http://localhost:8000/api/user/request-credits

# Test admin credit requests endpoint
curl http://localhost:8000/api/admin/credit-requests
```

### 2. Frontend Features
- [ ] "Request More Credits" button appears in Dashboard when questions ≤ 50
- [ ] "Request More Credits" button appears in Profile tab when questions ≤ 50
- [ ] Daily Questions shows **60** (not 50)
- [ ] Total Questions shows **700**
- [ ] Credit request modal opens and submits correctly
- [ ] Admin Dashboard has "Credit Requests" tab

### 3. Database
```bash
# Check if credit_requests table exists
psql -U studyqna_user -d studyqna -c "\d credit_requests"

# Check if bonus_questions column exists
psql -U studyqna_user -d studyqna -c "\d users" | grep bonus_questions
```

---

## Quick Deployment Script

If you want to automate the process, create this script on the server:

```bash
#!/bin/bash
# save as: ~/deploy-updates.sh

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Navigate to project
cd ~/studyqna-assistant

# Pull latest code (if using Git)
if [ -d .git ]; then
    echo "📥 Pulling latest code..."
    git pull origin main || git pull origin master
fi

# Backend updates
echo "🔧 Updating backend..."
cd backend
source venv/bin/activate
pip install -q -r requirements.txt

# Run migration if needed
if [ -f "migrations/run_credit_request_migration_standalone.py" ]; then
    echo "🗄️  Running database migration..."
    python migrations/run_credit_request_migration_standalone.py || echo "⚠️  Migration may have already run"
fi

# Restart backend
echo "🔄 Restarting backend..."
sudo systemctl restart studyqna-backend || pm2 restart studyqna-backend

# Frontend updates
echo "🎨 Updating frontend..."
cd ../frontend
npm install --silent
npm run build

# Reload Nginx
echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo "📋 Please verify the application is working correctly."
```

**Make it executable:**
```bash
chmod +x ~/deploy-updates.sh
```

**Run it:**
```bash
~/deploy-updates.sh
```

---

## Troubleshooting

### If "Request More Credits" button doesn't appear:

1. **Check if user has ≤ 50 questions remaining:**
   - The button only shows when `remaining ≤ 50`
   - Check in browser console: `localStorage` or check API response

2. **Check if frontend code was updated:**
   ```bash
   # On server, check file modification time
   stat ~/studyqna-assistant/frontend/src/pages/Dashboard.jsx
   # Should be recent
   ```

3. **Clear browser cache:**
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Or clear cache completely

### If daily limit still shows 50:

1. **Check backend .env file:**
   ```bash
   grep PREMIUM_DAILY_GENERATION_LIMIT ~/studyqna-assistant/backend/.env
   # Should show: PREMIUM_DAILY_GENERATION_LIMIT=60
   ```

2. **Check backend config.py:**
   ```bash
   grep PREMIUM_DAILY_GENERATION_LIMIT ~/studyqna-assistant/backend/app/config.py
   # Should show default: 60
   ```

3. **Restart backend:**
   ```bash
   sudo systemctl restart studyqna-backend
   ```

### If database migration fails:

1. **Check database connection:**
   ```bash
   psql -U studyqna_user -d studyqna -c "SELECT 1;"
   ```

2. **Check if table already exists:**
   ```bash
   psql -U studyqna_user -d studyqna -c "\d credit_requests"
   # If it exists, migration already ran
   ```

3. **Run migration manually:**
   ```bash
   cd ~/studyqna-assistant/backend
   source venv/bin/activate
   python migrations/run_credit_request_migration_standalone.py
   ```

---

## Summary

**What needs to be updated:**
1. ✅ Backend code (all Python files)
2. ✅ Frontend code (all React components)
3. ✅ Database (run migration for credit requests)
4. ✅ Environment variables (add PREMIUM_DAILY_GENERATION_LIMIT=60)
5. ✅ Rebuild frontend
6. ✅ Restart backend
7. ✅ Reload Nginx

**Expected result:**
- Daily Questions: **60** (not 50)
- Total Questions: **700**
- "Request More Credits" button visible when ≤ 50 questions remaining
- Credit request feature working
- Admin can approve/reject credit requests

---

## Need Help?

If you encounter issues:
1. Check backend logs: `sudo journalctl -u studyqna-backend -f`
2. Check frontend build: `cd frontend && npm run build`
3. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Verify database: `psql -U studyqna_user -d studyqna -c "\dt"`


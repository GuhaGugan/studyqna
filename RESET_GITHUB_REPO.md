# Reset GitHub Repository - Two Options

## ⚠️ WARNING
- **Option 1 (Recommended)**: Force push - keeps your local changes, just overwrites GitHub
- **Option 2 (Nuclear)**: Complete reset - removes ALL history from GitHub

---

## Option 1: Force Push (Recommended - Safer)

This will overwrite GitHub with your local code but keeps the repository structure.

### On Your Local Machine:

```bash
# Make sure you're on main branch
git checkout main

# Add all current files
git add .

# Commit everything (if not already committed)
git commit -m "Complete reset: sync local codebase to GitHub"

# Force push to GitHub (overwrites remote)
git push origin main --force

# Verify
git log --oneline -5
```

**This is safer because:**
- ✅ Keeps repository structure
- ✅ You can still see commit history locally
- ✅ Easier to recover if something goes wrong

---

## Option 2: Complete Reset (Nuclear Option)

This completely removes everything from GitHub and starts fresh.

### Step 1: Backup Important Data

```bash
# Create a backup of your current code
cp -r "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant" "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant BACKUP"
```

### Step 2: Remove .git and Start Fresh

```powershell
# Navigate to your project
cd "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant"

# Remove existing git repository
Remove-Item -Recurse -Force .git

# Initialize new git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - fresh start"

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/GuhaGugan/studyqna.git

# Force push to GitHub (this will overwrite everything)
git push origin main --force
```

### Step 3: Update Production Server

After pushing to GitHub, on your server:

```bash
cd ~/studyqna/studyqna

# Backup current code (just in case)
cp -r . ../studyqna-backup-$(date +%Y%m%d)

# Remove and re-clone
cd ~/studyqna
rm -rf studyqna
git clone https://github.com/GuhaGugan/studyqna.git studyqna

# Navigate to project
cd studyqna/studyqna

# Restore .env file (if you have one)
# cp ../studyqna-backup-*/backend/.env backend/.env

# Rebuild frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart studyqna-backend
sudo systemctl restart nginx
```

---

## Option 3: Clean Reset (Recommended Alternative)

This keeps your repository but removes all commit history.

### On Your Local Machine:

```bash
# Create orphan branch (no history)
git checkout --orphan new-main

# Add all files
git add .

# Commit
git commit -m "Initial commit - clean start"

# Delete old main branch
git branch -D main

# Rename current branch to main
git branch -m main

# Force push to GitHub
git push origin main --force

# Clean up
git gc --aggressive --prune=all
```

---

## Which Option Should You Choose?

- **Option 1**: If you just want to sync your local code to GitHub (recommended)
- **Option 2**: If you want to completely start fresh (loses all history)
- **Option 3**: If you want a clean start but keep repository structure

---

## After Any Option: Update Production Server

```bash
# SSH into server
ssh ubuntu@YOUR_SERVER_IP

# Navigate to project
cd ~/studyqna/studyqna

# Pull latest code
git pull origin main --force

# Rebuild frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart studyqna-backend
sudo systemctl restart nginx
```

---

## ⚠️ Important Notes:

1. **Backup First**: Always backup your code before doing any reset
2. **Production Server**: Make sure to update your production server after resetting
3. **Environment Files**: Don't commit `.env` files - they should remain on the server
4. **Database**: Your database won't be affected by this
5. **Storage Files**: Uploaded files won't be affected

---

## Recommended Approach:

I recommend **Option 1 (Force Push)** because:
- ✅ Simplest and safest
- ✅ Keeps repository structure
- ✅ Easy to recover
- ✅ No need to reconfigure server

Just run:
```bash
git add .
git commit -m "Complete sync: local to GitHub"
git push origin main --force
```





# Update Production Server After Fresh Repository

## Step-by-Step Instructions:

### Step 1: Navigate to Backend Directory

```bash
cd ~/studyqna/studyqna/backend
```

### Step 2: Install Backend Dependencies

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install requirements (note: requirements.txt, not requirement.txt)
pip install -r requirements.txt
```

### Step 3: Build Frontend

```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### Step 4: Restart Services

```bash
# Restart backend
sudo systemctl restart studyqna-backend

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status studyqna-backend
sudo systemctl status nginx
```

### Step 5: Restore Environment File (if needed)

If you had a `.env` file before, restore it:

```bash
# Check if backup exists
ls -la ~/studyqna-backup-*/backend/.env

# Copy it (replace YYYYMMDD with actual date)
cp ~/studyqna-backup-YYYYMMDD/backend/.env ~/studyqna/studyqna/backend/.env

# Or create a new one if it doesn't exist
cd ~/studyqna/studyqna/backend
nano .env
# Add your environment variables
```

---

## Quick Commands (Copy & Paste):

```bash
# Backend setup
cd ~/studyqna/studyqna/backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart studyqna-backend
sudo systemctl restart nginx

# Verify
sudo systemctl status studyqna-backend
```

---

## Common Issues:

### If requirements.txt doesn't exist:
```bash
# Check if file exists
ls -la ~/studyqna/studyqna/backend/requirements.txt

# If missing, check the repository structure
ls -la ~/studyqna/studyqna/backend/
```

### If virtual environment doesn't exist:
```bash
cd ~/studyqna/studyqna/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### If npm install fails:
```bash
cd ~/studyqna/studyqna/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```




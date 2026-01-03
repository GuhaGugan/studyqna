# Fix Backend Service After Repository Reset

## Issue: Backend service failed to start

This is likely because the systemd service file points to the old directory path.

---

## Step 1: Check Service Status and Logs

```bash
# Check service status
sudo systemctl status studyqna-backend.service

# Check detailed logs
sudo journalctl -xeu studyqna-backend.service -n 50
```

---

## Step 2: Check Service File Configuration

```bash
# View the service file
sudo cat /etc/systemd/system/studyqna-backend.service
```

Look for the `WorkingDirectory` and `ExecStart` paths - they should point to:
- `/home/ubuntu/studyqna/studyqna/backend` (or wherever your new repository is)

---

## Step 3: Update Service File

```bash
# Edit the service file
sudo nano /etc/systemd/system/studyqna-backend.service
```

Make sure it looks like this (adjust paths as needed):

```ini
[Unit]
Description=StudyQnA Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/studyqna/studyqna/backend
Environment="PATH=/home/ubuntu/studyqna/studyqna/backend/venv/bin"
ExecStart=/home/ubuntu/studyqna/studyqna/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save**: `Ctrl+X`, then `Y`, then `Enter`

---

## Step 4: Reload Systemd and Restart

```bash
# Reload systemd to pick up changes
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart studyqna-backend

# Check status
sudo systemctl status studyqna-backend
```

---

## Step 5: Check for Missing Dependencies

```bash
# Navigate to backend
cd ~/studyqna/studyqna/backend

# Activate virtual environment
source venv/bin/activate

# Check if all dependencies are installed
pip list

# If missing, install requirements
pip install -r requirements.txt
```

---

## Step 6: Check Environment Variables

```bash
# Make sure .env file exists
ls -la ~/studyqna/studyqna/backend/.env

# If missing, create it or copy from backup
# cp ~/studyqna-backup-*/backend/.env ~/studyqna/studyqna/backend/.env
```

---

## Step 7: Test Backend Manually

```bash
cd ~/studyqna/studyqna/backend
source venv/bin/activate

# Test if backend starts manually
uvicorn app.main:app --host 0.0.0.0 --port 8000

# If it works, press Ctrl+C to stop
# Then the service should work too
```

---

## Common Issues:

### Issue 1: Wrong Working Directory
**Solution**: Update `WorkingDirectory` in service file to match new repository location

### Issue 2: Virtual Environment Path Wrong
**Solution**: Update `Environment` and `ExecStart` paths in service file

### Issue 3: Missing .env File
**Solution**: Create or restore `.env` file in backend directory

### Issue 4: Dependencies Not Installed
**Solution**: Run `pip install -r requirements.txt` in virtual environment

### Issue 5: Port Already in Use
**Solution**: 
```bash
# Check what's using port 8000
sudo lsof -i :8000
# Kill the process if needed
sudo kill -9 <PID>
```

---

## Quick Fix Commands:

```bash
# 1. Check current service file
sudo cat /etc/systemd/system/studyqna-backend.service

# 2. Update paths if needed
sudo nano /etc/systemd/system/studyqna-backend.service

# 3. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart studyqna-backend

# 4. Check status
sudo systemctl status studyqna-backend

# 5. Check logs if still failing
sudo journalctl -u studyqna-backend -f
```





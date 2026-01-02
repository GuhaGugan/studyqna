# Update Lightsail Server - Answer Display Fix

## Steps to Deploy Changes to Lightsail Server

### 1. SSH into Lightsail Server
```bash
ssh ubuntu@your-lightsail-ip
```

### 2. Navigate to Project Directory
```bash
cd ~/studyqna/studyqna
```

### 3. Pull Latest Changes from GitHub
```bash
git pull origin main
```

### 4. Update Backend

#### Navigate to backend directory
```bash
cd backend
```

#### Activate virtual environment (if using venv)
```bash
source venv/bin/activate
```

#### Install any new dependencies (if requirements.txt was updated)
```bash
pip install -r requirements.txt
```

#### Restart Backend Service
```bash
sudo systemctl restart studyqna-backend
```

#### Check Backend Status
```bash
sudo systemctl status studyqna-backend
```

#### View Backend Logs (if needed)
```bash
sudo journalctl -u studyqna-backend -f
```

### 5. Update Frontend

#### Navigate to frontend directory
```bash
cd ../frontend
```

#### Install any new dependencies (if package.json was updated)
```bash
npm install
```

#### Build Frontend
```bash
npm run build
```

#### Restart Frontend Service (if using PM2 or similar)
```bash
# If using PM2:
pm2 restart studyqna-frontend

# Or if using systemd:
sudo systemctl restart studyqna-frontend
```

#### Check Frontend Status
```bash
# If using PM2:
pm2 status

# Or if using systemd:
sudo systemctl status studyqna-frontend
```

### 6. Verify Deployment

#### Check Backend Health
```bash
curl http://localhost:8000/api/health
# Or check your domain API endpoint
```

#### Check Frontend
- Open your domain in a browser
- Test the Generate tab to verify answers are displaying
- Test mobile responsive mode

### 7. Troubleshooting

#### If Backend Fails to Start
```bash
# Check logs
sudo journalctl -u studyqna-backend -n 50

# Check for syntax errors
cd ~/studyqna/studyqna/backend
source venv/bin/activate
python -c "import app.main; print('✅ Syntax OK')"
```

#### If Frontend Fails to Build
```bash
cd ~/studyqna/studyqna/frontend
npm install
npm run build
# Check for any error messages
```

#### If Services Are Not Running
```bash
# Check all services
sudo systemctl status studyqna-backend
sudo systemctl status studyqna-frontend

# Restart nginx if needed
sudo systemctl restart nginx
```

### 8. Quick Update Script (Optional)

You can create a script to automate the update:

```bash
#!/bin/bash
# update-server.sh

cd ~/studyqna/studyqna
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart studyqna-backend

# Update frontend
cd ../frontend
npm install
npm run build
pm2 restart studyqna-frontend  # or systemctl restart

echo "✅ Update complete!"
```

Make it executable:
```bash
chmod +x update-server.sh
```

Run it:
```bash
./update-server.sh
```

## Changes Included in This Update

1. **Answer Display Fix**: Fixed rendering of answers with capitalized keys (Background/Context, Key Points, etc.)
2. **Mobile Responsive Fix**: Improved Q/A generation display in mobile mode
3. **Enhanced Debugging**: Added comprehensive logging for troubleshooting
4. **State Management**: Improved result persistence and state handling

## Expected Behavior After Update

- ✅ Answers should display correctly in the Generate tab
- ✅ Answers should show Background/Context, Key Points, Explanation, Conclusion sections
- ✅ Mobile responsive mode should display generated Q/A correctly
- ✅ Console logs will provide detailed debugging information

## Rollback (If Needed)

If something goes wrong, you can rollback to the previous commit:

```bash
cd ~/studyqna/studyqna
git log --oneline -5  # View recent commits
git reset --hard <previous-commit-hash>
git push origin main --force  # Only if necessary
sudo systemctl restart studyqna-backend
cd frontend && npm run build && pm2 restart studyqna-frontend
```

**Note**: Be careful with `--force` push. Only use if absolutely necessary.




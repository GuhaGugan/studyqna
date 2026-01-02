# Complete Guide: Update Frontend on Production Server

## ⚠️ Issues to Fix:
1. ❌ Still showing "Select Subject" dropdown (should be removed)
2. ❌ Getting 2 OTP notifications (should be only 1)
3. ❌ Frontend not updated on domain

---

## Step 1: Verify All Changes Are Committed and Pushed

### On Your Local Machine:

```bash
# Check if there are any uncommitted changes
git status

# If there are changes, commit them:
git add .
git commit -m "Update frontend: remove subject selector, fix OTP notification"
git push origin main
```

---

## Step 2: SSH into Production Server

```bash
ssh ubuntu@YOUR_SERVER_IP
# Or use your SSH key file
```

---

## Step 3: Update Code on Production Server

```bash
# Navigate to project directory
cd ~/studyqna/studyqna

# Pull latest code from GitHub
git pull origin main

# Verify the pull was successful
git log --oneline -5
```

---

## Step 4: Rebuild Frontend

```bash
# Navigate to frontend directory
cd frontend

# Remove old build and cache
rm -rf dist node_modules/.vite

# Install dependencies (in case package.json changed)
npm install

# Build for production
npm run build

# Verify build was successful
ls -la dist/
# Should show index.html and other files
```

---

## Step 5: Restart Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

---

## Step 6: Verify Nginx Configuration

```bash
# Check if Nginx is pointing to the correct directory
sudo cat /etc/nginx/sites-available/studyqna | grep root

# Should show something like:
# root /home/ubuntu/studyqna/frontend/dist;

# If wrong, update it:
sudo nano /etc/nginx/sites-available/studyqna
# Update the root path to: /home/ubuntu/studyqna/frontend/dist
# Save: Ctrl+X, then Y, then Enter

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 7: Clear Browser Cache

On your local browser:
- **Chrome/Edge**: Press `Ctrl + Shift + Delete`
  - Select "Cached images and files"
  - Time range: "All time"
  - Click "Clear data"
- **Or use Incognito/Private window**: `Ctrl + Shift + N`
- **Or hard refresh**: `Ctrl + Shift + R` or `Ctrl + F5`

---

## Step 8: Verify the Update

1. Visit `https://app.gugancloud.co.in/dashboard` in a new incognito window
2. Check:
   - ✅ "Select Subject" dropdown should NOT be visible in Upload page
   - ✅ Only ONE OTP notification should appear when requesting OTP
   - ✅ Numbers should match localhost

---

## Troubleshooting

### If build fails:

```bash
# Check Node.js version (should be 18+)
node --version

# If outdated:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Clear npm cache
npm cache clean --force

# Remove and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### If Nginx shows old content:

```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if dist folder exists and has new files
ls -la ~/studyqna/studyqna/frontend/dist/
stat ~/studyqna/studyqna/frontend/dist/index.html

# Force Nginx to reload
sudo systemctl reload nginx
```

### If still seeing old content:

```bash
# Check Nginx cache (if enabled)
sudo rm -rf /var/cache/nginx/*

# Restart Nginx
sudo systemctl restart nginx

# Check what Nginx is actually serving
curl -I http://localhost/
```

---

## Quick One-Liner (Copy & Paste):

```bash
cd ~/studyqna/studyqna && git pull origin main && cd frontend && rm -rf dist node_modules/.vite && npm install && npm run build && sudo systemctl restart nginx && echo "✅ Frontend updated successfully!"
```

---

## After Update Checklist:

- [ ] Code pulled from GitHub
- [ ] Frontend built successfully (`npm run build`)
- [ ] Nginx restarted
- [ ] Browser cache cleared
- [ ] "Select Subject" removed from Upload page
- [ ] Only 1 OTP notification appears
- [ ] Numbers match localhost




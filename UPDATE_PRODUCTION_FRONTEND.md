# Update Frontend on Production Server (app.gugancloud.co.in)

## Step-by-Step Instructions:

### 1. SSH into your Lightsail server
```bash
ssh ubuntu@YOUR_SERVER_IP
# Or use your SSH key
```

### 2. Navigate to the project directory
```bash
cd ~/studyqna/studyqna
```

### 3. Pull the latest code from GitHub
```bash
git pull origin main
```

### 4. Navigate to frontend directory
```bash
cd frontend
```

### 5. Install/Update dependencies (if package.json changed)
```bash
npm install
```

### 6. Build the frontend for production
```bash
npm run build
```

This will create/update the `dist/` folder with the latest frontend code.

### 7. Restart Nginx to serve the new build
```bash
sudo systemctl restart nginx
```

### 8. Verify Nginx is running
```bash
sudo systemctl status nginx
```

### 9. Check if the build was successful
```bash
ls -la dist/
# Should show index.html and other built files
```

### 10. Clear browser cache on your end
- Press `Ctrl + Shift + Delete`
- Select "Cached images and files"
- Click "Clear data"
- Or use Incognito/Private window

---

## Quick One-Liner (if you're already in the project directory):
```bash
cd ~/studyqna/studyqna && git pull origin main && cd frontend && npm install && npm run build && sudo systemctl restart nginx
```

---

## Troubleshooting:

### If npm install fails:
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### If build fails:
```bash
# Check Node.js version (should be 18+)
node --version

# If outdated, update Node.js:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### If Nginx shows old content:
```bash
# Check Nginx configuration points to correct directory
sudo cat /etc/nginx/sites-available/studyqna | grep root

# Should show: root /home/ubuntu/studyqna/frontend/dist;

# If wrong, update nginx config:
sudo nano /etc/nginx/sites-available/studyqna
# Update the root path
sudo nginx -t
sudo systemctl restart nginx
```

### Verify the update worked:
```bash
# Check the build timestamp
ls -la dist/index.html

# Check Nginx is serving the new files
curl -I http://localhost/
```

---

## After Update:
1. Visit `https://app.gugancloud.co.in/dashboard` in a new incognito window
2. Check if the numbers match localhost
3. Verify all features work correctly




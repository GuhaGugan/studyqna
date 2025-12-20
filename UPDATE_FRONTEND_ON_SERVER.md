# How to Update Frontend Code on Production Server

## Quick Steps to Update FileUpload.jsx Fix

### Step 1: SSH into Your Server

```bash
ssh ubuntu@YOUR_SERVER_IP
# or
ssh studyqna@YOUR_SERVER_IP
```

### Step 2: Navigate to Project Directory

```bash
cd ~/studyqna-assistant
# or wherever your project is located
cd ~/studyqna
```

### Step 3: Pull Latest Changes (if using Git)

If you're using Git and have committed the changes:

```bash
# Pull latest changes
git pull origin main
# or
git pull origin master
```

### Step 4: Update the File Directly (if not using Git)

If you're not using Git, you can update the file directly:

```bash
# Navigate to frontend directory
cd frontend/src/components

# Edit the file
nano FileUpload.jsx
```

**Find this code (around line 85):**
```javascript
toast.warning(
```

**Replace it with:**
```javascript
toast(
```

**And update the options object to include warning styling:**
```javascript
toast(
  `⚠️ ${response.data.subject_mismatch_warning}${response.data.detected_subject ? ` Detected: ${response.data.detected_subject}` : ''}`,
  {
    duration: isMobile ? 8000 : 6000,
    icon: '⚠️',
    style: {
      maxWidth: isMobile ? '95%' : '500px',
      wordBreak: 'break-word',
      fontSize: isMobile ? '14px' : '13px',
      padding: isMobile ? '16px' : '12px',
      backgroundColor: '#fef3c7',
      color: '#92400e',
      border: '1px solid #fbbf24',
    },
    position: isMobile ? 'top-center' : 'top-right'
  }
)
```

**Save and exit:** `Ctrl + X`, then `Y`, then `Enter`

### Step 5: Rebuild Frontend

```bash
# Navigate to frontend directory (if not already there)
cd ~/studyqna-assistant/frontend
# or
cd ~/studyqna/frontend

# Install dependencies (if needed)
npm install

# Build for production
npm run build
```

**Wait for the build to complete** - this may take 1-2 minutes.

### Step 6: Verify Build Output

```bash
# Check if dist folder was created/updated
ls -la dist/

# You should see index.html and other build files
```

### Step 7: Restart Nginx (if needed)

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx to serve new files
sudo systemctl reload nginx
```

### Step 8: Clear Browser Cache (Important!)

**On your mobile device:**
1. Clear browser cache
2. Or use incognito/private mode
3. Or hard refresh (if possible)

**The updated code should now work!**

---

## Alternative: Complete File Replacement Method

If you prefer to replace the entire file:

### Step 1: Copy Updated File to Server

**From your local machine:**
```bash
# Using SCP (replace with your server details)
scp frontend/src/components/FileUpload.jsx ubuntu@YOUR_SERVER_IP:~/studyqna-assistant/frontend/src/components/FileUpload.jsx
```

### Step 2: Rebuild Frontend

```bash
# SSH into server
ssh ubuntu@YOUR_SERVER_IP

# Navigate to frontend
cd ~/studyqna-assistant/frontend

# Rebuild
npm run build
```

### Step 3: Reload Nginx

```bash
sudo systemctl reload nginx
```

---

## Using Git Workflow (Recommended)

If you're using Git, this is the cleanest approach:

### Step 1: Commit and Push Changes Locally

```bash
# On your local machine
git add frontend/src/components/FileUpload.jsx
git commit -m "Fix: Replace toast.warning with toast() for react-hot-toast compatibility"
git push origin main
```

### Step 2: Pull and Rebuild on Server

```bash
# SSH into server
ssh ubuntu@YOUR_SERVER_IP

# Navigate to project
cd ~/studyqna-assistant

# Pull latest changes
git pull origin main

# Navigate to frontend
cd frontend

# Rebuild
npm run build

# Reload Nginx
sudo systemctl reload nginx
```

---

## Verify the Fix

1. **Test on mobile device:**
   - Take a photo and upload it
   - The warning toast should now work without errors

2. **Check browser console:**
   - Open developer tools (if possible on mobile)
   - Look for any JavaScript errors
   - The `toast.warning is not a function` error should be gone

---

## Troubleshooting

### If build fails:

```bash
# Check Node.js version
node --version
# Should be 16+ or 18+

# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Try building again
npm run build
```

### If changes don't appear:

1. **Clear browser cache completely**
2. **Check Nginx is serving the correct directory:**
   ```bash
   # Check Nginx config
   sudo nano /etc/nginx/sites-available/studyqna
   # Verify root points to: /home/studyqna/studyqna-assistant/frontend/dist
   # or your actual path
   ```

3. **Verify build output:**
   ```bash
   ls -la ~/studyqna-assistant/frontend/dist/
   # Check modification time - should be recent
   ```

4. **Restart Nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

---

## Quick One-Liner (if using Git)

```bash
cd ~/studyqna-assistant && git pull origin main && cd frontend && npm run build && sudo systemctl reload nginx
```

This will:
1. Pull latest code
2. Rebuild frontend
3. Reload Nginx

---

## Notes

- **No backend restart needed** - This is a frontend-only change
- **No database changes** - This is purely a UI fix
- **Build time:** Usually 1-2 minutes
- **Downtime:** None - Nginx reload is seamless


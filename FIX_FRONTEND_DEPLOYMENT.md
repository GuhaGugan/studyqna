# Fix Frontend Deployment - Directory Creation

## Issue
The Nginx root directory `/var/www/studyqna-frontend` doesn't exist.

## Solution

### Step 1: Create the Directory

```bash
# Create the directory
sudo mkdir -p /var/www/studyqna-frontend

# Set ownership
sudo chown -R ubuntu:ubuntu /var/www/studyqna-frontend

# Set permissions
sudo chmod -R 755 /var/www/studyqna-frontend
```

### Step 2: Move Frontend Files

```bash
# Move files from /tmp to the correct location
sudo mv /tmp/studyqna-frontend/* /var/www/studyqna-frontend/

# Verify files are there
ls -la /var/www/studyqna-frontend/
```

### Step 3: Verify Nginx Configuration

```bash
# Check Nginx config points to correct location
sudo cat /etc/nginx/sites-available/studyqna | grep -A 5 root

# Should show:
# root /var/www/studyqna-frontend;
```

### Step 4: Test and Reload Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

### Step 5: Verify Files Are Served

```bash
# Check if index.html exists
ls -la /var/www/studyqna-frontend/index.html

# Test if Nginx can serve the files
curl http://localhost/
# Should return HTML content
```

## Complete Command Sequence

Run these commands in order:

```bash
# 1. Create directory
sudo mkdir -p /var/www/studyqna-frontend

# 2. Set ownership
sudo chown -R ubuntu:ubuntu /var/www/studyqna-frontend

# 3. Move files
sudo mv /tmp/studyqna-frontend/* /var/www/studyqna-frontend/

# 4. Verify files
ls -la /var/www/studyqna-frontend/

# 5. Test Nginx
sudo nginx -t

# 6. Reload Nginx
sudo systemctl reload nginx

# 7. Test
curl http://localhost/ | head -20
```

## Alternative: If Files Are Already in Different Location

If your frontend files are already built somewhere else:

```bash
# Find where frontend dist might be
find /home -name "index.html" -type f 2>/dev/null | grep -i frontend
find /var/www -name "index.html" -type f 2>/dev/null

# If found, copy to correct location
sudo cp -r /path/to/existing/dist/* /var/www/studyqna-frontend/
```

## Troubleshooting

### If mv command fails with "directory not empty":
```bash
# Remove existing files first (backup if needed)
sudo rm -rf /var/www/studyqna-frontend/*

# Then move new files
sudo mv /tmp/studyqna-frontend/* /var/www/studyqna-frontend/
```

### If permission denied:
```bash
# Use sudo for all operations
sudo mv /tmp/studyqna-frontend/* /var/www/studyqna-frontend/
sudo chown -R www-data:www-data /var/www/studyqna-frontend
sudo chmod -R 755 /var/www/studyqna-frontend
```

### If Nginx still shows old files:
```bash
# Clear Nginx cache
sudo systemctl restart nginx

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log
```


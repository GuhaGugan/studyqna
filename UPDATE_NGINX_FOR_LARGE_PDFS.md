# Fix: "Request Entity Too Large" for PDFs >50MB

## Problem
You're getting "413 Request Entity Too Large" error when uploading PDFs larger than 50MB on the production server.

## Root Cause
Nginx `client_max_body_size` is currently set to 20MB, but you need to upload PDFs up to 100MB (backend supports this for book splitting feature).

## Solution: Increase Nginx Upload Limit

### Quick Fix (SSH into Server)

```bash
# 1. SSH into your server
ssh ubuntu@YOUR_SERVER_IP

# 2. Edit Nginx configuration
sudo nano /etc/nginx/sites-available/studyqna

# 3. Find this line:
client_max_body_size 20M;

# 4. Change it to:
client_max_body_size 100M;

# 5. Save and exit (Ctrl+X, Y, Enter)

# 6. Test Nginx configuration
sudo nginx -t

# 7. If test passes, reload Nginx
sudo systemctl reload nginx
```

### Verify the Fix

1. Try uploading a large PDF (>50MB) again
2. The error should be resolved

---

## Complete Nginx Configuration

Here's the updated configuration with 100MB limit:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        root /home/studyqna/studyqna/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for large file uploads and AI processing (10 minutes)
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        
        # Increase buffer sizes for large uploads
        proxy_request_buffering off;
        client_body_buffer_size 128k;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        root /home/studyqna/studyqna/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload size limit (100MB for large PDFs and mobile photos)
    client_max_body_size 100M;
}
```

---

## Important Notes

### Backend Limits
- **Backend supports:** Up to 100MB PDFs (`MAX_BOOK_PDF_SIZE_MB: int = 100`)
- **Nginx must match or exceed:** Set to 100MB to match backend

### Timeout Settings
For large file uploads, you may also need to increase timeouts:

```nginx
# In the /api location block:
proxy_read_timeout 600s;      # 10 minutes for large uploads
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
```

### If You Need Larger Files (>100MB)

1. **Update Nginx:**
   ```nginx
   client_max_body_size 200M;  # or higher
   ```

2. **Update Backend Config:**
   Edit `backend/app/config.py`:
   ```python
   MAX_BOOK_PDF_SIZE_MB: int = 200  # Increase from 100 to 200
   ```

3. **Restart Backend:**
   ```bash
   sudo systemctl restart studyqna-backend
   ```

---

## Troubleshooting

### If upload still fails after increasing limit:

1. **Check Nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Verify the limit was applied:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Check backend logs:**
   ```bash
   sudo journalctl -u studyqna-backend -n 50 --no-pager
   ```

4. **Verify backend limit:**
   - Check `backend/app/config.py` - `MAX_BOOK_PDF_SIZE_MB` should be 100 or higher

### Common Issues

- **Still getting 413 error:** Nginx not reloaded - run `sudo systemctl reload nginx`
- **Upload times out:** Increase `proxy_read_timeout` in Nginx config
- **Backend rejects:** Check backend `MAX_BOOK_PDF_SIZE_MB` setting

---

## Summary

**Current Status:**
- ✅ Backend supports: 100MB PDFs
- ❌ Nginx limit: 20MB (needs update)

**Fix:**
- Update Nginx `client_max_body_size` to 100M
- Reload Nginx: `sudo systemctl reload nginx`

**After fix:**
- ✅ PDFs up to 100MB will work
- ✅ Mobile photos will work
- ✅ Large book PDFs can be uploaded and split


# Fix: "Request Entity Too Large" Error for Mobile Image Uploads

## Problem
When uploading images from mobile devices on the domain, you get a "413 Request Entity Too Large" error. This works fine on localhost but fails on the domain.

## Root Cause
Nginx has a default `client_max_body_size` limit of 1MB, and your current configuration sets it to 10MB. Mobile camera photos (especially high-resolution ones) can easily exceed 10MB.

## Solution

### Step 1: Update Nginx Configuration

SSH into your server and edit the Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/studyqna
```

### Step 2: Find and Update `client_max_body_size`

Look for this line:
```nginx
client_max_body_size 10M;
```

Change it to:
```nginx
# File upload size limit (100MB for large PDFs and mobile photos)
client_max_body_size 100M;
```

**Note:** If you don't see this line, add it inside the `server { }` block, typically at the end before the closing brace.

### Step 3: Test and Reload Nginx

```bash
# Test the configuration for syntax errors
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

### Step 4: Verify the Fix

1. Try uploading a mobile photo again
2. The error should be resolved

## Alternative: Increase Further if Needed

If 100MB is still not enough, you can increase it further:

```nginx
client_max_body_size 200M;  # For very large PDFs
```

**Note:** The backend currently supports up to 100MB PDFs for the book splitting feature. If you need larger files, also update `MAX_BOOK_PDF_SIZE_MB` in `backend/app/config.py`.

**Important:** Also ensure your backend configuration allows this size:
- Check `backend/app/config.py` - `MAX_IMAGE_SIZE_MB` should be at least as large as your Nginx limit
- Current backend limit: 10MB (you may want to increase this too)

## Complete Nginx Configuration Example

Here's a complete example with the proper upload limit:

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
        
        # Increase timeouts for AI processing (5 minutes)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
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

## Why It Works on Localhost But Not on Domain

- **Localhost:** When running the development server directly (e.g., `uvicorn app.main:app`), there's no Nginx in between, so the limit doesn't apply
- **Domain/Production:** Nginx acts as a reverse proxy, and it enforces the `client_max_body_size` limit before the request even reaches your backend

## Additional Notes

- The limit applies to the entire request body, including multipart form data
- Mobile photos are often 3-8MB, but high-resolution photos can be 10-15MB+
- 20MB provides a comfortable buffer for most mobile uploads
- If you need to support very large files (e.g., 50MB+), consider implementing chunked uploads or resizing images on the client side


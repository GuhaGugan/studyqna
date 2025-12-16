# IP Address Testing Guide

## Why You See `127.0.0.1` (Localhost)

When testing locally, you'll see `127.0.0.1` because:
- **Localhost access**: If you access `http://localhost:3000` or `http://127.0.0.1:3000`, the IP will always be `127.0.0.1`
- **This is correct behavior** - the client IS localhost

## How to Get Real IP Addresses

### Option 1: Access via Network IP (Recommended for Testing)

1. **Find your computer's IP address:**
   ```bash
   # Windows
   ipconfig
   # Look for "IPv4 Address" (e.g., 192.168.1.100)
   
   # Mac/Linux
   ifconfig
   # Look for inet address (e.g., 192.168.1.100)
   ```

2. **Access the app using your network IP:**
   - Frontend: `http://192.168.1.100:3000` (replace with your IP)
   - Backend: `http://192.168.1.100:8000` (replace with your IP)

3. **Update frontend API base URL** (if needed):
   - In `frontend/src/utils/api.js`, change `API_BASE` to use your network IP
   - Or use environment variable

4. **Test from mobile device:**
   - Connect mobile to same WiFi network
   - Access: `http://192.168.1.100:3000`
   - Now you'll see the mobile device's IP address (usually `192.168.1.XXX`)

### Option 2: Use ngrok or Similar (For External Testing)

1. **Install ngrok:**
   ```bash
   npm install -g ngrok
   # or download from ngrok.com
   ```

2. **Expose your backend:**
   ```bash
   ngrok http 8000
   ```

3. **Update frontend to use ngrok URL**

4. **Now external IPs will be captured**

## What IP Headers Are Checked

The system checks IP addresses in this priority order:

1. **X-Forwarded-For** - Most common for proxies/load balancers
2. **X-Real-IP** - Nginx proxy header
3. **CF-Connecting-IP** - Cloudflare header
4. **True-Client-IP** - Some CDNs/proxies
5. **Direct client IP** - Fallback to request.client.host

## Debugging

Check your backend console logs when a user logs in. You'll see:
```
🔍 Login from user: user@example.com
📡 IP Detection Debug:
   - X-Forwarded-For: None
   - X-Real-IP: None
   - CF-Connecting-IP: None
   - True-Client-IP: None
   - Direct client: 192.168.1.50
   - Final IP: 192.168.1.50
   - Device: mobile
```

## Production Deployment

In production (with proper proxy/load balancer):
- IP addresses will be correctly captured from headers
- `X-Forwarded-For` will contain the real client IP
- Localhost IPs won't appear (unless someone accesses via localhost)

## Quick Test

1. **Start backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm run dev -- --host 0.0.0.0
   ```

3. **Find your IP:**
   ```bash
   # Windows
   ipconfig | findstr IPv4
   ```

4. **Access from mobile:**
   - Open `http://YOUR_IP:3000` on mobile
   - Login
   - Check admin dashboard - you should see mobile's IP (not 127.0.0.1)

## Notes

- **Localhost = 127.0.0.1**: This is expected when testing locally
- **Network IP**: Use your computer's network IP to test from other devices
- **Production**: Real IPs will be captured automatically via proxy headers



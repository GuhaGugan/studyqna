# Mobile Access Setup Guide

This guide explains how to access your StudyQnA application from a mobile device on the same network.

## Prerequisites

1. **Both devices must be on the same Wi-Fi network**
2. **Windows Firewall must allow connections on ports 3000 and 8000**

## Step 1: Find Your Computer's IP Address

### Windows:
1. Open Command Prompt or PowerShell
2. Run: `ipconfig`
3. Look for "IPv4 Address" under your active network adapter (usually Wi-Fi or Ethernet)
4. Example: `192.168.1.100` or `10.0.0.5`

### Alternative (Quick Method):
```bash
ipconfig | findstr /i "IPv4"
```

## Step 2: Update Frontend Configuration

The `vite.config.js` has been updated to allow external connections. Make sure it includes:

```javascript
server: {
  port: 3000,
  host: '0.0.0.0', // This allows mobile access
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## Step 3: Configure Windows Firewall

### Allow Ports 3000 and 8000:

1. **Open Windows Defender Firewall:**
   - Press `Win + R`, type `wf.msc`, press Enter

2. **Create Inbound Rules:**
   - Click "Inbound Rules" → "New Rule"
   - Select "Port" → Next
   - Select "TCP" → Enter port `3000` → Next
   - Select "Allow the connection" → Next
   - Check all profiles (Domain, Private, Public) → Next
   - Name: "StudyQnA Frontend" → Finish

3. **Repeat for port 8000:**
   - Same steps, but use port `8000`
   - Name: "StudyQnA Backend"

### Quick PowerShell Method (Run as Administrator):
```powershell
# Allow port 3000 (Frontend)
New-NetFirewallRule -DisplayName "StudyQnA Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow

# Allow port 8000 (Backend)
New-NetFirewallRule -DisplayName "StudyQnA Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

## Step 4: Start the Servers

### Backend (Terminal 1):
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

**Important:** Both servers must use `--host 0.0.0.0` (backend) and `host: '0.0.0.0'` (frontend) to accept external connections.

## Step 5: Access from Mobile

1. **Make sure your mobile device is on the same Wi-Fi network**

2. **Open a browser on your mobile device**

3. **Enter your computer's IP address with port 3000:**
   ```
   http://192.168.1.100:3000
   ```
   (Replace `192.168.1.100` with your actual IP address)

4. **The app should load on your mobile device!**

## Troubleshooting

### Can't access from mobile?

1. **Check IP Address:**
   - Make sure you're using the correct IP (not `127.0.0.1` or `localhost`)
   - Verify both devices are on the same network

2. **Check Firewall:**
   - Temporarily disable Windows Firewall to test
   - If it works, re-enable and add the rules properly

3. **Check Server Logs:**
   - Backend should show: `INFO: Uvicorn running on http://0.0.0.0:8000`
   - Frontend should show: `Local: http://localhost:3000/` and `Network: http://192.168.x.x:3000/`

4. **Test Backend Directly:**
   - From mobile, try: `http://YOUR_IP:8000/docs`
   - Should show the API documentation

5. **Check Network:**
   - Some networks block device-to-device communication
   - Try a different Wi-Fi network if possible
   - Mobile hotspot might not work (devices may be isolated)

### Still not working?

1. **Ping test from mobile:**
   - Install a network tool app
   - Try to ping your computer's IP address

2. **Check router settings:**
   - Some routers have "AP Isolation" enabled
   - Disable it to allow device-to-device communication

3. **Use ngrok for external access (alternative):**
   ```bash
   # Install ngrok: https://ngrok.com/
   ngrok http 3000
   ```
   This creates a public URL that works from anywhere (not just local network)

## Security Notes

⚠️ **Important Security Considerations:**

1. **Local Network Only:** The `0.0.0.0` binding makes your server accessible to anyone on your local network. This is fine for development/testing.

2. **Production Deployment:** For production, use proper hosting (AWS, Heroku, etc.) with HTTPS and authentication.

3. **Firewall:** Keep Windows Firewall enabled and only allow necessary ports.

## Quick Reference

- **Backend URL:** `http://YOUR_IP:8000`
- **Frontend URL:** `http://YOUR_IP:3000`
- **API Docs:** `http://YOUR_IP:8000/docs`
- **Find IP:** `ipconfig` (Windows) or `ifconfig` (Linux/Mac)



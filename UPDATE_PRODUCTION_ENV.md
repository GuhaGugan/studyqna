# Update Production Server Environment Variables

## Issue
Production server is showing different limits than localhost:
- **Production**: Daily 50 / Total 700
- **Localhost**: Daily 60 / Total 800

## Solution
Update the production server's `.env` file to match the correct values.

## Steps to Update Production Server

### 1. SSH into Production Server
```bash
ssh studyqna@your-server-ip
# or
ssh ubuntu@your-server-ip
```

### 2. Navigate to Backend Directory
```bash
cd ~/studyqna-assistant/backend
# or wherever your backend is located
```

### 3. Edit .env File
```bash
nano .env
# or
vi .env
```

### 4. Update These Variables
Find and update these lines in the `.env` file:

```env
# Daily Generation Limit (Premium Users)
PREMIUM_DAILY_GENERATION_LIMIT=60

# Total Questions Limit (Premium Users)
PREMIUM_TOTAL_QUESTIONS_LIMIT=700

# Max Questions Per Generation
# Note: This is in config.py, but if you have it in .env, update it:
# MAX_QUESTIONS_PER_GENERATE=15
```

**Important Values:**
- `PREMIUM_DAILY_GENERATION_LIMIT=60` (not 50)
- `PREMIUM_TOTAL_QUESTIONS_LIMIT=700` (correct, but ensure it's set)
- If `MAX_QUESTIONS_PER_GENERATE` is in `.env`, set it to `15`

### 5. Save and Exit
- **Nano**: Press `Ctrl+X`, then `Y`, then `Enter`
- **Vi**: Press `Esc`, type `:wq`, then `Enter`

### 6. Restart Backend Service
```bash
# If using systemd:
sudo systemctl restart studyqna-backend

# If using PM2:
pm2 restart studyqna-backend

# If running manually, stop and restart:
# Stop: Ctrl+C or kill the process
# Start: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. Verify Changes
1. Check backend logs to ensure it started correctly:
   ```bash
   sudo journalctl -u studyqna-backend -f
   # or
   pm2 logs studyqna-backend
   ```

2. Refresh the production dashboard and verify:
   - Daily Questions: Should show **60** (not 50)
   - Total Questions: Should show **700** (correct)

## Current Code Defaults (config.py)
These are the defaults in the code. If not set in `.env`, these will be used:
- `PREMIUM_DAILY_GENERATION_LIMIT: 60`
- `PREMIUM_TOTAL_QUESTIONS_LIMIT: 700`
- `MAX_QUESTIONS_PER_GENERATE: 15`

## Troubleshooting

### If limits still don't match:
1. **Check if environment variables are set elsewhere:**
   ```bash
   # Check systemd service file
   sudo nano /etc/systemd/system/studyqna-backend.service
   # Look for Environment= lines
   ```

2. **Check if PM2 has environment variables:**
   ```bash
   pm2 show studyqna-backend
   # Look for env section
   ```

3. **Verify .env file is being loaded:**
   ```bash
   # In backend directory
   python -c "from app.config import settings; print(f'Daily: {settings.PREMIUM_DAILY_GENERATION_LIMIT}, Total: {settings.PREMIUM_TOTAL_QUESTIONS_LIMIT}')"
   ```

### If you need to set environment variables in systemd:
Edit the service file:
```bash
sudo nano /etc/systemd/system/studyqna-backend.service
```

Add under `[Service]`:
```ini
Environment="PREMIUM_DAILY_GENERATION_LIMIT=60"
Environment="PREMIUM_TOTAL_QUESTIONS_LIMIT=700"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart studyqna-backend
```

## Summary
- **Daily Limit**: Update from 50 → **60**
- **Total Limit**: Ensure it's set to **700** (should already be correct)
- **Per Generation**: Ensure it's **15** (updated in code)

After updating, restart the backend service and verify the dashboard shows the correct limits.


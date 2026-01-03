# Fix: Port 8000 Already in Use

## Issue: `[Errno 98] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`

This means either:
1. The systemd service is already running
2. Another process is using port 8000

---

## Solution 1: Check if Service is Running

```bash
# Check service status
sudo systemctl status studyqna-backend

# If it's running, that's good! The service is working.
# You don't need to run uvicorn manually.
```

---

## Solution 2: If Service is Not Running, Check What's Using Port 8000

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Or
sudo netstat -tlnp | grep 8000

# Kill the process if needed
sudo kill -9 <PID>
```

---

## Solution 3: Restart the Service

```bash
# Stop the service
sudo systemctl stop studyqna-backend

# Start it again
sudo systemctl start studyqna-backend

# Check status
sudo systemctl status studyqna-backend
```

---

## Solution 4: If Service is Running but Not Working

```bash
# Check service logs
sudo journalctl -u studyqna-backend -f

# Restart service
sudo systemctl restart studyqna-backend

# Check status
sudo systemctl status studyqna-backend
```

---

## ✅ Success Indicators:

When the service is running correctly, you should see:
- `Active: active (running)`
- No error messages in status
- Backend accessible at `http://127.0.0.1:8000`

---

## Test Backend:

```bash
# Test if backend is responding
curl http://127.0.0.1:8000/health

# Should return: {"status":"healthy"}
```





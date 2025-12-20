# Complete Deployment Steps - After File Copy

You've successfully copied the files. Now complete these steps on the production server:

## Step 1: SSH into Production Server

```bash
ssh -i "G:\LightsailDefaultKey-ap-south-1.pem" ubuntu@13.200.124.120
```

## Step 2: Move Frontend Files to Correct Location

```bash
# Check where Nginx is serving from
sudo cat /etc/nginx/sites-available/studyqna | grep root
# Common locations:
# - /home/ubuntu/studyqna-assistant/frontend/dist
# - /var/www/studyqna/dist
# - /home/studyqna/studyqna-assistant/frontend/dist

# Move files from /tmp to actual location
# Replace PATH with your actual Nginx root path
sudo mv /tmp/studyqna-frontend/* /home/ubuntu/studyqna-assistant/frontend/dist/
# or
sudo mv /tmp/studyqna-frontend/* /var/www/studyqna/dist/

# Set correct permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/studyqna-assistant/frontend/dist/
# or
sudo chown -R www-data:www-data /var/www/studyqna/dist/
```

## Step 3: Update .env File

```bash
cd /home/ubuntu/studyqna/backend
# or
cd /home/ubuntu/studyqna-assistant/backend

# Edit .env file
nano .env
# or
vi .env
```

**Add or update these lines:**
```env
PREMIUM_DAILY_GENERATION_LIMIT=60
PREMIUM_TOTAL_QUESTIONS_LIMIT=700
```

**Save and exit:**
- Nano: `Ctrl+X`, then `Y`, then `Enter`
- Vi: `Esc`, type `:wq`, then `Enter`

## Step 4: Run Database Migration for Credit Requests

```bash
cd /home/ubuntu/studyqna/backend
# or
cd /home/ubuntu/studyqna-assistant/backend

# Activate virtual environment
source venv/bin/activate
# or if venv is in different location:
# source ~/venv/bin/activate

# Run migration
python migrations/run_credit_request_migration_standalone.py
```

**Expected output:**
```
✅ Migration completed successfully!
✅ Added bonus_questions column to users table
✅ Created credit_requests table
✅ Created indexes
```

**If migration script doesn't exist, run SQL directly:**
```bash
# First, copy migration SQL file if needed
# Then run:
psql -U studyqna_user -d studyqna -f migrations/add_credit_request_feature.sql
```

## Step 5: Restart Backend Service

```bash
# Check which service manager is used
sudo systemctl status studyqna-backend
# or
pm2 status

# Restart backend
sudo systemctl restart studyqna-backend
# or
pm2 restart studyqna-backend

# Verify it's running
sudo systemctl status studyqna-backend
# or
pm2 status
```

## Step 6: Reload Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx

# Or restart if needed
sudo systemctl restart nginx
```

## Step 7: Verify Deployment

### Check Backend Logs
```bash
# View recent logs
sudo journalctl -u studyqna-backend -n 50 --no-pager
# or
pm2 logs studyqna-backend --lines 50
```

### Check if Backend is Responding
```bash
curl http://localhost:8000/api/health
# or
curl http://localhost:8000/docs
```

### Verify Database Migration
```bash
# Check if credit_requests table exists
psql -U studyqna_user -d studyqna -c "\d credit_requests"

# Check if bonus_questions column exists
psql -U studyqna_user -d studyqna -c "\d users" | grep bonus_questions
```

### Test Frontend
1. Open your production URL: `https://app.gugancloud.co.in` or `http://13.200.124.120`
2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Check:
   - Daily Questions shows **60** (not 50)
   - Total Questions shows **700**
   - "Request More Credits" button appears when questions ≤ 50
   - All features work correctly

## Quick One-Liner Commands

### If using systemd:
```bash
cd /home/ubuntu/studyqna/backend && \
source venv/bin/activate && \
python migrations/run_credit_request_migration_standalone.py && \
sudo systemctl restart studyqna-backend && \
sudo systemctl reload nginx && \
echo "✅ Deployment complete!"
```

### If using PM2:
```bash
cd /home/ubuntu/studyqna/backend && \
source venv/bin/activate && \
python migrations/run_credit_request_migration_standalone.py && \
pm2 restart studyqna-backend && \
sudo systemctl reload nginx && \
echo "✅ Deployment complete!"
```

## Troubleshooting

### If backend won't start:
```bash
# Check logs for errors
sudo journalctl -u studyqna-backend -n 100

# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Check Python version
python --version
# Should be 3.8+

# Check if dependencies are installed
source venv/bin/activate
pip list | grep fastapi
```

### If migration fails:
```bash
# Check database connection
psql -U studyqna_user -d studyqna -c "SELECT 1;"

# Check if table already exists
psql -U studyqna_user -d studyqna -c "\d credit_requests"

# If table exists, migration already ran - that's OK!
```

### If frontend not updating:
```bash
# Check Nginx root path
sudo cat /etc/nginx/sites-available/studyqna | grep root

# Verify files are in correct location
ls -la /home/ubuntu/studyqna-assistant/frontend/dist/

# Check file permissions
ls -la /home/ubuntu/studyqna-assistant/frontend/dist/index.html

# Clear Nginx cache
sudo systemctl restart nginx
```

## Summary

**What you've done:**
✅ Copied frontend dist files to `/tmp/studyqna-frontend/`
✅ Copied backend app files to `/home/ubuntu/studyqna/backend/app/`

**What you need to do:**
1. ✅ Move frontend files from `/tmp` to actual Nginx root
2. ✅ Update `.env` file with `PREMIUM_DAILY_GENERATION_LIMIT=60`
3. ✅ Run database migration for credit requests
4. ✅ Restart backend service
5. ✅ Reload Nginx
6. ✅ Verify everything works

**Expected result:**
- Daily Questions: **60** ✅
- Total Questions: **700** ✅
- "Request More Credits" button visible ✅
- Credit request feature working ✅


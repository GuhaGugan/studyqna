# 🔧 Fix PostgreSQL Password Authentication Error

## Problem
```
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: 
FATAL: password authentication failed for user "studyqna_user"
```

## Solution: Reset Database User Password

### **Option 1: Reset Password (Recommended)**

```bash
# Connect as postgres superuser
sudo -u postgres psql

# In PostgreSQL shell, run:
ALTER USER studyqna_user WITH PASSWORD 'YOUR_NEW_SECURE_PASSWORD';

# Exit PostgreSQL
\q
```

**Then update your .env file:**
```bash
cd ~/studyqna/backend
nano .env
```

**Update DATABASE_URL:**
```env
DATABASE_URL=postgresql://studyqna_user:YOUR_NEW_SECURE_PASSWORD@localhost:5432/studyqna
```

**Save and test:**
```bash
# Test connection
psql -U studyqna_user -d studyqna -h localhost
# Enter the new password when prompted
```

---

### **Option 2: Recreate Database User (If Option 1 doesn't work)**

```bash
# Connect as postgres superuser
sudo -u postgres psql

# In PostgreSQL shell, run:
-- Drop existing user (if exists)
DROP USER IF EXISTS studyqna_user;

-- Create new user with password
CREATE USER studyqna_user WITH PASSWORD 'YOUR_SECURE_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;

-- Grant schema privileges (important!)
\c studyqna
GRANT ALL ON SCHEMA public TO studyqna_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO studyqna_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO studyqna_user;

-- Exit
\q
```

**Then update .env file and test connection.**

---

### **Option 3: Check if User Exists**

```bash
# Connect as postgres
sudo -u postgres psql

# List all users
\du

# Check if studyqna_user exists
# If not, create it using Option 2
```

---

## Quick Fix Commands

**Run these commands on your server:**

```bash
# 1. Set a new password (replace 'YourNewPassword123!' with your desired password)
sudo -u postgres psql -c "ALTER USER studyqna_user WITH PASSWORD 'YourNewPassword123!';"

# 2. Update .env file
cd ~/studyqna/backend
nano .env

# 3. Update this line in .env:
# DATABASE_URL=postgresql://studyqna_user:YourNewPassword123!@localhost:5432/studyqna

# 4. Test connection
psql -U studyqna_user -d studyqna -h localhost
# Enter: <YOUR_NEW_PASSWORD>
```

---

## Verify Database Setup

```bash
# Check if database exists
sudo -u postgres psql -l | grep studyqna

# Check if user exists
sudo -u postgres psql -c "\du" | grep studyqna_user

# Test connection with new password
psql -U studyqna_user -d studyqna -h localhost
```

---

## Common Issues

### **Issue 1: User doesn't exist**
```bash
# Create user
sudo -u postgres psql -c "CREATE USER studyqna_user WITH PASSWORD 'YourPassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;"
```

### **Issue 2: Database doesn't exist**
```bash
# Create database
sudo -u postgres psql -c "CREATE DATABASE studyqna;"
```

### **Issue 3: Permission denied**
```bash
# Grant schema privileges
sudo -u postgres psql -d studyqna -c "GRANT ALL ON SCHEMA public TO studyqna_user;"
```

---

## Complete Database Setup (Fresh Start)

If you want to start fresh:

```bash
# Connect as postgres
sudo -u postgres psql

# Run these commands:
DROP DATABASE IF EXISTS studyqna;
DROP USER IF EXISTS studyqna_user;

CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD '<YOUR_NEW_PASSWORD>
';
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;

\c studyqna
GRANT ALL ON SCHEMA public TO studyqna_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO studyqna_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO studyqna_user;

\q
```

**Then update .env:**
```env
DATABASE_URL=postgresql://studyqna_user:<YOUR_NEW_PASSWORD>
@localhost:5432/studyqna
```

---

## After Fixing Password

1. **Update .env file** with correct password
2. **Test connection:**
   ```bash
   psql -U studyqna_user -d studyqna -h localhost
   ```
3. **Initialize database:**
   ```bash
   cd ~/studyqna/backend
   source venv/bin/activate
   python init_db.py
   ```
4. **Restart backend service:**
   ```bash
   sudo systemctl restart studyqna-backend
   ```

---

**Need help?** Check the connection with:
```bash
sudo systemctl status postgresql
```


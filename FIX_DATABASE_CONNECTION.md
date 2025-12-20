# Fix Database Connection Error

## Problem
The migration script is failing because your `DATABASE_URL` in `.env` file is incorrect or missing.

Error: `password authentication failed for user "user"`

This means the `.env` file is using placeholder/default values instead of your actual database credentials.

## Solution

### Step 1: Check if .env file exists

Navigate to: `backend/.env`

If it doesn't exist, create it:
```bash
# Copy the template
copy backend\ENV_TEMPLATE.txt backend\.env
```

### Step 2: Edit the .env file

Open `backend/.env` in a text editor and find this line:

```env
DATABASE_URL=postgresql://studyqna_user:your_secure_password_here@localhost:5432/studyqna
```

**Replace it with your actual database credentials:**

```env
DATABASE_URL=postgresql://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE
```

**Example:**
```env
DATABASE_URL=postgresql://postgres:mypassword123@localhost:5432/studyqna_db
```

### Step 3: Find Your Database Credentials

If you don't know your database credentials, check:

1. **If you set up PostgreSQL yourself:**
   - Username: Usually `postgres` or the user you created
   - Password: The password you set during PostgreSQL installation
   - Database: The database name you created (e.g., `studyqna`, `studyqna_db`)

2. **If using the installation script:**
   - Check the script output or logs
   - Username: Usually `studyqna_user`
   - Password: The password you provided during installation
   - Database: Usually `studyqna` or `studyqna_db`

3. **If you forgot the password:**
   - You can reset it (see below)

### Step 4: Test the Connection

Run this command to check if your connection works:

```bash
python backend/migrations/check_database_connection.py
```

### Step 5: Run the Migration

Once the connection works, run:

```bash
python backend/migrations/run_credit_request_migration.py
```

---

## Alternative: Reset PostgreSQL Password

If you need to reset your PostgreSQL password:

### Windows:

1. **Open Command Prompt as Administrator**

2. **Stop PostgreSQL service:**
   ```cmd
   net stop postgresql-x64-XX
   ```
   (Replace XX with your PostgreSQL version number)

3. **Start PostgreSQL in single-user mode:**
   ```cmd
   "C:\Program Files\PostgreSQL\XX\bin\pg_ctl.exe" -D "C:\Program Files\PostgreSQL\XX\data" -o "-p 5432" start
   ```

4. **Connect and reset password:**
   ```cmd
   "C:\Program Files\PostgreSQL\XX\bin\psql.exe" -U postgres
   ```
   Then in psql:
   ```sql
   ALTER USER your_username WITH PASSWORD 'new_password';
   \q
   ```

### Linux/Mac:

1. **Edit pg_hba.conf** to allow local connections without password temporarily
2. **Restart PostgreSQL**
3. **Connect and reset:**
   ```bash
   psql -U postgres
   ALTER USER your_username WITH PASSWORD 'new_password';
   ```

---

## Quick Fix: Use psql Directly

If you know your database credentials, you can run the migration directly using psql:

```bash
psql -U your_username -d your_database -f backend/migrations/add_credit_request_feature.sql
```

You'll be prompted for the password.

---

## Verify .env File Format

Your `DATABASE_URL` should look like this:

```
postgresql://username:password@host:port/database
```

**Correct Examples:**
- `postgresql://postgres:mypass@localhost:5432/studyqna`
- `postgresql://studyqna_user:secure123@localhost:5432/studyqna_db`

**Wrong Examples:**
- `postgresql://user:password@localhost:5432/studyqna` ❌ (placeholder values)
- `postgresql://user@localhost:5432/studyqna` ❌ (missing password)
- `DATABASE_URL=postgresql://...` ❌ (don't include "DATABASE_URL=" in the URL itself)

---

## Still Having Issues?

1. **Check PostgreSQL is running:**
   ```bash
   # Windows
   net start postgresql-x64-XX
   
   # Linux
   sudo systemctl status postgresql
   ```

2. **Test connection manually:**
   ```bash
   psql -U your_username -d your_database -h localhost
   ```

3. **Check if database exists:**
   ```sql
   \l  -- List all databases
   ```

4. **Verify user exists:**
   ```sql
   \du  -- List all users
   ```


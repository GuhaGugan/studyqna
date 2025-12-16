# PostgreSQL Setup with pgAdmin (Windows)

Complete guide for setting up PostgreSQL database using pgAdmin desktop tool on Windows.

## Prerequisites

- PostgreSQL installed on Windows
- pgAdmin installed (comes with PostgreSQL installer)
- Admin access to your Windows machine

---

## Step 1: Install PostgreSQL (if not already installed)

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run the installer
3. During installation:
   - **Port**: Keep default (5432)
   - **Superuser password**: Set a strong password for `postgres` user (remember this!)
   - **Locale**: Keep default
4. Complete the installation
5. pgAdmin will be installed automatically

---

## Step 2: Launch pgAdmin

1. Open **pgAdmin** from Start Menu
2. You'll see the pgAdmin interface
3. Enter your **master password** (this is for pgAdmin itself, set during first launch)
   - This is different from the postgres database password
   - You can set it to be the same for convenience

---

## Step 3: Connect to PostgreSQL Server

1. In the left panel (Object Explorer), you'll see:
   ```
   Servers
     └── PostgreSQL [version] (e.g., PostgreSQL 15)
   ```

2. **Expand "Servers"** by clicking the arrow

3. **Click on "PostgreSQL [version]"**
   - If it shows a lock icon 🔒, it means you need to connect
   - If prompted, enter the **postgres user password** (set during installation)

4. **Right-click on "PostgreSQL [version]"** → **"Connect Server"**
   - Enter password if prompted
   - The lock icon should disappear when connected

---

## Step 4: Create Database

1. **Expand "PostgreSQL [version]"** (click the arrow)

2. **Right-click on "Databases"** → **"Create"** → **"Database..."**

3. In the **"General"** tab:
   - **Database**: `studyqna`
   - **Owner**: Leave as default (postgres) or select from dropdown
   - **Comment**: (Optional) "StudyQnA Generator Database"

4. Click **"Save"** button at the bottom

5. You should now see `studyqna` database in the list

---

## Step 5: Create Database User

1. **Expand "PostgreSQL [version]"** in the left panel

2. **Expand "Login/Group Roles"**

3. **Right-click on "Login/Group Roles"** → **"Create"** → **"Login/Group Role..."**

4. In the **"General"** tab:
   - **Name**: `studyqna_user`
   - **Comment**: (Optional) "StudyQnA application user"

5. In the **"Definition"** tab:
   - **Password**: Enter a strong password (e.g., `SecurePass123!`)
   - **Password expiration**: Leave **unchecked**
   - **Connection limit**: Leave as `-1` (unlimited)

6. In the **"Privileges"** tab:
   - Check **"Can login?"** ✅
   - Leave other options unchecked

7. Click **"Save"** button

8. You should now see `studyqna_user` in the Login/Group Roles list

---

## Step 6: Grant Database Privileges

1. **Expand "Databases"** → **"studyqna"**

2. **Right-click on "studyqna"** → **"Properties"**

3. Go to **"Security"** tab

4. Click **"Add"** button (➕)

5. In the new row:
   - **Grantee**: Select `studyqna_user` from dropdown
   - **Privileges**: Check **"ALL"** ✅
   - Or individually check: SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER

6. Click **"Save"** button

---

## Step 7: Grant Schema Privileges (IMPORTANT!)

1. **Expand "studyqna"** database

2. **Expand "Schemas"**

3. **Expand "public"** schema

4. **Right-click on "public"** → **"Properties"**

5. Go to **"Security"** tab

6. Click **"Add"** button (➕)

7. In the new row:
   - **Grantee**: Select `studyqna_user` from dropdown
   - **Privileges**: Check **"ALL"** ✅
   - Or individually check: CREATE, USAGE

8. Click **"Save"** button

---

## Step 8: Verify Setup

### Test Connection from pgAdmin:

1. **Right-click on "studyqna"** database → **"Query Tool"**

2. In the query editor, type:
   ```sql
   SELECT current_database(), current_user;
   ```

3. Click **"Execute"** button (▶️) or press F5

4. You should see:
   ```
   current_database | current_user
   -----------------+---------------
   studyqna        | postgres
   ```

### Test with studyqna_user:

1. **Right-click on "PostgreSQL [version]"** → **"Disconnect Server"**

2. **Right-click on "PostgreSQL [version]"** → **"Properties"**

3. Go to **"Connection"** tab

4. Change:
   - **Username**: `studyqna_user`
   - **Password**: (enter the password you set)

5. Click **"Save"**

6. **Right-click on "PostgreSQL [version]"** → **"Connect Server"**

7. Try to expand "studyqna" database - it should work!

---

## Step 9: Update .env File

Now update your backend `.env` file with the database connection:

```env
DATABASE_URL=postgresql://studyqna_user:SecurePass123!@localhost:5432/studyqna
```

**Format:**
```
postgresql://username:password@host:port/database
```

**Example:**
- Username: `studyqna_user`
- Password: `SecurePass123!` (your password)
- Host: `localhost`
- Port: `5432` (default)
- Database: `studyqna`

---

## Visual Guide

### pgAdmin Interface Overview:

```
pgAdmin 4
├── Servers
│   └── PostgreSQL 15
│       ├── Databases
│       │   └── studyqna  ← Your database
│       ├── Login/Group Roles
│       │   └── studyqna_user  ← Your user
│       └── ...
```

### Quick Access:

- **Query Tool**: Right-click database → "Query Tool"
- **Properties**: Right-click any object → "Properties"
- **Refresh**: Right-click → "Refresh" (if changes not visible)

---

## Troubleshooting

### Problem: Can't connect to server
**Solution:**
- Check PostgreSQL service is running:
  - Open Services (Win + R → `services.msc`)
  - Find "postgresql-x64-[version]"
  - Ensure it's "Running"
  - If not, right-click → "Start"

### Problem: "Password authentication failed"
**Solution:**
- Verify you're using the correct password
- Check if user exists: Login/Group Roles → studyqna_user
- Reset password: Right-click user → Properties → Definition tab

### Problem: "Permission denied" errors
**Solution:**
- Ensure you granted ALL privileges on database (Step 6)
- Ensure you granted ALL privileges on public schema (Step 7)
- Try reconnecting with postgres user and re-granting

### Problem: Can't see studyqna database
**Solution:**
- Click "Refresh" button (🔄) in pgAdmin toolbar
- Or right-click "Databases" → "Refresh"

### Problem: Query Tool shows "permission denied"
**Solution:**
- Make sure you granted schema privileges (Step 7)
- Try reconnecting with postgres user
- Re-run Step 6 and Step 7

---

## Next Steps

After completing this setup:

1. ✅ Database created: `studyqna`
2. ✅ User created: `studyqna_user`
3. ✅ Privileges granted
4. ✅ Update `.env` file with connection string
5. ✅ Run `python init_db.py` to create tables
6. ✅ Start backend server

---

## Quick Reference

**Database Name:** `studyqna`  
**Username:** `studyqna_user`  
**Password:** (the one you set in Step 5)  
**Host:** `localhost`  
**Port:** `5432`  

**Connection String Format:**
```
postgresql://studyqna_user:YOUR_PASSWORD@localhost:5432/studyqna
```

---

## Additional Resources

- pgAdmin Documentation: https://www.pgadmin.org/docs/
- PostgreSQL Windows Guide: https://www.postgresql.org/docs/current/installation-windows.html
- Connection String Format: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING



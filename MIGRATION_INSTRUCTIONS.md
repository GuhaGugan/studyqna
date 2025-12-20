# How to Run Credit Request Feature Migration

## Method 1: Using Python Script (Recommended - Easiest)

This method uses your existing database connection from `.env` file.

### Steps:
1. **Activate your virtual environment** (if using one):
   ```bash
   # Windows
   backend\venv\Scripts\activate
   
   # Linux/Mac
   source backend/venv/bin/activate
   ```

2. **Navigate to project root**:
   ```bash
   cd "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant"
   ```

3. **Run the Python migration script**:
   ```bash
   python backend/migrations/run_credit_request_migration.py
   ```

This will automatically:
- Use your database connection from `.env` file
- Add the `bonus_questions` column
- Create the `credit_requests` table
- Create necessary indexes

---

## Method 2: Using psql Command Line (Direct Database Access)

### For Windows:

1. **Open Command Prompt or PowerShell**

2. **Navigate to project directory**:
   ```cmd
   cd "G:\GUGAN_PROJECTS\AI_PROJECTS\ATS_Resume_analyser\StudyQnA Assistant"
   ```

3. **Run psql command**:
   ```cmd
   psql -U your_database_user -d your_database_name -f backend/migrations/add_credit_request_feature.sql
   ```

   **Replace:**
   - `your_database_user` - Your PostgreSQL username (e.g., `studyqna_user`)
   - `your_database_name` - Your database name (e.g., `studyqna_db`)

   **Example:**
   ```cmd
   psql -U studyqna_user -d studyqna_db -f backend/migrations/add_credit_request_feature.sql
   ```

4. **Enter password when prompted**

### For Linux/Mac:

1. **Open Terminal**

2. **Navigate to project directory**:
   ```bash
   cd /path/to/StudyQnA\ Assistant
   ```

3. **Run psql command**:
   ```bash
   psql -U your_database_user -d your_database_name -f backend/migrations/add_credit_request_feature.sql
   ```

   **Example:**
   ```bash
   psql -U studyqna_user -d studyqna_db -f backend/migrations/add_credit_request_feature.sql
   ```

---

## Method 3: Using pgAdmin (GUI Method)

1. **Open pgAdmin**

2. **Connect to your database**

3. **Right-click on your database** → **Query Tool**

4. **Open the migration file**:
   - File → Open → Select `backend/migrations/add_credit_request_feature.sql`

5. **Click Execute (F5)** or press **F5**

---

## Method 4: Copy-Paste SQL (If psql not available)

1. **Open the migration file**:
   ```
   backend/migrations/add_credit_request_feature.sql
   ```

2. **Copy all SQL statements**

3. **Connect to your database** using any PostgreSQL client:
   - pgAdmin
   - DBeaver
   - psql
   - Any database GUI tool

4. **Paste and execute** the SQL statements

---

## Finding Your Database Credentials

Your database credentials are in your `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

**Extract:**
- **Username**: Part before `:` after `postgresql://`
- **Password**: Part after `:` and before `@`
- **Database**: Part after last `/`
- **Host**: Part between `@` and `:`
- **Port**: Part between `:` and `/` (usually 5432)

**Example:**
```
DATABASE_URL=postgresql://studyqna_user:mypassword@localhost:5432/studyqna_db
```
- Username: `studyqna_user`
- Password: `mypassword`
- Database: `studyqna_db`
- Host: `localhost`
- Port: `5432`

---

## Verification

After running the migration, verify it worked:

### Using Python:
```python
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if bonus_questions column exists
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='bonus_questions'
    """))
    if result.fetchone():
        print("✅ bonus_questions column exists")
    
    # Check if credit_requests table exists
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name='credit_requests'
    """))
    if result.fetchone():
        print("✅ credit_requests table exists")
```

### Using psql:
```sql
-- Check column
\d users

-- Check table
\dt credit_requests
```

---

## Troubleshooting

### Error: "psql: command not found"
**Solution**: Install PostgreSQL client tools or use Method 1 (Python script)

### Error: "password authentication failed"
**Solution**: Check your `.env` file for correct password

### Error: "database does not exist"
**Solution**: Verify database name in `.env` file

### Error: "permission denied"
**Solution**: Ensure your database user has CREATE TABLE and ALTER TABLE permissions

### Error: "relation already exists"
**Solution**: This is okay! The migration uses `IF NOT EXISTS`, so it's safe to run multiple times

---

## Recommended Method

**Use Method 1 (Python script)** - It's the easiest and uses your existing database configuration automatically.

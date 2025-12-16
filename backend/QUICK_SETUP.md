# Quick Setup Guide

## Step 1: Create .env File

Run the setup script:

```bash
python setup_env.py
```

This will ask you for:
- Database username (default: studyqna_user)
- Database password (required)
- Database host (default: localhost)
- Database port (default: 5432)
- Database name (default: studyqna)
- Admin email
- OpenAI API key (optional for now)

## Step 2: Or Create .env Manually

Create a file named `.env` in the `backend/` directory with:

```env
DATABASE_URL=postgresql://studyqna_user:YOUR_PASSWORD@localhost:5432/studyqna
SECRET_KEY=your-generated-secret-key
ADMIN_EMAIL=your-email@example.com
OPENAI_API_KEY=sk-your-key-here
```

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 3: Initialize Database

```bash
python init_db.py
```

## Step 4: Start Server

```bash
python run.py
```

## Troubleshooting

### Error: "password authentication failed for user 'user'"

This means `.env` file is missing or not being read.

**Solution:**
1. Make sure `.env` file exists in `backend/` directory
2. Check that `DATABASE_URL` is correct
3. Verify database user and password match your PostgreSQL setup

### Check if .env exists:

```bash
dir .env
# Should show: .env
```

### Verify DATABASE_URL format:

```env
DATABASE_URL=postgresql://username:password@host:port/database
```

Example:
```env
DATABASE_URL=postgresql://studyqna_user:SecurePass123!@localhost:5432/studyqna
```



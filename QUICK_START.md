# Quick Start Guide - StudyQnA Generator

## Starting the Application

You need to run **both** the backend and frontend servers.

### Step 1: Start Backend Server

Open a **new terminal window** and run:

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already activated)
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Start the backend server
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal open!**

### Step 2: Start Frontend Server

Open **another terminal window** and run:

```bash
# Navigate to frontend directory
cd frontend

# Start the frontend development server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

### Step 3: Access the Application

Open your browser and go to:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Troubleshooting

### Error: "ECONNREFUSED" or "http proxy error"

**Problem**: Frontend can't connect to backend

**Solution**: 
1. Make sure the backend is running on port 8000
2. Check that you see `Uvicorn running on http://0.0.0.0:8000` in the backend terminal
3. Verify your `.env` file is configured correctly
4. Make sure the database is running (PostgreSQL)

### Backend won't start

**Check:**
1. Virtual environment is activated
2. All dependencies are installed: `pip install -r requirements.txt`
3. Database is running and `.env` has correct `DATABASE_URL`
4. Database tables are initialized: `python init_db.py`

### Port already in use

If port 8000 is already in use:
- Change port in `backend/run.py`: `port=8001`
- Update `frontend/vite.config.js`: `target: 'http://localhost:8001'`

## Running Both Servers

You need **TWO terminal windows**:

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Both must be running simultaneously for the application to work!

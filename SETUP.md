# Setup Instructions

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python init_db.py

# Run server
python run.py
# Or: uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Database Setup

1. Install PostgreSQL
2. Create database:
```sql
CREATE DATABASE studyqna;
```

3. Update `DATABASE_URL` in `backend/.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/studyqna
```

### 4. Required Services

- **PostgreSQL**: Database
- **OpenAI API Key**: For Q/A generation
- **SMTP Server**: For OTP emails (Gmail works)

### 5. Human Detection Setup

The app uses YOLO for human detection. On first run, it will download the model automatically.

For manual setup:
```bash
# Install ultralytics (already in requirements.txt)
pip install ultralytics

# Model will be downloaded automatically on first use
```

### 6. Storage Setup

Create storage directory:
```bash
mkdir -p storage/uploads
chmod 700 storage
```

Update `STORAGE_PATH` in `.env` to point to this directory.

## Configuration Checklist

- [ ] PostgreSQL database created
- [ ] Database URL configured in `.env`
- [ ] JWT secret key set (use a strong random key)
- [ ] Admin email configured
- [ ] SMTP credentials configured
- [ ] OpenAI API key configured
- [ ] Storage directory created with proper permissions
- [ ] Frontend API proxy configured (if needed)

## Testing

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev`
3. Visit: `http://localhost:3000`
4. Login with your admin email to test

## Troubleshooting

### Database Connection Error
- Check PostgreSQL is running
- Verify DATABASE_URL format
- Check user permissions

### Human Detection Not Working
- Install ultralytics: `pip install ultralytics`
- Model downloads automatically on first use
- Check internet connection for model download

### Email Not Sending
- Verify SMTP credentials
- Check firewall/network settings
- For Gmail, use App Password, not regular password

### File Upload Fails
- Check storage directory permissions
- Verify file size limits
- Check disk space



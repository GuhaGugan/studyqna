# Installation Summary - StudyQnA Generator

## 📋 Quick Reference

### 1. Database Setup
```sql
CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE studyqna TO studyqna_user;
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ENV_TEMPLATE.txt .env
# Edit .env with your values
python init_db.py
python run.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔑 Required .env Variables

### Minimum Required (to get started):
```env
DATABASE_URL=postgresql://studyqna_user:password@localhost:5432/studyqna
SECRET_KEY=<generate-with-python-command>
ADMIN_EMAIL=your-email@example.com
OPENAI_API_KEY=sk-your-key-here
```

### Full Configuration:
See `backend/ENV_TEMPLATE.txt` for complete list

---

## 📚 Documentation Files

1. **INSTALLATION_GUIDE.md** - Complete step-by-step installation
2. **QUICK_START.md** - Get running in 5 minutes
3. **SETUP.md** - Configuration details
4. **DEPLOYMENT.md** - Production deployment guide
5. **README.md** - Project overview

---

## ✅ Verification Checklist

After installation, verify:

- [ ] PostgreSQL database created and accessible
- [ ] Backend server starts on port 8000
- [ ] Frontend server starts on port 3000
- [ ] Can access http://localhost:3000
- [ ] Database tables created (check with `python init_db.py`)
- [ ] Storage directory exists with correct permissions
- [ ] .env file configured with all required values
- [ ] Can receive OTP emails (or check terminal for OTP in dev mode)
- [ ] Can login with admin email

---

## 🚀 Next Steps

1. Login with admin email
2. Test file upload
3. Generate sample Q/A
4. Review admin dashboard
5. Configure for production (see DEPLOYMENT.md)

---

## 🆘 Need Help?

- **Installation issues**: See INSTALLATION_GUIDE.md → Troubleshooting section
- **Configuration**: See SETUP.md
- **Production**: See DEPLOYMENT.md
- **Quick start**: See QUICK_START.md



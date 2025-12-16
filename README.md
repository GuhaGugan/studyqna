# StudyQnA Generator

A secure, production-ready web application for generating AI-powered questions and answers from PDFs and images.

## Features

- 🔐 **Secure Authentication**: OTP-based email login with JWT tokens
- 📄 **File Upload**: Support for PDFs and images with human detection
- 🤖 **AI Q/A Generation**: Multiple difficulty levels, question types, and output formats
- 💎 **Premium Access**: Request-based premium system with admin approval
- 📱 **Mobile Responsive**: Full mobile support with camera input (mobile only)
- 👨‍🏫 **Teacher Mode**: Chapter-wise Q/A generation
- 💾 **Saved Sets**: Store and download Q/A sets in multiple formats

## Tech Stack

- **Frontend**: React + Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: Local encrypted directory (Lightsail disk)

## Quick Start

### Running the Application

**IMPORTANT**: You need to run **both** backend and frontend servers in separate terminals!

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows (or: source venv/bin/activate on Linux/Mac)
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open http://localhost:3000 in your browser.

See [QUICK_START.md](QUICK_START.md) for detailed instructions.

## Quick Start (Old)

### Option 1: Docker (Recommended) 🐳

```bash
# Start database only
docker-compose up -d postgres

# Or start full stack
docker-compose -f docker-compose.full.yml up -d
```

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for complete Docker guide.

### Option 2: Local Installation

```bash
# 1. Database
CREATE DATABASE studyqna;
CREATE USER studyqna_user WITH PASSWORD 'password';

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ENV_TEMPLATE.txt .env
# Edit .env
python init_db.py
python run.py

# 3. Frontend
cd frontend
npm install
npm run dev
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed instructions.

## Documentation

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Complete installation guide
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Docker setup (recommended)
- **[WINDOWS_PGADMIN_SETUP.md](WINDOWS_PGADMIN_SETUP.md)** - pgAdmin setup for Windows
- **[QUICK_START.md](QUICK_START.md)** - 5-minute quick start
- **[SETUP.md](SETUP.md)** - Configuration details
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## Environment Variables

See `backend/ENV_TEMPLATE.txt` for all required environment variables.

Minimum required:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `ADMIN_EMAIL` - Admin user email
- `OPENAI_API_KEY` - OpenAI API key

## Usage Limits

### Free Users
- Max 10 pages per PDF
- 1 PDF per day
- Preview only (2-3 sample Q/A)
- No downloads

### Premium Users
- 15 PDF uploads/month
- 20 image uploads/month
- Up to 40 pages per PDF
- Full Q/A generation
- Download in PDF/DOCX/TXT formats

## Security Features

- Human detection before OCR processing
- Encrypted file storage
- JWT authentication
- Admin/user route separation
- File size and page limits
- Usage quota management

## API Endpoints

- `POST /api/auth/otp/request` - Request OTP
- `POST /api/auth/otp/verify` - Verify OTP
- `POST /api/upload` - Upload file
- `POST /api/qna/generate` - Generate Q/A
- `GET /api/qna/sets` - List saved sets
- `GET /api/qna/sets/{id}/download` - Download set
- `POST /api/user/request-premium` - Request premium
- `GET /api/admin/premium-requests` - List requests (admin)

See API docs at http://localhost:8000/docs when running.

## Mobile Features

- Automatic mobile device detection
- Camera input (mobile only)
- Responsive UI for all screen sizes
- Touch-friendly controls
- Mobile-optimized download handling

## License

MIT

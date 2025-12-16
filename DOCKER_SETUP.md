# Docker Setup Guide - StudyQnA Generator

Complete guide for running StudyQnA Generator using Docker. This simplifies installation by containerizing all services.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Database Only)](#quick-start-database-only)
3. [Full Stack Setup](#full-stack-setup)
4. [Environment Configuration](#environment-configuration)
5. [Managing Containers](#managing-containers)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Download: https://www.docker.com/products/docker-desktop
   - Verify installation:
     ```bash
     docker --version
     docker-compose --version
     ```

2. **Git** (optional, for cloning)

### System Requirements

- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 10GB free
- **CPU**: 2+ cores recommended

---

## Quick Start (Database Only)

This setup runs only PostgreSQL in Docker, while you run backend/frontend locally.

### Step 1: Create Environment File

Create `.env` file in project root:

```env
DB_PASSWORD=<DEMO_ADMIN_PASSWORD>
```

### Step 2: Start PostgreSQL

```bash
# Start database
docker-compose up -d postgres

# Check status
docker-compose ps

# View logs
docker-compose logs postgres
```

### Step 3: Verify Database

```bash
# Test connection
docker-compose exec postgres psql -U studyqna_user -d studyqna -c "SELECT version();"
```

### Step 4: Initialize Database Tables

```bash
# Run from backend directory
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Update .env with Docker database URL
# DATABASE_URL=postgresql://studyqna_user:SecurePass123!@localhost:5432/studyqna

python init_db.py
```

### Step 5: Access pgAdmin (Optional)

pgAdmin is available at: http://localhost:5050

- **Email**: `admin@studyqna.com`
- **Password**: `<DEMO_ADMIN_PASSWORD>` (or your PGADMIN_PASSWORD)

To connect to PostgreSQL in pgAdmin (web version):
- **Host**: `postgres` (container name - use this in Docker pgAdmin web UI)
- **Port**: `5432`
- **Username**: `studyqna_user`
- **Password**: `SecurePass123!` (or your DB_PASSWORD)

**⚠️ Important:** If using pgAdmin Desktop (not Docker), use:
- **Host**: `localhost` (NOT `postgres`)
- **Port**: `5432`
- **Username**: `studyqna_user`
- **Password**: Your DB_PASSWORD

See [PGADMIN_CONNECTION_TROUBLESHOOTING.md](PGADMIN_CONNECTION_TROUBLESHOOTING.md) for connection issues.

---

## Full Stack Setup

Run everything in Docker (PostgreSQL + Backend + Frontend).

### Step 1: Create Environment File

Create `.env` file in project root:

```env
# Database
DB_PASSWORD=SecurePass123!

# JWT
SECRET_KEY=your-super-secret-jwt-key-here

# Admin
ADMIN_EMAIL=admin@example.com

# Storage
ENCRYPT_STORAGE=true

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=StudyQnA <noreply@studyqna.com>

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# App
APP_URL=http://localhost:3000

# pgAdmin (Optional)
PGADMIN_EMAIL=admin@studyqna.com
PGADMIN_PASSWORD=admin123
```

### Step 2: Build and Start All Services

```bash
# Build and start all services
docker-compose -f docker-compose.full.yml up -d --build

# View logs
docker-compose -f docker-compose.full.yml logs -f

# Check status
docker-compose -f docker-compose.full.yml ps
```

### Step 3: Initialize Database

```bash
# Run database initialization
docker-compose -f docker-compose.full.yml exec backend python init_db.py
```

### Step 4: Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050

---

## Environment Configuration

### Database Connection

**When using Docker for database only:**
```env
DATABASE_URL=postgresql://studyqna_user:SecurePass123!@localhost:5432/studyqna
```

**When using Docker for full stack:**
```env
DATABASE_URL=postgresql://studyqna_user:SecurePass123!@postgres:5432/studyqna
```
(Note: `postgres` is the service name, not `localhost`)

### Generate Secret Key

```bash
# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output to `.env` as `SECRET_KEY`.

---

## Managing Containers

### View Running Containers

```bash
docker-compose ps
# Or for full stack
docker-compose -f docker-compose.full.yml ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update and Rebuild

```bash
# Pull latest images and rebuild
docker-compose pull
docker-compose up -d --build
```

### Access Container Shell

```bash
# PostgreSQL
docker-compose exec postgres psql -U studyqna_user -d studyqna

# Backend
docker-compose exec backend bash

# Frontend
docker-compose exec frontend sh
```

---

## Data Persistence

### Volumes

Docker creates volumes to persist data:

- `postgres_data`: Database files
- `backend_storage`: Uploaded files
- `pgadmin_data`: pgAdmin settings

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U studyqna_user studyqna > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U studyqna_user -d studyqna < backup.sql
```

### View Volume Locations

```bash
docker volume ls
docker volume inspect studyqna_postgres_data
```

---

## Troubleshooting

### Problem: Port already in use

**Error**: `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Solution**:
```bash
# Check what's using the port
# Windows
netstat -ano | findstr :5432

# Linux/Mac
lsof -i :5432

# Stop the conflicting service or change port in docker-compose.yml
```

### Problem: Database connection refused

**Solution**:
```bash
# Check if postgres is healthy
docker-compose ps

# Check logs
docker-compose logs postgres

# Wait for database to be ready
docker-compose exec postgres pg_isready -U studyqna_user
```

### Problem: Backend can't connect to database

**Solution**:
- Verify `DATABASE_URL` uses `postgres` (service name) not `localhost`
- Check network: `docker network ls`
- Ensure postgres is healthy: `docker-compose ps`

### Problem: Permission denied errors

**Solution**:
```bash
# Fix storage permissions
docker-compose exec backend chmod 700 /app/storage
docker-compose exec backend chown -R root:root /app/storage
```

### Problem: Out of disk space

**Solution**:
```bash
# Clean up unused Docker resources
docker system prune -a

# Remove specific volumes (⚠️ deletes data)
docker volume rm studyqna_postgres_data
```

### Problem: Container keeps restarting

**Solution**:
```bash
# Check logs for errors
docker-compose logs backend

# Check container status
docker-compose ps

# Inspect container
docker inspect studyqna_backend
```

---

## Development Workflow

### Option 1: Database in Docker, Code Local

```bash
# Start database
docker-compose up -d postgres

# Run backend locally
cd backend
source venv/bin/activate
python run.py

# Run frontend locally
cd frontend
npm run dev
```

### Option 2: Everything in Docker

```bash
# Start all services
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose -f docker-compose.full.yml logs -f

# Make changes and rebuild
docker-compose -f docker-compose.full.yml up -d --build
```

---

## Production Deployment

For production, consider:

1. **Use specific image tags** (not `latest`)
2. **Set strong passwords** in `.env`
3. **Use Docker secrets** for sensitive data
4. **Configure SSL/TLS** (use reverse proxy like Nginx)
5. **Set resource limits** in docker-compose.yml
6. **Enable logging** and monitoring
7. **Set up backups** for volumes

Example production docker-compose:

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Useful Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Execute command in container
docker-compose exec backend python init_db.py

# Access database
docker-compose exec postgres psql -U studyqna_user -d studyqna

# Clean up everything
docker-compose down -v
docker system prune -a
```

---

## Next Steps

After Docker setup:

1. ✅ Database running in Docker
2. ✅ Access pgAdmin at http://localhost:5050 (if enabled)
3. ✅ Initialize database tables
4. ✅ Configure backend `.env` with Docker database URL
5. ✅ Start backend and frontend
6. ✅ Access application at http://localhost:3000

---

## Comparison: Docker vs Local Installation

| Feature | Docker | Local |
|---------|--------|-------|
| Setup Time | ⚡ Fast (5 min) | 🐌 Slower (30+ min) |
| Dependencies | ✅ Auto-installed | ❌ Manual install |
| Isolation | ✅ Yes | ❌ No |
| Port Conflicts | ⚠️ Possible | ⚠️ Possible |
| Updates | ✅ Easy | ⚠️ Manual |
| Production Ready | ✅ Yes | ✅ Yes |

**Recommendation**: Use Docker for development and production!

---

## Additional Resources

- Docker Documentation: https://docs.docker.com/
- Docker Compose Reference: https://docs.docker.com/compose/
- PostgreSQL Docker Image: https://hub.docker.com/_/postgres
- pgAdmin Docker Image: https://hub.docker.com/r/dpage/pgadmin4


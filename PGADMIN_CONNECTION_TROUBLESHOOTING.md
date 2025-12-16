# pgAdmin Connection Troubleshooting

## Error: "Unable to connect to server: [Errno 11001] getaddrinfo failed"

This error means pgAdmin cannot resolve the hostname/address you're trying to connect to.

---

## Solution 1: Check Hostname/Address

### For Docker Setup (Recommended)

If you're using Docker for PostgreSQL:

1. **In pgAdmin Connection Settings:**
   - **Host name/address**: `localhost` (not `postgres` or container name)
   - **Port**: `5432`
   - **Maintenance database**: `postgres` or `studyqna`
   - **Username**: `studyqna_user`
   - **Password**: Your DB_PASSWORD from .env file

2. **Verify Docker container is running:**
   ```bash
   docker-compose ps
   # Should show postgres container as "Up"
   ```

3. **Check if port is accessible:**
   ```bash
   # Windows
   netstat -an | findstr :5432
   
   # Should show: 0.0.0.0:5432 or 127.0.0.1:5432
   ```

### For Local PostgreSQL Installation

1. **Host name/address**: `localhost` or `127.0.0.1`
2. **Port**: `5432`
3. **Username**: `studyqna_user`
4. **Password**: The password you set when creating the user

---

## Solution 2: Verify PostgreSQL is Running

### Docker Setup

```bash
# Check container status
docker-compose ps

# If not running, start it
docker-compose up -d postgres

# Check logs for errors
docker-compose logs postgres
```

### Local Installation

**Windows:**
1. Open **Services** (Win + R → type `services.msc`)
2. Find **"postgresql-x64-[version]"**
3. Ensure status is **"Running"**
4. If not, right-click → **"Start"**

**Linux:**
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

---

## Solution 3: Correct pgAdmin Connection Settings

### Step-by-Step Connection Setup

1. **Open pgAdmin**
2. **Right-click "Servers"** → **"Register"** → **"Server..."**

3. **General Tab:**
   - **Name**: `StudyQnA Local` (any name you want)

4. **Connection Tab:**
   - **Host name/address**: `localhost` ⚠️ (NOT `postgres`, NOT empty)
   - **Port**: `5432`
   - **Maintenance database**: `postgres` (or `studyqna`)
   - **Username**: `studyqna_user`
   - **Password**: Your password (from .env DB_PASSWORD or what you set)
   - **Save password?**: ✅ Check this box

5. **Click "Save"**

### Common Mistakes:

❌ **Wrong**: Host name = `postgres` (this is for Docker internal network)  
✅ **Correct**: Host name = `localhost` (for connecting from your machine)

❌ **Wrong**: Host name = empty  
✅ **Correct**: Host name = `localhost` or `127.0.0.1`

❌ **Wrong**: Port = empty or wrong port  
✅ **Correct**: Port = `5432`

---

## Solution 4: Test Connection from Command Line

Before trying pgAdmin, test if you can connect:

### Docker Setup

```bash
# Test connection
docker-compose exec postgres psql -U studyqna_user -d studyqna

# Or from your machine
psql -h localhost -U studyqna_user -d studyqna -p 5432
```

### Local Installation

```bash
psql -h localhost -U studyqna_user -d studyqna -p 5432
```

If this works, pgAdmin should work too (with same settings).

---

## Solution 5: Check Firewall/Network

### Windows Firewall

1. Open **Windows Defender Firewall**
2. Check if PostgreSQL port 5432 is allowed
3. If not, add exception for port 5432

### Antivirus Software

Some antivirus software blocks database connections. Temporarily disable to test.

---

## Solution 6: Verify Docker Port Mapping

Check if Docker is correctly mapping the port:

```bash
# Check port mapping
docker-compose ps

# Should show: 0.0.0.0:5432->5432/tcp

# If port is different, check docker-compose.yml
```

If port mapping is wrong, update `docker-compose.yml`:

```yaml
services:
  postgres:
    ports:
      - "5432:5432"  # Ensure this matches
```

---

## Solution 7: Connect to Docker Container Directly

If you can't connect from outside, connect from within Docker:

1. **In pgAdmin, use Docker network:**
   - This is more complex and not recommended
   - Better to use `localhost` from your machine

2. **Or use Docker exec:**
   ```bash
   docker-compose exec postgres psql -U studyqna_user -d studyqna
   ```

---

## Quick Checklist

Before connecting in pgAdmin, verify:

- [ ] PostgreSQL container/service is running
- [ ] Port 5432 is not blocked by firewall
- [ ] Host name is `localhost` (not `postgres`)
- [ ] Port is `5432`
- [ ] Username is `studyqna_user`
- [ ] Password is correct (check .env file)
- [ ] Database `studyqna` exists

---

## Example: Correct pgAdmin Settings

```
General Tab:
  Name: StudyQnA Local

Connection Tab:
  Host name/address: localhost
  Port: 5432
  Maintenance database: postgres
  Username: studyqna_user
  Password: SecurePass123!  (your actual password)
  Save password?: ✅ Yes
```

---

## Still Not Working?

1. **Check Docker logs:**
   ```bash
   docker-compose logs postgres
   ```

2. **Restart Docker container:**
   ```bash
   docker-compose restart postgres
   ```

3. **Verify database exists:**
   ```bash
   docker-compose exec postgres psql -U postgres -c "\l"
   # Should list studyqna database
   ```

4. **Check pgAdmin version:**
   - Update to latest pgAdmin version
   - Or use pgAdmin from Docker: http://localhost:5050

---

## Alternative: Use pgAdmin from Docker

If pgAdmin desktop isn't working, use the web version:

1. **Start pgAdmin in Docker:**
   ```bash
   docker-compose up -d pgadmin
   ```

2. **Access at:** http://localhost:5050

3. **Login:**
   - Email: `admin@studyqna.com`
   - Password: `admin123` (or your PGADMIN_PASSWORD)

4. **Add Server:**
   - Right-click "Servers" → "Register" → "Server"
   - **Name**: StudyQnA
   - **Host**: `postgres` (use container name, not localhost!)
   - **Port**: `5432`
   - **Username**: `studyqna_user`
   - **Password**: Your DB_PASSWORD

---

## Summary

**Most Common Fix:**

Change **Host name/address** from empty or `postgres` to **`localhost`**

Then verify:
- Docker container is running
- Port 5432 is accessible
- Username and password are correct



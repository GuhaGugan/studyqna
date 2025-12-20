# 🚀 Automated Installation Script

## Quick Start

This script automates the complete installation of StudyQnA Assistant on Ubuntu 22.04.

### Prerequisites

- Ubuntu 22.04 LTS server
- SSH access to the server
- Sudo privileges
- Your application code already uploaded to the server

### Usage

1. **Upload the script to your server:**
   ```bash
   scp -i your-key.pem install.sh ubuntu@YOUR_SERVER_IP:~/
   ```

2. **Make it executable:**
   ```bash
   chmod +x install.sh
   ```

3. **Run the script:**
   ```bash
   ./install.sh
   ```

4. **Follow the prompts:**
   - Enter your static IP address (optional)
   - Enter your domain name (optional, for SSL)
   - Enter database password (twice for confirmation)

### What the Script Does

The script automates all these steps:

1. ✅ Updates system packages
2. ✅ Installs essential tools (curl, wget, git, etc.)
3. ✅ Creates application user (`studyqna`)
4. ✅ Configures firewall (UFW)
5. ✅ Sets up swap memory (2GB)
6. ✅ Installs and configures PostgreSQL
7. ✅ Installs Python 3.11 and dependencies
8. ✅ Installs Node.js 18
9. ✅ Sets up backend environment
10. ✅ Sets up frontend environment
11. ✅ Installs and configures Nginx
12. ✅ Creates systemd service
13. ✅ Sets up SSL (if domain provided)
14. ✅ Creates .env file template

### After Installation

The script will print a summary with next steps:

1. **Edit .env file** - Add your API keys
2. **Install Python dependencies** - `pip install -r requirements.txt`
3. **Initialize database** - `python init_db.py`
4. **Build frontend** - `npm run build`
5. **Start service** - `sudo systemctl start studyqna-backend`
6. **Setup SSL** - `sudo certbot --nginx -d yourdomain.com`

### Important Notes

- **Code must be in place:** The script assumes your code is already at `/home/studyqna/studyqna/`
- **Manual steps required:** Some steps (like installing Python packages) need to be done manually after the script
- **.env configuration:** You must edit the .env file and add your actual API keys
- **Database password:** Choose a strong password - it will be stored in .env file

### Troubleshooting

**Script fails with permission error:**
- Make sure you're not running as root
- The script will use `sudo` when needed

**Database creation fails:**
- Check if PostgreSQL is running: `sudo systemctl status postgresql`
- Check if database already exists: `sudo -u postgres psql -l`

**Nginx configuration error:**
- Test configuration: `sudo nginx -t`
- Check logs: `sudo tail -f /var/log/nginx/error.log`

**Service won't start:**
- Check logs: `sudo journalctl -u studyqna-backend -f`
- Verify .env file exists and has correct values
- Make sure Python dependencies are installed

### Manual Installation

If you prefer manual installation or the script fails, refer to:
- `COMPLETE_INSTALLATION_GUIDE.md` - Step-by-step manual guide

---

**Estimated Time:** 15-30 minutes (depending on internet speed)

**Script Version:** 1.0


# 🌐 Domain & IP Configuration Guide

## Where to Provide Domain/IP During Installation

When you run `install.sh`, you'll be prompted for domain/IP configuration. Here's when to provide what:

---

## 📍 **During Script Execution**

The script will ask you:

```
=== Configuration Setup ===

Domain/IP Configuration:
  - If you have a domain name (e.g., studyqna.com), enter it below
  - If you don't have a domain, enter your server's static IP address
  - You can skip both and configure later, but you'll need at least one

Enter your domain name (e.g., studyqna.com) or press Enter to skip: 
```

### **Option 1: You Have a Domain Name** ✅
**Enter:** `studyqna.com` (or your actual domain)

**What happens:**
- Nginx configured for: `studyqna.com www.studyqna.com`
- .env APP_URL: `https://studyqna.com`
- .env CORS_ORIGINS_LIST: `https://studyqna.com,https://www.studyqna.com`
- SSL certificate can be set up after installation

**Example:**
```
Enter your domain name: studyqna.com
```

---

### **Option 2: You Don't Have a Domain (Use IP Only)** ✅
**Press Enter** (skip domain), then **Enter your static IP**

**What happens:**
- Nginx configured for: `54.123.45.67` (your IP)
- .env APP_URL: `http://54.123.45.67`
- .env CORS_ORIGINS_LIST: `http://54.123.45.67`
- No SSL (can't get SSL for IP addresses)

**Example:**
```
Enter your domain name: [Press Enter]
Enter your static IP address: 54.123.45.67
```

---

### **Option 3: Skip Both (Not Recommended)** ⚠️
**Press Enter** for both prompts

**What happens:**
- Script uses server's auto-detected IP
- You'll need to manually update .env file later
- Less ideal, but works for testing

---

## 📋 **Where Domain/IP Are Used**

### **1. Nginx Configuration** (`/etc/nginx/sites-available/studyqna`)
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;  # ← Here
    ...
}
```

**Used for:**
- Web server routing
- SSL certificate binding (if domain provided)

---

### **2. Backend .env File** (`/home/studyqna/studyqna/backend/.env`)
```env
APP_URL=https://yourdomain.com  # ← Here (or http://IP)

CORS_ORIGINS_LIST=https://yourdomain.com,https://www.yourdomain.com  # ← Here
```

**Used for:**
- CORS (Cross-Origin Resource Sharing) - allows frontend to call backend
- Email links and redirects
- API endpoint references

---

### **3. SSL Certificate (If Domain Provided)**
After installation, you can run:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Requirements:**
- Domain must point to your server's IP (DNS configured)
- Port 80 must be open (for Let's Encrypt verification)

---

## 🔄 **Changing Domain/IP Later**

If you need to change domain/IP after installation:

### **1. Update Nginx:**
```bash
sudo nano /etc/nginx/sites-available/studyqna
# Change server_name line
sudo nginx -t
sudo systemctl reload nginx
```

### **2. Update .env:**
```bash
nano /home/studyqna/studyqna/backend/.env
# Update APP_URL and CORS_ORIGINS_LIST
sudo systemctl restart studyqna-backend
```

---

## ✅ **Quick Decision Guide**

| Situation | What to Enter |
|-----------|---------------|
| ✅ Have domain, DNS configured | Enter domain: `studyqna.com` |
| ✅ Have domain, DNS not ready | Enter domain: `studyqna.com` (configure DNS later) |
| ✅ No domain, have static IP | Skip domain, enter IP: `54.123.45.67` |
| ⚠️ No domain, no static IP | Skip both (uses auto-detected IP) |
| 🔄 Testing locally | Skip both, use `localhost` or IP later |

---

## 🎯 **Recommended Approach**

**Best Practice:**
1. **If you have a domain:** Enter it during installation
2. **If you don't have a domain:** Enter your static IP
3. **You can always change it later** by editing the files above

**For Production:**
- Always use a domain name (looks professional, enables SSL)
- Domain costs ₹500-1,000/year (GoDaddy, Namecheap, etc.)

**For Testing:**
- IP address is fine
- Can switch to domain later

---

## 📝 **Example Scenarios**

### **Scenario 1: Production with Domain**
```
Enter domain: studyqna.com
[Script configures everything for domain]
[After installation: Setup SSL with certbot]
[Access: https://studyqna.com]
```

### **Scenario 2: Testing with IP**
```
Enter domain: [Enter]
Enter IP: 54.123.45.67
[Script configures for IP]
[Access: http://54.123.45.67]
```

### **Scenario 3: Domain Later**
```
Enter domain: [Enter]
Enter IP: 54.123.45.67
[Use IP for now]
[Later: Update Nginx and .env when domain is ready]
```

---

**That's it!** The script handles everything automatically based on what you provide. 🚀


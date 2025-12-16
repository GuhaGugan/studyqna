# Demo Environment Setup Guide for Marketplace Listing

## 🎯 Purpose

Create a live demo environment that potential buyers can access to test all features of StudyQnA before purchasing.

---

## 📋 Prerequisites

1. **Server/Hosting:**
   - AWS EC2 (t2.micro - free tier eligible)
   - DigitalOcean Droplet ($6/month)
   - Heroku (free tier)
   - Railway.app (free tier)
   - Render (free tier)

2. **Domain (Optional):**
   - Free subdomain: `studyqna-demo.railway.app`
   - Or use your own: `demo.studyqna.com`

3. **Services:**
   - OpenAI API key (for demo)
   - Email service (Brevo free tier)
   - PostgreSQL database (included with hosting)

---

## 🚀 Quick Setup (Railway.app - Recommended)

### **Step 1: Create Railway Account**
1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project

### **Step 2: Deploy Backend**
1. Connect GitHub repository
2. Select `backend` folder
3. Add environment variables:
   ```
   DATABASE_URL=postgresql://...
   SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-openai-key
   SMTP_HOST=smtp-relay.brevo.com
   SMTP_USER=your-email
   SMTP_PASSWORD=your-password
   ```
4. Deploy

### **Step 3: Deploy Frontend**
1. Add new service
2. Select `frontend` folder
3. Add environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app/api
   ```
4. Deploy

### **Step 4: Setup Database**
1. Add PostgreSQL service
2. Run migrations:
   ```bash
   python init_db.py
   ```

---

## 🎬 Demo Account Setup

### **Create Demo Accounts:**

1. **Admin Account:**
   - Email: `admin@demo.studyqna.com`
   - Password: `<DEMO_ADMIN_PASSWORD>`
   - Role: Admin

2. **Premium User:**
   - Email: `premium@demo.studyqna.com`
   - Password: `<DEMO_PREMIUM_PASSWORD>`
   - Status: Premium (approved)

3. **Free User:**
   - Email: `free@demo.studyqna.com`
   - Password: `<DEMO_FREE_PASSWORD>`
   - Status: Free

### **Setup Script:**

```python
# create_demo_accounts.py
from app.database import SessionLocal
from app.models import User, UserRole, PremiumStatus
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

# Admin
admin = User(
    email="admin@demo.studyqna.com",
    role=UserRole.ADMIN,
    premium_status=PremiumStatus.APPROVED,
    premium_valid_until=datetime.utcnow() + timedelta(days=365),
    upload_quota_remaining=100,
    image_quota_remaining=100
)
# Note: Password should be set via auth system
db.add(admin)

# Premium User
premium = User(
    email="premium@demo.studyqna.com",
    role=UserRole.USER,
    premium_status=PremiumStatus.APPROVED,
    premium_valid_until=datetime.utcnow() + timedelta(days=365),
    upload_quota_remaining=15,
    image_quota_remaining=20
)
db.add(premium)

# Free User
free = User(
    email="free@demo.studyqna.com",
    role=UserRole.USER,
    premium_status=PremiumStatus.FREE,
    upload_quota_remaining=1,
    image_quota_remaining=0
)
db.add(free)

db.commit()
```

---

## 📸 Screenshots to Prepare

### **1. Homepage/Login:**
- Login page
- OTP request screen
- OTP verification

### **2. User Dashboard:**
- Dashboard overview
- Upload tab
- Generate tab
- Saved sets tab
- Profile tab

### **3. Admin Dashboard:**
- Users management
- Premium requests
- Uploads management
- AI usage tracker
- Login logs
- Reviews

### **4. Features:**
- File upload (PDF)
- File upload (Image with camera)
- Q/A generation form
- Generated Q/A display
- Download options (PDF, DOCX, TXT)
- Multilingual support

### **5. Mobile Views:**
- Mobile dashboard
- Mobile camera upload
- Mobile Q/A display

---

## 🎥 Demo Video Script

### **Video 1: Overview (2-3 minutes)**

**Introduction (0:00-0:30):**
- "Welcome to StudyQnA - AI-powered Q/A generator"
- "This is a complete, production-ready SaaS platform"

**Features Walkthrough (0:30-2:00):**
- Show login process
- Upload a PDF
- Generate questions
- Show multilingual support
- Download in different formats
- Show admin dashboard

**Closing (2:00-2:30):**
- "Ready to launch, no development needed"
- "Contact for demo access"

### **Video 2: Technical Deep Dive (5-7 minutes)**

**Architecture (0:00-1:00):**
- Show code structure
- Tech stack overview
- Database schema

**Features (1:00-4:00):**
- AI integration
- OCR processing
- Content validation
- PDF generation
- Admin features

**Deployment (4:00-5:00):**
- Docker setup
- Environment variables
- Database migration

**Closing (5:00-5:30):**
- "Production-ready code"
- "Full documentation included"

---

## 🔒 Security for Demo

### **1. Rate Limiting:**
- Limit API calls per IP
- Prevent abuse
- Use demo API keys with limits

### **2. Data Isolation:**
- Separate demo database
- Reset daily/weekly
- No real user data

### **3. Access Control:**
- Password-protected demo
- Time-limited access
- IP whitelist (optional)

### **4. Monitoring:**
- Track demo usage
- Monitor for abuse
- Alert on suspicious activity

---

## 📝 Demo Access Instructions for Buyers

### **Email Template:**

```
Subject: StudyQnA Demo Access

Hi [Buyer Name],

Thanks for your interest in StudyQnA!

Here are the demo credentials:

🌐 Demo URL: https://demo.studyqna.com

👤 Admin Account:
   Email: admin@demo.studyqna.com
   Password: <DEMO_ADMIN_PASSWORD>

👤 Premium User:
   Email: premium@demo.studyqna.com
   Password: <DEMO_PREMIUM_PASSWORD>

👤 Free User:
   Email: free@demo.studyqna.com
   Password: <DEMO_FREE_PASSWORD>

📋 What to Test:
1. Login with different accounts
2. Upload a PDF or image
3. Generate Q/A with different settings
4. Try multilingual support
5. Download in different formats
6. Explore admin dashboard

⏰ Demo Access:
- Valid for 7 days
- Data resets daily at midnight
- Please don't abuse the system

📞 Questions?
Feel free to reach out!

Best regards,
[Your Name]
```

---

## 🛠️ Maintenance

### **Daily:**
- Reset demo data (optional)
- Check server status
- Monitor API usage

### **Weekly:**
- Review demo accounts
- Update sample data
- Check for issues

### **Monthly:**
- Review costs
- Optimize resources
- Update documentation

---

## 💰 Cost Estimate

### **Free Tier Options:**
- **Railway.app**: Free tier available
- **Render**: Free tier available
- **Heroku**: Free tier (limited)

### **Paid Options:**
- **DigitalOcean**: $6-12/month
- **AWS EC2**: $5-10/month (t2.micro)
- **Domain**: ₹500-1,000/year (optional)

### **Services:**
- **OpenAI API**: Pay per use (~$5-10/month for demo)
- **Email (Brevo)**: Free tier (300 emails/day)

**Total: ₹500-1,500/month** (~$6-18/month)

---

## ✅ Checklist

### **Before Listing:**
- [ ] Deploy demo environment
- [ ] Create demo accounts
- [ ] Take screenshots
- [ ] Record demo videos
- [ ] Write demo access instructions
- [ ] Test all features
- [ ] Set up monitoring
- [ ] Configure security

### **During Listing:**
- [ ] Share demo credentials with serious buyers
- [ ] Monitor demo usage
- [ ] Respond to questions
- [ ] Update demo if needed

### **After Sale:**
- [ ] Transfer demo access
- [ ] Provide production setup guide
- [ ] Hand over code
- [ ] Offer support period

---

## 🎯 Pro Tips

1. **Keep Demo Fresh:**
   - Reset data regularly
   - Add sample content
   - Show latest features

2. **Monitor Usage:**
   - Track who's using demo
   - Identify serious buyers
   - Follow up with active users

3. **Be Responsive:**
   - Answer questions quickly
   - Provide additional access if needed
   - Offer code walkthrough

4. **Show Value:**
   - Highlight unique features
   - Demonstrate ease of use
   - Show production readiness

---

**Remember**: A good demo can make or break a sale. Invest time in making it perfect!



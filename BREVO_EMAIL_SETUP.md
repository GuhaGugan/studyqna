# Brevo Email Setup Guide

This guide explains how to configure Brevo (formerly Sendinblue) API for sending emails in StudyQnA Generator.

## Why Brevo?

- **Free Tier**: 300 emails/day (perfect for development and small deployments)
- **Easy Setup**: Just need an API key
- **Reliable**: Professional email delivery service
- **No SMTP Configuration**: No need to configure SMTP servers, ports, or passwords

## Setup Steps

### 1. Create Brevo Account

1. Go to [https://www.brevo.com](https://www.brevo.com)
2. Sign up for a free account
3. Verify your email address

### 2. Get API Key

1. Log in to your Brevo dashboard
2. Go to **Settings** → **API Keys** (or visit: https://app.brevo.com/settings/keys/api)
3. Click **Generate a new API key**
4. Give it a name (e.g., "StudyQnA Production")
5. Copy the API key (you'll only see it once!)

### 3. Verify Sender Email

1. Go to **Settings** → **Senders** (or visit: https://app.brevo.com/settings/senders)
2. Click **Add a sender**
3. Enter your email address (e.g., `noreply@yourdomain.com`)
4. Verify the email by clicking the verification link sent to your inbox
5. Wait for approval (usually instant for verified domains)

### 4. Configure .env File

Edit your `backend/.env` file and add:

```env
# Email Provider - Use Brevo
EMAIL_PROVIDER=brevo

# Brevo API Configuration
BREVO_API_KEY=xkeysib-your-api-key-here
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=StudyQnA
```

**Important Notes:**
- Replace `xkeysib-your-api-key-here` with your actual Brevo API key
- Replace `noreply@yourdomain.com` with your verified sender email
- The `BREVO_FROM_NAME` will appear as the sender name in emails

### 5. Test Email Sending

1. Start your backend server:
   ```bash
   cd backend
   python run.py
   ```

2. Try requesting an OTP from the frontend
3. Check the backend console for success message:
   ```
   ✅ OTP email sent via Brevo to user@example.com
   ✅ Brevo email sent successfully. Message ID: ...
   ```

4. Check the recipient's inbox (and spam folder if needed)

## Fallback to SMTP

If Brevo is not configured or fails, the system will automatically:
1. Try SMTP (if configured)
2. Fall back to console output (for development)

To use SMTP instead, set:
```env
EMAIL_PROVIDER=smtp
```

## Troubleshooting

### Error: "Invalid API key"
- Double-check your API key in `.env`
- Make sure there are no extra spaces or quotes
- Regenerate the API key if needed

### Error: "Sender email not verified"
- Go to Brevo dashboard → Settings → Senders
- Verify your sender email address
- Wait for approval if pending

### Emails going to spam
- Verify your sender domain in Brevo
- Add SPF/DKIM records to your domain DNS (if using custom domain)
- Use a professional sender email address

### Rate Limits
- Free tier: 300 emails/day
- If you exceed, upgrade to a paid plan or use SMTP as backup

## Environment Variables Summary

```env
# Choose email provider
EMAIL_PROVIDER=brevo          # or "smtp"

# Brevo API (if EMAIL_PROVIDER=brevo)
BREVO_API_KEY=your-api-key
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=StudyQnA

# SMTP (if EMAIL_PROVIDER=smtp or as fallback)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=StudyQnA <noreply@studyqna.com>
```

## Benefits of Brevo

✅ **No SMTP Configuration**: Just API key  
✅ **Better Deliverability**: Professional email infrastructure  
✅ **Email Templates**: Can create templates in Brevo dashboard  
✅ **Analytics**: Track email opens, clicks, bounces  
✅ **Free Tier**: 300 emails/day is generous for most use cases  
✅ **Reliable**: Used by thousands of companies worldwide  

## Support

- Brevo Documentation: https://developers.brevo.com/
- Brevo API Reference: https://developers.brevo.com/reference/sendtransacemail
- Brevo Support: https://help.brevo.com/



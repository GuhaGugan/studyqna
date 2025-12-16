import aiosmtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.security import generate_otp, store_otp

async def send_otp_email(email: str) -> str:
    """Send OTP email using Brevo API or SMTP and return the OTP"""
    otp = generate_otp()
    store_otp(email, otp)
    
    # Try Brevo API first if configured
    if settings.EMAIL_PROVIDER.lower() == "brevo" and settings.BREVO_API_KEY:
        try:
            await send_via_brevo(email, otp)
            print(f"✅ OTP email sent via Brevo to {email}")
            return otp
        except Exception as e:
            print(f"❌ Brevo API error: {e}")
            print(f"⚠️  Falling back to SMTP or console output...")
    
    # Fallback to SMTP if Brevo fails or not configured
    if settings.EMAIL_PROVIDER.lower() == "smtp" or (not settings.BREVO_API_KEY and settings.SMTP_USER and settings.SMTP_PASSWORD):
        try:
            await send_via_smtp(email, otp)
            print(f"✅ OTP email sent via SMTP to {email}")
            return otp
        except Exception as e:
            print(f"❌ SMTP error: {e}")
            print(f"⚠️  DEVELOPMENT MODE: OTP for {email} is: {otp}")
            return otp
    
    # If neither is configured, print to console
    print(f"⚠️  Email not configured. OTP for {email} is: {otp}")
    return otp

async def send_via_brevo(email: str, otp: str) -> None:
    """Send email using Brevo API"""
    if not settings.BREVO_API_KEY:
        raise ValueError("BREVO_API_KEY not configured")
    
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": settings.BREVO_FROM_NAME,
            "email": settings.BREVO_FROM_EMAIL
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": "Your StudyQnA Login OTP",
        "htmlContent": f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #2563eb;">Your StudyQnA Login OTP</h2>
              <p>Your OTP code is:</p>
              <div style="background-color: #f3f4f6; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                <strong style="font-size: 32px; color: #2563eb; letter-spacing: 4px;">{otp}</strong>
              </div>
              <p>This OTP will expire in <strong>5 minutes</strong>.</p>
              <p style="color: #6b7280; font-size: 14px;">If you didn't request this, please ignore this email.</p>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
              <p style="color: #9ca3af; font-size: 12px;">© 2025 StudyQnA — Created by GUGAN</p>
            </div>
          </body>
        </html>
        """,
        "textContent": f"""
        Your StudyQnA login OTP is: {otp}
        
        This OTP will expire in 5 minutes.
        
        If you didn't request this, please ignore this email.
        """
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if "messageId" in result:
            print(f"✅ Brevo email sent successfully. Message ID: {result['messageId']}")
        else:
            print(f"⚠️  Brevo response: {result}")

async def send_via_smtp(email: str, otp: str) -> None:
    """Send email using SMTP (fallback method)"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise ValueError("SMTP credentials not configured")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your StudyQnA Login OTP"
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    
    text = f"""
    Your StudyQnA login OTP is: {otp}
    
    This OTP will expire in 5 minutes.
    
    If you didn't request this, please ignore this email.
    """
    
    html = f"""
    <html>
      <body>
        <h2>Your StudyQnA Login OTP</h2>
        <p>Your OTP is: <strong style="font-size: 24px; color: #2563eb;">{otp}</strong></p>
        <p>This OTP will expire in 5 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=True,
    )

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import OTPRequest, OTPVerify, Token
from app.security import verify_otp, create_access_token, is_admin_email
from app.email_service import send_otp_email
from app.email_validation import validate_email_address
from app.models import User, UserRole, LoginLog
from datetime import timedelta
from app.config import settings
import re

router = APIRouter()

@router.post("/otp/request")
async def request_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Request OTP for login"""
    email = request.email.lower()
    
    # Validate email address (RFC + DNS MX)
    is_valid, error_msg = validate_email_address(email)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create user if doesn't exist
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            role=UserRole.ADMIN if is_admin_email(email) else UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Send OTP (email service handles errors gracefully)
    await send_otp_email(email)
    
    # Always return success - OTP is either sent via email or printed to console
    return {"message": "OTP sent to your email (check server console if email not configured)"}

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Priority order for IP extraction:
    # 1. X-Forwarded-For (most common for proxies/load balancers)
    # 2. X-Real-IP (nginx proxy)
    # 3. CF-Connecting-IP (Cloudflare)
    # 4. True-Client-IP (some CDNs)
    # 5. Direct client IP
    
    # Check X-Forwarded-For (comma-separated list, first is original client)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        ip = forwarded.split(",")[0].strip()
        # Validate it's not localhost
        if ip and ip != "127.0.0.1" and ip != "::1":
            return ip
    
    # Check X-Real-IP (nginx proxy)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip != "127.0.0.1" and real_ip != "::1":
        return real_ip
    
    # Check Cloudflare header
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and cf_ip != "127.0.0.1" and cf_ip != "::1":
        return cf_ip
    
    # Check True-Client-IP (some CDNs/proxies)
    true_client_ip = request.headers.get("True-Client-IP")
    if true_client_ip and true_client_ip != "127.0.0.1" and true_client_ip != "::1":
        return true_client_ip
    
    # Fallback to direct client IP
    if request.client:
        client_ip = request.client.host
        # If it's localhost, try to get more info
        if client_ip in ["127.0.0.1", "::1", "localhost"]:
            # For localhost, we can't get the real IP, but log it
            return f"{client_ip} (localhost)"
        return client_ip
    
    return "unknown"

def detect_device_type(user_agent: str) -> str:
    """Detect device type from User-Agent string"""
    if not user_agent:
        return "unknown"
    
    user_agent_lower = user_agent.lower()
    
    # Mobile device patterns
    mobile_patterns = [
        r'mobile', r'android', r'iphone', r'ipod', r'ipad',
        r'blackberry', r'windows phone', r'opera mini'
    ]
    
    # Tablet patterns
    tablet_patterns = [
        r'ipad', r'android(?!.*mobile)', r'tablet'
    ]
    
    # Check for tablets first (more specific)
    for pattern in tablet_patterns:
        if re.search(pattern, user_agent_lower):
            return "tablet"
    
    # Check for mobile
    for pattern in mobile_patterns:
        if re.search(pattern, user_agent_lower):
            return "mobile"
    
    # Default to desktop
    return "desktop"

@router.post("/otp/verify", response_model=Token)
async def verify_otp_endpoint(
    request: OTPVerify,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Verify OTP and return JWT token"""
    email = request.email.lower()
    
    # Verify OTP
    if not verify_otp(email, request.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    # Get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Capture login information
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")
    device_type = detect_device_type(user_agent)
    
    # Debug: Log IP detection details (for troubleshooting)
    print(f"🔍 Login from user: {email}")
    print(f"📡 IP Detection Debug:")
    print(f"   - X-Forwarded-For: {http_request.headers.get('X-Forwarded-For', 'None')}")
    print(f"   - X-Real-IP: {http_request.headers.get('X-Real-IP', 'None')}")
    print(f"   - CF-Connecting-IP: {http_request.headers.get('CF-Connecting-IP', 'None')}")
    print(f"   - True-Client-IP: {http_request.headers.get('True-Client-IP', 'None')}")
    print(f"   - Direct client: {http_request.client.host if http_request.client else 'None'}")
    print(f"   - Final IP: {ip_address}")
    print(f"   - Device: {device_type}")
    
    # Log login
    login_log = LoginLog(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,  # Limit length
        device_type=device_type
    )
    db.add(login_log)
    db.commit()
    db.refresh(login_log)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email, 
            "user_id": user.id, 
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value
    }


from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import OTPRequest, OTPVerify, Token, DeviceLoginRequest
from app.security import verify_otp, create_access_token, is_admin_email, generate_device_fingerprint, generate_device_token
from app.email_service import send_otp_email
from app.email_validation import validate_email_address
from app.models import User, UserRole, LoginLog, DeviceSession
from datetime import timedelta, datetime
from app.config import settings
import re

router = APIRouter()

@router.post("/otp/request")
async def request_otp(
    request: OTPRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Request OTP for login - checks if device is known first"""
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
    
    # Check if device is known (trusted device)
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")
    device_fingerprint = generate_device_fingerprint(ip_address, user_agent)
    
    # Clean up expired device sessions for this user
    db.query(DeviceSession).filter(
        DeviceSession.user_id == user.id,
        DeviceSession.expires_at <= datetime.utcnow()
    ).delete()
    db.commit()
    
    # Check for existing valid device session
    device_session = db.query(DeviceSession).filter(
        DeviceSession.user_id == user.id,
        DeviceSession.device_fingerprint == device_fingerprint,
        DeviceSession.expires_at > datetime.utcnow()
    ).first()
    
    if device_session:
        # Device is known - return device token for direct login
        return {
            "message": "Trusted device detected",
            "device_token": device_session.device_token,
            "requires_otp": False
        }
    
    # Device is new or expired - require OTP
    await send_otp_email(email)
    
    return {
        "message": "OTP sent to your email (check server console if email not configured)",
        "requires_otp": True
    }

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
    
    # Create device fingerprint and check for existing session
    device_fingerprint = generate_device_fingerprint(ip_address, user_agent)
    
    # Check if device session exists
    device_session = db.query(DeviceSession).filter(
        DeviceSession.user_id == user.id,
        DeviceSession.device_fingerprint == device_fingerprint
    ).first()
    
    # Create or update device session (30 days)
    if device_session:
        # Update existing session
        device_session.last_used_at = datetime.utcnow()
        device_session.expires_at = datetime.utcnow() + timedelta(days=30)
        device_session.ip_address = ip_address
        device_session.user_agent = user_agent[:500] if user_agent else None
        device_session.device_type = device_type
    else:
        # Create new device session
        device_token = generate_device_token()
        device_session = DeviceSession(
            user_id=user.id,
            device_fingerprint=device_fingerprint,
            device_token=device_token,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            device_type=device_type,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(device_session)
    
    db.commit()
    db.refresh(device_session)
    
    # Create access token (30 days for trusted devices)
    access_token_expires = timedelta(days=30)  # 30 days for device-based login
    access_token = create_access_token(
        data={
            "sub": user.email, 
            "user_id": user.id, 
            "role": user.role.value,
            "device_token": device_session.device_token  # Include device token in JWT
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "device_token": device_session.device_token  # Return device token for frontend storage
    }

@router.post("/device/login", response_model=Token)
async def device_login_endpoint(
    request: DeviceLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Login using device token (no OTP required for trusted devices)"""
    email = request.email.lower()
    
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
    
    # Clean up expired device sessions for this user
    db.query(DeviceSession).filter(
        DeviceSession.user_id == user.id,
        DeviceSession.expires_at <= datetime.utcnow()
    ).delete()
    db.commit()
    
    # Verify device token
    device_session = db.query(DeviceSession).filter(
        DeviceSession.user_id == user.id,
        DeviceSession.device_token == request.device_token,
        DeviceSession.expires_at > datetime.utcnow()
    ).first()
    
    if not device_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired device token. Please login with OTP."
        )
    
    # Verify device fingerprint matches (security check)
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")
    device_fingerprint = generate_device_fingerprint(ip_address, user_agent)
    
    if device_session.device_fingerprint != device_fingerprint:
        # Device fingerprint changed - require OTP for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device changed. Please login with OTP."
        )
    
    # Update last used timestamp
    device_session.last_used_at = datetime.utcnow()
    db.commit()
    
    # Capture login information
    device_type = detect_device_type(user_agent)
    
    # Log login
    login_log = LoginLog(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        device_type=device_type
    )
    db.add(login_log)
    db.commit()
    
    # Create access token (30 days)
    access_token_expires = timedelta(days=30)
    access_token = create_access_token(
        data={
            "sub": user.email, 
            "user_id": user.id, 
            "role": user.role.value,
            "device_token": device_session.device_token
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "device_token": device_session.device_token
    }


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user
from app.models import User, PremiumRequest, PremiumStatus, Upload, UsageLog, FileType, LoginLog
from app.schemas import UserResponse, PremiumRequestCreate, PremiumRequestResponse, UserProfileResponse
from app.config import settings
from app.generation_tracker import get_daily_generation_stats
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

router = APIRouter()

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log user logout time"""
    from datetime import datetime
    
    # Find the most recent login log for this user that doesn't have a logout time
    login_log = db.query(LoginLog).filter(
        LoginLog.user_id == current_user.id,
        LoginLog.logout_at.is_(None)
    ).order_by(LoginLog.login_at.desc()).first()
    
    if login_log:
        login_log.logout_at = datetime.utcnow()
        db.commit()
        print(f"✅ Logged logout for user: {current_user.email} at {login_log.logout_at}")
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile with usage statistics"""
    
    # Get premium request date
    premium_request = db.query(PremiumRequest).filter(
        PremiumRequest.user_id == current_user.id
    ).order_by(PremiumRequest.requested_at.desc()).first()
    
    premium_request_date = premium_request.requested_at if premium_request else None
    
    # Calculate usage statistics
    from datetime import datetime, timedelta
    
    # Get current month start
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    # Calculate remaining quotas (use database fields as source of truth)
    is_premium = (
        current_user.premium_status == PremiumStatus.APPROVED and
        current_user.premium_valid_until and
        current_user.premium_valid_until > datetime.utcnow()
    )
    
    if is_premium:
        pdf_limit = settings.PREMIUM_PDF_QUOTA
        image_limit = settings.PREMIUM_IMAGE_QUOTA
        # Use quota fields as source of truth to ensure consistency with Dashboard
        pdf_remaining = current_user.upload_quota_remaining
        image_remaining = current_user.image_quota_remaining
    else:
        pdf_limit = 1  # Free users: 1 per day
        image_limit = 0  # Free users: no images
        pdf_remaining = 0
        image_remaining = 0
    
    # Calculate used count from limit and remaining (ensures consistency)
    # This ensures profile tab and upload tab show matching counts
    pdf_uploads_used = max(0, pdf_limit - pdf_remaining)
    image_uploads_used = max(0, image_limit - image_remaining)
    
    # Calculate monthly reset date based on premium activation date (purchase date)
    if is_premium:
        # Get the approved premium request to find activation date
        approved_request = db.query(PremiumRequest).filter(
            PremiumRequest.user_id == current_user.id,
            PremiumRequest.status == PremiumStatus.APPROVED
        ).order_by(PremiumRequest.reviewed_at.desc()).first()
        
        if approved_request and approved_request.reviewed_at:
            # Use the day of month from when premium was activated (purchased)
            activation_date = approved_request.reviewed_at
            reset_day = activation_date.day
            
            # Calculate next reset date (same day of month as activation)
            if now.day >= reset_day:
                # This month's reset day has passed, next reset is next month
                if now.month == 12:
                    next_reset = datetime(now.year + 1, 1, reset_day)
                else:
                    next_reset = datetime(now.year, now.month + 1, reset_day)
            else:
                # This month's reset day hasn't come yet
                next_reset = datetime(now.year, now.month, reset_day)
            
            monthly_reset_date = next_reset.isoformat()
            monthly_reset_day = reset_day
        else:
            # Fallback: use premium_valid_until day if no activation date found
            if current_user.premium_valid_until:
                reset_day = current_user.premium_valid_until.day
                if now.day >= reset_day:
                    if now.month == 12:
                        next_reset = datetime(now.year + 1, 1, reset_day)
                    else:
                        next_reset = datetime(now.year, now.month + 1, reset_day)
                else:
                    next_reset = datetime(now.year, now.month, reset_day)
                monthly_reset_date = next_reset.isoformat()
                monthly_reset_day = reset_day
            else:
                # Fallback to 1st of month
                if now.month == 12:
                    next_reset = datetime(now.year + 1, 1, 1)
                else:
                    next_reset = datetime(now.year, now.month + 1, 1)
                monthly_reset_date = next_reset.isoformat()
                monthly_reset_day = 1
    else:
        # Free users: reset on 1st of each month
        if now.month == 12:
            next_reset = datetime(now.year + 1, 1, 1)
        else:
            next_reset = datetime(now.year, now.month + 1, 1)
        monthly_reset_date = next_reset.isoformat()
        monthly_reset_day = 1
    
    # Get daily generation stats
    generation_stats = get_daily_generation_stats(db, current_user.id)
    
    # Calculate total questions based on upload quotas
    # Formula: (PDF uploads remaining × QUESTIONS_PER_PDF_UPLOAD) + (Image uploads remaining × QUESTIONS_PER_IMAGE_UPLOAD) = Total questions available
    # Premium: 15 PDF × 20 = 300, 20 Image × 20 = 400, Total = 700 questions
    if is_premium:
        # Use config values to ensure consistency
        pdf_questions_per_upload = settings.QUESTIONS_PER_PDF_UPLOAD  # Default: 20
        image_questions_per_upload = settings.QUESTIONS_PER_IMAGE_UPLOAD  # Default: 20
        
        pdf_questions_available = pdf_remaining * pdf_questions_per_upload  # PDF uploads × 20
        image_questions_available = image_remaining * image_questions_per_upload  # Image uploads × 20
        questions_remaining = pdf_questions_available + image_questions_available
        
        questions_limit = settings.PREMIUM_TOTAL_QUESTIONS_LIMIT  # 700 questions total
        questions_used = questions_limit - questions_remaining
    else:
        questions_limit = 0
        questions_used = 0
        questions_remaining = 0
    
    usage_stats = {
        "pdf_uploads": {
            "used": pdf_uploads_used,
            "remaining": pdf_remaining,
            "limit": pdf_limit
        },
        "image_uploads": {
            "used": image_uploads_used,
            "remaining": image_remaining,
            "limit": image_limit
        },
        "generations": {
            "used": generation_stats.get("used", 0),
            "remaining": generation_stats.get("remaining", 0),
            "limit": generation_stats.get("limit", 0),
            "reset_time": generation_stats.get("reset_time"),
            "percentage": generation_stats.get("percentage", 0)
        },
        "questions": {
            "used": questions_used,
            "remaining": questions_remaining,
            "limit": questions_limit
        },
        "monthly_reset_date": monthly_reset_date,
        "monthly_reset_day": monthly_reset_day
    }
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
        "created_at": current_user.created_at,
        "premium_status": current_user.premium_status.value,
        "premium_valid_until": current_user.premium_valid_until,
        "premium_request_date": premium_request_date,
        "usage_stats": usage_stats
    }

@router.post("/request-premium", response_model=PremiumRequestResponse)
async def request_premium(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request premium access"""
    
    # Check if already has active premium
    if (
        current_user.premium_status == PremiumStatus.APPROVED and
        current_user.premium_valid_until and
        current_user.premium_valid_until > datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has active premium access"
        )
    
    # Check if pending request exists
    pending_request = db.query(PremiumRequest).filter(
        PremiumRequest.user_id == current_user.id,
        PremiumRequest.status == PremiumStatus.PENDING
    ).first()
    
    if pending_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Premium request already pending"
        )
    
    # Create request
    premium_request = PremiumRequest(
        user_id=current_user.id,
        status=PremiumStatus.PENDING
    )
    db.add(premium_request)
    
    current_user.premium_status = PremiumStatus.PENDING
    db.commit()
    db.refresh(premium_request)
    
    # Return response in correct format
    return {
        "id": premium_request.id,
        "user_id": premium_request.user_id,
        "user_email": current_user.email,
        "status": premium_request.status.value,
        "requested_at": premium_request.requested_at,
        "reviewed_at": premium_request.reviewed_at
    }

@router.get("/generation-stats")
async def get_generation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily generation statistics for current user"""
    stats = get_daily_generation_stats(db, current_user.id)
    return stats


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user
from app.models import User, PremiumRequest, PremiumStatus, Upload, UsageLog, FileType, LoginLog, DeviceSession
from app.schemas import UserResponse, PremiumRequestCreate, PremiumRequestResponse, UserProfileResponse
from app.config import settings
from app.generation_tracker import get_daily_generation_stats
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

router = APIRouter()

@router.post("/logout")
async def logout_user(
    logout_all_devices: bool = False,  # Optional: logout from all devices
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
    
    # If logout_all_devices is True, remove all device sessions
    if logout_all_devices:
        deleted_count = db.query(DeviceSession).filter(
            DeviceSession.user_id == current_user.id
        ).delete()
        db.commit()
        print(f"✅ Removed {deleted_count} device session(s) for user: {current_user.email}")
    
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
    
    # Calculate total questions based on actual questions generated from QnASet records
    from app.models import QnASet
    
    # Count total questions from QnASets (after reset timestamp if set)
    if current_user.total_questions_reset_at:
        reset_timestamp_total = current_user.total_questions_reset_at
        qna_sets = db.query(QnASet).filter(
            QnASet.user_id == current_user.id,
            QnASet.created_at >= reset_timestamp_total
        ).all()
    else:
        qna_sets = db.query(QnASet).filter(
            QnASet.user_id == current_user.id
        ).all()
    
    questions_used = 0
    for qna_set in qna_sets:
        if qna_set.qna_json and isinstance(qna_set.qna_json, dict):
            questions = qna_set.qna_json.get("questions", [])
            if isinstance(questions, list):
                questions_used += len(questions)
    
    # Count daily questions (questions generated after reset timestamp)
    today_start = datetime.combine(now.date(), datetime.min.time())
    # If reset timestamp is set and is today or later, use it
    if current_user.daily_questions_reset_at:
        if current_user.daily_questions_reset_at.date() >= now.date():
            reset_timestamp = current_user.daily_questions_reset_at
        else:
            # Reset timestamp is from a previous day, use today's start instead
            reset_timestamp = today_start
    else:
        reset_timestamp = today_start
    
    daily_qna_sets = db.query(QnASet).filter(
        QnASet.user_id == current_user.id,
        QnASet.created_at >= reset_timestamp
    ).all()
    
    daily_questions_used = 0
    for qna_set in daily_qna_sets:
        if qna_set.qna_json and isinstance(qna_set.qna_json, dict):
            questions = qna_set.qna_json.get("questions", [])
            if isinstance(questions, list):
                daily_questions_used += len(questions)
    
    # Set limits based on premium status - use user's actual limit fields (can be customized by admin)
    if is_premium:
        # Use user's actual limit fields (defaults to 700 and 50 if not set, but can be customized by admin)
        questions_limit = current_user.total_questions_limit or settings.PREMIUM_TOTAL_QUESTIONS_LIMIT
        daily_questions_limit = current_user.daily_questions_limit or settings.PREMIUM_DAILY_GENERATION_LIMIT
        questions_remaining = max(0, questions_limit - questions_used)
    else:
        questions_limit = 0
        daily_questions_limit = 0
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
        "daily_questions": {
            "used": daily_questions_used,
            "remaining": max(0, daily_questions_limit - daily_questions_used),
            "limit": daily_questions_limit
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


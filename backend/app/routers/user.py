from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user
from app.models import User, PremiumRequest, PremiumStatus, Upload, UsageLog, FileType, LoginLog, QnASet, CreditRequest, CreditRequestStatus
from app.schemas import (
    UserResponse, PremiumRequestCreate, PremiumRequestResponse, UserProfileResponse,
    CreditRequestCreate, CreditRequestResponse
)
from app.config import settings
from app.generation_tracker import get_daily_question_stats
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
    
    # Check premium status
    is_premium = (
        current_user.premium_status == PremiumStatus.APPROVED and
        current_user.premium_valid_until and
        current_user.premium_valid_until > datetime.utcnow()
    )
    
    # Question-based quotas (no PDF/image quotas)
    # PDF and image uploads are unlimited, but generation is limited by questions
    pdf_limit = 0  # No limit
    image_limit = 0  # No limit
    pdf_remaining = 0
    image_remaining = 0
    pdf_uploads_used = 0
    image_uploads_used = 0
    
    # Calculate monthly reset date based on validity expiry date
    if is_premium:
        # Use premium_valid_until (validity expiry date) as the base for monthly reset
        if current_user.premium_valid_until:
            # Use the day of month from validity expiry date
            validity_date = current_user.premium_valid_until
            reset_day = validity_date.day
            
            # Calculate next reset date (same day of month as validity expiry)
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
            # Fallback to 1st of month if no validity date
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
    
    # Get daily question stats (not generation stats)
    from app.generation_tracker import get_daily_question_stats
    daily_question_stats = get_daily_question_stats(db, current_user.id)
    
<<<<<<< HEAD
    # Calculate total questions based on ACTUAL questions generated (not upload quotas)
    # Count actual questions from all QnASet records for this user
    if is_premium:
        # Base limit + bonus credits granted by admin
        base_limit = settings.PREMIUM_TOTAL_QUESTIONS_LIMIT  # 700 questions base
        bonus_questions = current_user.bonus_questions or 0  # Additional credits
        questions_limit = base_limit + bonus_questions  # Effective limit
        
        # Count actual questions generated from all QnASet records
        qna_sets = db.query(QnASet).filter(QnASet.user_id == current_user.id).all()
        questions_used = 0
        for qna_set in qna_sets:
            if qna_set.qna_json and isinstance(qna_set.qna_json, dict):
                questions = qna_set.qna_json.get("questions", [])
                if isinstance(questions, list):
                    questions_used += len(questions)
        
=======
    # Calculate total questions (700 questions per purchase for premium)
    if is_premium:
        questions_limit = current_user.questions_limit if current_user.questions_limit > 0 else 700
        questions_used = current_user.questions_used if current_user.questions_used else 0
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
        questions_remaining = max(0, questions_limit - questions_used)
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
        "daily_questions": {
            "used": daily_question_stats.get("used", 0),
            "remaining": daily_question_stats.get("remaining", 0),
            "limit": daily_question_stats.get("limit", 0),
            "reset_time": daily_question_stats.get("reset_time"),
            "percentage": daily_question_stats.get("percentage", 0)
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

@router.post("/request-credits", response_model=CreditRequestResponse)
async def request_credits(
    request: CreditRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request additional question credits"""
    
    # Validate requested credits
    if request.requested_credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested credits must be greater than 0"
        )
    
    if request.requested_credits > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 credits can be requested at once"
        )
    
    # Check if pending request exists
    pending_request = db.query(CreditRequest).filter(
        CreditRequest.user_id == current_user.id,
        CreditRequest.status == CreditRequestStatus.PENDING.value
    ).first()
    
    if pending_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit request already pending. Please wait for admin review."
        )
    
    # Create request
    credit_request = CreditRequest(
        user_id=current_user.id,
        requested_credits=request.requested_credits,
        status=CreditRequestStatus.PENDING.value,  # Use .value to ensure lowercase string is stored
        user_notes=request.user_notes
    )
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)
    
    return {
        "id": credit_request.id,
        "user_id": credit_request.user_id,
        "user_email": current_user.email,
        "requested_credits": credit_request.requested_credits,
        "status": credit_request.status,  # Already a string value (not an enum)
        "requested_at": credit_request.requested_at,
        "reviewed_at": credit_request.reviewed_at,
        "user_notes": credit_request.user_notes,
        "notes": credit_request.notes
    }

@router.get("/generation-stats")
async def get_generation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily question statistics for current user"""
    stats = get_daily_question_stats(db, current_user.id)
    return stats


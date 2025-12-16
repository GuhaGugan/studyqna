"""
Daily Generation Limit Tracking and Error Logging
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date
from app.models import DailyGenerationUsage, User
from app.config import settings
import logging
import traceback
from typing import Optional

# Configure logging
import os
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_daily_generation_limit(user: User) -> int:
    """Get daily generation limit for a user based on their premium status"""
    from datetime import datetime
    is_premium = (
        user.premium_status.value == "approved" and
        user.premium_valid_until and
        user.premium_valid_until > datetime.utcnow()
    )
    
    if is_premium:
        limit = settings.PREMIUM_DAILY_GENERATION_LIMIT
        # Debug: Log the limit being used
        logger.info(f"📊 Premium daily generation limit for user {user.id}: {limit}")
        return limit
    else:
        limit = settings.FREE_DAILY_GENERATION_LIMIT
        logger.info(f"📊 Free daily generation limit for user {user.id}: {limit}")
        return limit

def check_daily_generation_limit(db: Session, user: User) -> tuple[bool, int, int, str]:
    """
    Check if user has exceeded daily generation limit
    
    Returns:
        (can_generate: bool, used: int, limit: int, message: str)
    """
    try:
        # Get today's date (UTC, date only)
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Get or create today's usage record
        usage = db.query(DailyGenerationUsage).filter(
            and_(
                DailyGenerationUsage.user_id == user.id,
                func.date(DailyGenerationUsage.usage_date) == today
            )
        ).first()
        
        if not usage:
            # Create new record for today
            usage = DailyGenerationUsage(
                user_id=user.id,
                usage_date=today_start,
                generation_count=0,
                last_reset_at=datetime.utcnow()
            )
            db.add(usage)
            db.commit()
            db.refresh(usage)
        
        # Get user's daily limit
        limit = get_daily_generation_limit(user)
        used = usage.generation_count
        
        # Check if limit exceeded
        if used >= limit:
            return (
                False,
                used,
                limit,
                f"Daily generation limit reached. You have used {used} of {limit} generations today. Your limit resets at midnight UTC."
            )
        
        # Check if approaching limit (80% warning)
        if used >= int(limit * 0.8):
            return (
                True,
                used,
                limit,
                f"Warning: You have used {used} of {limit} generations today ({int(used/limit*100)}%). Limit resets at midnight UTC."
            )
        
        return (
            True,
            used,
            limit,
            f"You have {limit - used} generations remaining today."
        )
    
    except Exception as e:
        logger.error(f"Error checking daily generation limit for user {user.id}: {str(e)}")
        logger.error(traceback.format_exc())
        # On error, allow generation (fail open) but log the error
        return (True, 0, get_daily_generation_limit(user), "")

def increment_daily_generation_count(db: Session, user_id: int) -> bool:
    """
    Increment daily generation count for a user
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Get or create today's usage record
        usage = db.query(DailyGenerationUsage).filter(
            and_(
                DailyGenerationUsage.user_id == user_id,
                func.date(DailyGenerationUsage.usage_date) == today
            )
        ).first()
        
        if not usage:
            usage = DailyGenerationUsage(
                user_id=user_id,
                usage_date=today_start,
                generation_count=0,
                last_reset_at=datetime.utcnow()
            )
            db.add(usage)
        
        # Increment count
        usage.generation_count += 1
        usage.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error incrementing daily generation count for user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        return False

def get_daily_generation_stats(db: Session, user_id: int) -> dict:
    """
    Get daily generation statistics for a user
    
    Returns:
        dict with 'used', 'limit', 'remaining', 'reset_time'
    """
    try:
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Get today's usage
        usage = db.query(DailyGenerationUsage).filter(
            and_(
                DailyGenerationUsage.user_id == user_id,
                func.date(DailyGenerationUsage.usage_date) == today
            )
        ).first()
        
        # Get user to determine limit
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"used": 0, "limit": 0, "remaining": 0, "reset_time": None}
        
        limit = get_daily_generation_limit(user)
        used = usage.generation_count if usage else 0
        
        # Calculate reset time (next midnight UTC)
        tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = tomorrow.replace(day=tomorrow.day + 1)
        
        return {
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used),
            "reset_time": tomorrow.isoformat(),
            "percentage": int((used / limit * 100)) if limit > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"Error getting daily generation stats for user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return {"used": 0, "limit": 0, "remaining": 0, "reset_time": None, "percentage": 0}


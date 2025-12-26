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

def get_daily_question_limit(user: User) -> int:
    """Get daily question limit for a user based on their premium status"""
    is_premium = (
        user.premium_status.value == "approved" and
        user.premium_valid_until and
        user.premium_valid_until > datetime.utcnow()
    )
    
    if is_premium:

        limit = settings.PREMIUM_DAILY_GENERATION_LIMIT
        # Debug: Log the limit being used
        logger.info(f"Premium daily generation limit for user {user.id}: {limit}")
        return limit
    else:
        limit = settings.FREE_DAILY_GENERATION_LIMIT
        logger.info(f"Free daily generation limit for user {user.id}: {limit}")

        # Premium users: 50 questions per day
        limit = 50
        logger.info(f"Premium daily question limit for user {user.id}: {limit}")
        return limit
    else:
        # Free users: 0 questions (cannot generate)
        limit = 0
        logger.info(f"Free daily question limit for user {user.id}: {limit}")

        return limit

def check_daily_question_limit(db: Session, user: User, requested_questions: int) -> tuple[bool, int, int, str]:
    """
    Check if user has exceeded daily question limit
    
    Args:
        db: Database session
        user: User object
        requested_questions: Number of questions user wants to generate
    
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
                questions_count=0,
                last_reset_at=datetime.utcnow()
            )
            db.add(usage)
            db.commit()
            db.refresh(usage)
        
        # Get user's daily limit
        limit = get_daily_question_limit(user)
        used = usage.questions_count if usage else 0
        
        # Check if user is premium
        is_premium = (
            user.premium_status.value == "approved" and
            user.premium_valid_until and
            user.premium_valid_until > datetime.utcnow()
        )
        
        if not is_premium:
            return (
                False,
                used,
                limit,
                "Free users cannot generate questions. Please upgrade to premium."
            )
        
        # Check if user has already exceeded the limit
        if used >= limit:
            return (
                False,
                used,
                limit,
<<<<<<< HEAD
                f"Daily quota exceeded! You have used {used} of {limit} generations today. Your daily quota has been reached. Please try again tomorrow after midnight UTC."
=======
                f"Daily question limit reached. You have used {used} of {limit} questions today. Your daily limit has been exceeded. Please wait until midnight UTC for the limit to reset."
            )
        
        # Check if this request would exceed limit
        if used + requested_questions > limit:
            remaining = max(0, limit - used)
            return (
                False,
                used,
                limit,
                f"Daily question limit reached. You have used {used} of {limit} questions today. You can generate {remaining} more question(s) today. Your limit resets at midnight UTC."
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
            )
        
        # Check if approaching limit (80% warning)
        if used >= int(limit * 0.8):
            return (
                True,
                used,
                limit,
                f"Warning: You have used {used} of {limit} questions today ({int(used/limit*100)}%). Limit resets at midnight UTC."
            )
        
        return (
            True,
            used,
            limit,
            f"You have {limit - used} questions remaining today."
        )
    
    except Exception as e:
        logger.error(f"Error checking daily question limit for user {user.id}: {str(e)}")
        logger.error(traceback.format_exc())
        # On error, allow generation (fail open) but log the error
        return (True, 0, get_daily_question_limit(user), "")

<<<<<<< HEAD
def increment_daily_generation_count(db: Session, user_id: int, questions_count: int = 1) -> bool:
    """
    Increment daily generation count for a user by the actual number of questions generated
=======
def increment_daily_question_count(db: Session, user_id: int, questions_generated: int) -> bool:
    """
    Increment daily question count for a user
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
    
    Args:
        db: Database session
        user_id: User ID
<<<<<<< HEAD
        questions_count: Number of questions generated (default: 1 for backward compatibility)
=======
        questions_generated: Number of questions actually generated (not requested)
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
    
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
                questions_count=0,
                last_reset_at=datetime.utcnow()
            )
            db.add(usage)
        
<<<<<<< HEAD
        # Increment count by actual number of questions generated
        usage.generation_count += questions_count
=======
        # Increment question count (count actual questions generated, not requested)
        usage.questions_count += questions_generated
>>>>>>> 3369d74 (Update StudyQnA backend and frontend changes)
        usage.updated_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"Incremented daily generation count for user {user_id} by {questions_count} questions (new total: {usage.generation_count})")
        return True
    
    except Exception as e:
        logger.error(f"Error incrementing daily question count for user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        return False

def get_daily_question_stats(db: Session, user_id: int) -> dict:
    """
    Get daily question statistics for a user
    
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
            return {"used": 0, "limit": 0, "remaining": 0, "reset_time": None, "percentage": 0}
        
        limit = get_daily_question_limit(user)
        used = usage.questions_count if usage else 0
        
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
        logger.error(f"Error getting daily question stats for user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return {"used": 0, "limit": 0, "remaining": 0, "reset_time": None, "percentage": 0}

# Backward compatibility aliases
def get_daily_generation_limit(user: User) -> int:
    """Backward compatibility - returns question limit"""
    return get_daily_question_limit(user)

def check_daily_generation_limit(db: Session, user: User) -> tuple[bool, int, int, str]:
    """Backward compatibility - checks question limit with 0 requested"""
    return check_daily_question_limit(db, user, 0)

def increment_daily_generation_count(db: Session, user_id: int) -> bool:
    """Backward compatibility - increments by 1 question"""
    return increment_daily_question_count(db, user_id, 1)

def get_daily_generation_stats(db: Session, user_id: int) -> dict:
    """Backward compatibility - returns question stats"""
    return get_daily_question_stats(db, user_id)


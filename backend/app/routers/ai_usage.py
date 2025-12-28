from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.routers.dependencies import get_admin_user
from app.models import User, AIUsageLog
from app.config import settings
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import csv
import io

router = APIRouter()

class AIUsageResponse(BaseModel):
    id: int
    user_id: int | None
    user_email: str | None
    qna_set_id: int | None
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIUsageStatsResponse(BaseModel):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    usage_count: int
    current_month_tokens: int
    current_month_cost: float
    threshold: int
    threshold_percentage: float
    is_threshold_reached: bool
    daily_usage: List[Dict[str, Any]]
    monthly_usage: List[Dict[str, Any]]

def _get_period_start(period: str) -> Optional[datetime]:
    now = datetime.utcnow()
    period = (period or "all").lower()
    if period == "daily":
        return datetime(now.year, now.month, now.day)
    if period == "monthly":
        return datetime(now.year, now.month, 1)
    if period == "yearly":
        return datetime(now.year, 1, 1)
    return None

def _get_period_end(period: str, start: Optional[datetime]) -> Optional[datetime]:
    if not start:
        return None
    if period == "daily":
        return start + timedelta(days=1)
    if period == "monthly":
        year = start.year + (1 if start.month == 12 else 0)
        month = 1 if start.month == 12 else start.month + 1
        return datetime(year, month, 1)
    if period == "yearly":
        return datetime(start.year + 1, 1, 1)
    return None

@router.get("/usage", response_model=List[AIUsageResponse])
async def get_ai_usage_logs(
    limit: int = 200,
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get AI usage logs (admin only) with optional period filter"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(AIUsageLog)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(AIUsageLog.created_at >= start)
    if end:
        query = query.filter(AIUsageLog.created_at < end)

    logs = query.order_by(desc(AIUsageLog.created_at)).limit(limit).all()
    
    result = []
    for log in logs:
        user_email = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            user_email = user.email if user else None
        
        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": user_email,
            "qna_set_id": log.qna_set_id,
            "model": log.model,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "estimated_cost": log.estimated_cost,
            "created_at": log.created_at
        })
    
    return result

@router.get("/usage/export")
async def export_ai_usage_logs(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export AI usage logs as CSV (all/daily/monthly/yearly)"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(AIUsageLog)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(AIUsageLog.created_at >= start)
    if end:
        query = query.filter(AIUsageLog.created_at < end)

    logs = query.order_by(desc(AIUsageLog.created_at)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "User Email", "Model", "Prompt Tokens",
        "Completion Tokens", "Total Tokens", "Estimated Cost", "Created At"
    ])

    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        writer.writerow([
            log.id,
            user.email if user else "Unknown",
            log.model,
            log.prompt_tokens,
            log.completion_tokens,
            log.total_tokens,
            log.estimated_cost or "",
            log.created_at.isoformat() if log.created_at else ""
        ])

    output.seek(0)
    filename = f"ai_usage_{period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

@router.delete("/usage")
async def delete_ai_usage_logs(
    ids: List[int] = Body(..., embed=True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk delete AI usage logs"""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No log IDs provided")
    deleted = db.query(AIUsageLog).filter(AIUsageLog.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted, "ids": ids}

@router.get("/usage/stats", response_model=AIUsageStatsResponse)
async def get_ai_usage_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get AI usage statistics (admin only)"""
    # Get all-time stats
    all_time = db.query(
        func.sum(AIUsageLog.total_tokens).label('total_tokens'),
        func.sum(AIUsageLog.prompt_tokens).label('prompt_tokens'),
        func.sum(AIUsageLog.completion_tokens).label('completion_tokens'),
        func.count(AIUsageLog.id).label('count')
    ).first()
    
    total_tokens = all_time.total_tokens or 0
    prompt_tokens = all_time.prompt_tokens or 0
    completion_tokens = all_time.completion_tokens or 0
    usage_count = all_time.count or 0
    
    # Calculate total cost
    total_cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)
    
    # Get current month stats
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    current_month = db.query(
        func.sum(AIUsageLog.total_tokens).label('total_tokens'),
        func.sum(AIUsageLog.prompt_tokens).label('prompt_tokens'),
        func.sum(AIUsageLog.completion_tokens).label('completion_tokens')
    ).filter(
        AIUsageLog.created_at >= month_start
    ).first()
    
    current_month_tokens = current_month.total_tokens or 0
    current_month_prompt = current_month.prompt_tokens or 0
    current_month_completion = current_month.completion_tokens or 0
    current_month_cost = (current_month_prompt / 1000 * 0.01) + (current_month_completion / 1000 * 0.03)
    
    # Check threshold
    threshold = settings.AI_USAGE_THRESHOLD_TOKENS
    threshold_percentage = (current_month_tokens / threshold * 100) if threshold > 0 else 0
    is_threshold_reached = current_month_tokens >= threshold
    
    # Daily usage (last 30 days) with cost calculations
    daily_usage = []
    for i in range(30):
        date = now - timedelta(days=i)
        day_start = datetime(date.year, date.month, date.day)
        day_end = day_start + timedelta(days=1)
        
        day_stats = db.query(
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.sum(AIUsageLog.prompt_tokens).label('prompt_tokens'),
            func.sum(AIUsageLog.completion_tokens).label('completion_tokens'),
            func.count(AIUsageLog.id).label('count')
        ).filter(
            AIUsageLog.created_at >= day_start,
            AIUsageLog.created_at < day_end
        ).first()
        
        day_tokens = day_stats.tokens or 0
        day_prompt = day_stats.prompt_tokens or 0
        day_completion = day_stats.completion_tokens or 0
        day_cost = (day_prompt / 1000 * 0.01) + (day_completion / 1000 * 0.03)
        
        daily_usage.append({
            "date": day_start.isoformat(),
            "tokens": int(day_tokens),
            "prompt_tokens": int(day_prompt),
            "completion_tokens": int(day_completion),
            "cost": round(day_cost, 4),
            "count": day_stats.count or 0
        })
    
    daily_usage.reverse()  # Oldest first
    
    # Monthly usage (last 12 months) with cost calculations
    monthly_usage = []
    for i in range(12):
        month_date = now - timedelta(days=30 * i)
        month_start_date = datetime(month_date.year, month_date.month, 1)
        if month_date.month == 12:
            month_end_date = datetime(month_date.year + 1, 1, 1)
        else:
            month_end_date = datetime(month_date.year, month_date.month + 1, 1)
        
        month_stats = db.query(
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.sum(AIUsageLog.prompt_tokens).label('prompt_tokens'),
            func.sum(AIUsageLog.completion_tokens).label('completion_tokens'),
            func.count(AIUsageLog.id).label('count')
        ).filter(
            AIUsageLog.created_at >= month_start_date,
            AIUsageLog.created_at < month_end_date
        ).first()
        
        month_tokens = month_stats.tokens or 0
        month_prompt = month_stats.prompt_tokens or 0
        month_completion = month_stats.completion_tokens or 0
        month_cost = (month_prompt / 1000 * 0.01) + (month_completion / 1000 * 0.03)
        
        monthly_usage.append({
            "month": month_start_date.strftime("%Y-%m"),
            "tokens": int(month_tokens),
            "prompt_tokens": int(month_prompt),
            "completion_tokens": int(month_completion),
            "cost": round(month_cost, 4),
            "count": month_stats.count or 0
        })
    
    monthly_usage.reverse()  # Oldest first
    
    # Yearly usage (last 5 years) with cost calculations
    yearly_usage = []
    for i in range(5):
        year_date = now.year - i
        year_start_date = datetime(year_date, 1, 1)
        year_end_date = datetime(year_date + 1, 1, 1)
        
        year_stats = db.query(
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.sum(AIUsageLog.prompt_tokens).label('prompt_tokens'),
            func.sum(AIUsageLog.completion_tokens).label('completion_tokens'),
            func.count(AIUsageLog.id).label('count')
        ).filter(
            AIUsageLog.created_at >= year_start_date,
            AIUsageLog.created_at < year_end_date
        ).first()
        
        year_tokens = year_stats.tokens or 0
        year_prompt = year_stats.prompt_tokens or 0
        year_completion = year_stats.completion_tokens or 0
        year_cost = (year_prompt / 1000 * 0.01) + (year_completion / 1000 * 0.03)
        
        yearly_usage.append({
            "year": year_date,
            "tokens": int(year_tokens),
            "prompt_tokens": int(year_prompt),
            "completion_tokens": int(year_completion),
            "cost": round(year_cost, 4),
            "count": year_stats.count or 0
        })
    
    yearly_usage.reverse()  # Oldest first
    
    return {
        "total_tokens": int(total_tokens),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "total_cost": round(total_cost, 4),
        "usage_count": usage_count,
        "current_month_tokens": int(current_month_tokens),
        "current_month_cost": round(current_month_cost, 4),
        "threshold": threshold,
        "threshold_percentage": round(threshold_percentage, 2),
        "is_threshold_reached": is_threshold_reached,
        "daily_usage": daily_usage,
        "monthly_usage": monthly_usage,
        "yearly_usage": yearly_usage
    }

@router.post("/usage/threshold")
async def update_ai_usage_threshold(
    threshold: int,
    admin_user: User = Depends(get_admin_user)
):
    """Update AI usage threshold (admin only)"""
    if threshold < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold must be a positive integer"
        )
    
    # Update in settings (this would require restart, so we'll store in database or env)
    # For now, return success and note that .env needs to be updated
    return {
        "message": "Threshold update requires .env file update and server restart",
        "new_threshold": threshold,
        "note": "Update AI_USAGE_THRESHOLD_TOKENS in .env file and restart server"
    }



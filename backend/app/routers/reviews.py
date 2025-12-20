from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user, get_admin_user
from app.models import User, Review
from app.schemas import ReviewCreate, ReviewResponse
from typing import List, Optional
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import csv
import io

router = APIRouter()

@router.post("/submit", response_model=ReviewResponse)
async def submit_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a review/feedback"""
    
    # Validate rating
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Create review
    new_review = Review(
        user_id=current_user.id,
        rating=review.rating,
        message=review.message
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return {
        "id": new_review.id,
        "user_id": new_review.user_id,
        "user_email": current_user.email,
        "rating": new_review.rating,
        "message": new_review.message,
        "created_at": new_review.created_at
    }

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

@router.get("/admin/reviews", response_model=List[ReviewResponse])
async def get_all_reviews(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all reviews (admin only) with optional period filter"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(Review)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(Review.created_at >= start)
    if end:
        query = query.filter(Review.created_at < end)

    reviews = query.order_by(Review.created_at.desc()).all()
    
    result = []
    for review in reviews:
        user = db.query(User).filter(User.id == review.user_id).first()
        result.append({
            "id": review.id,
            "user_id": review.user_id,
            "user_email": user.email if user else "Unknown",
            "rating": review.rating,
            "message": review.message,
            "created_at": review.created_at
        })
    
    return result

@router.get("/admin/reviews/export")
async def export_reviews(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export reviews as CSV"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(Review)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(Review.created_at >= start)
    if end:
        query = query.filter(Review.created_at < end)

    reviews = query.order_by(Review.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User Email", "Rating", "Message", "Created At"])
    for review in reviews:
        user = db.query(User).filter(User.id == review.user_id).first()
        writer.writerow([
            review.id,
            user.email if user else "Unknown",
            review.rating,
            review.message,
            review.created_at.isoformat() if review.created_at else ""
        ])

    output.seek(0)
    filename = f"reviews_{period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

@router.delete("/admin/reviews/bulk")
async def delete_reviews_bulk(
    ids: List[int] = Body(..., embed=True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk delete reviews (admin only)"""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No review IDs provided")
    deleted = db.query(Review).filter(Review.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted, "ids": ids}

@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a review (admin only)"""
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    db.delete(review)
    db.commit()
    
    return {"message": "Review deleted successfully", "review_id": review_id}


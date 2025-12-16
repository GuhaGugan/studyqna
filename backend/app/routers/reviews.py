from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user, get_admin_user
from app.models import User, Review
from app.schemas import ReviewCreate, ReviewResponse
from typing import List

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

@router.get("/admin/reviews", response_model=List[ReviewResponse])
async def get_all_reviews(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all reviews (admin only)"""
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    
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


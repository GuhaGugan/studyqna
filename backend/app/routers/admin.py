
from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.routers.dependencies import get_admin_user
from app.models import (
    User, PremiumRequest, PremiumStatus, 
    UsageLog, AuditLog, UserRole, Upload, FileType, LoginLog, ErrorLog,
    CreditRequest, CreditRequestStatus
)
from app.schemas import (
    PremiumRequestResponse, PremiumRequestApprove,
    UserQuotaAdjust, UsageLogResponse, LoginLogResponse,
    CreditRequestResponse, CreditRequestApprove
)
from app.config import settings
from app.storage_service import read_file
from app.error_logger import get_error_stats
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import csv
import io

router = APIRouter()

# Helpers
def _get_period_start(period: str) -> Optional[datetime]:
    """Return the datetime start (UTC midnight boundaries) for the given period."""
    now = datetime.utcnow()
    period = (period or "all").lower()
    # normalize to start-of-period in UTC
    if period == "daily":
        return datetime(now.year, now.month, now.day)
    if period == "monthly":
        return datetime(now.year, now.month, 1)
    if period == "yearly":
        return datetime(now.year, 1, 1)
    return None  # all

def _get_period_end(period: str, start: Optional[datetime]) -> Optional[datetime]:
    """Return the exclusive end datetime for the given period (UTC)."""
    if not start:
        return None
    if period == "daily":
        return start + timedelta(days=1)
    if period == "monthly":
        # next month start
        year = start.year + (1 if start.month == 12 else 0)
        month = 1 if start.month == 12 else start.month + 1
        return datetime(year, month, 1)
    if period == "yearly":
        return datetime(start.year + 1, 1, 1)
    return None

@router.get("/premium-requests", response_model=List[PremiumRequestResponse])
async def list_premium_requests(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all premium requests"""
    requests = db.query(PremiumRequest).filter(
        PremiumRequest.status == PremiumStatus.PENDING
    ).order_by(PremiumRequest.requested_at.desc()).all()
    
    # Add user email to response
    result = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "user_email": user.email if user else "Unknown",
            "status": req.status,  # Already a string value (not an enum)
            "requested_at": req.requested_at,
            "reviewed_at": req.reviewed_at
        })
    
    return result

@router.post("/premium-requests/{request_id}/approve")
async def approve_premium_request(
    request_id: int,
    approval: PremiumRequestApprove,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve premium request"""
    premium_request = db.query(PremiumRequest).filter(
        PremiumRequest.id == request_id
    ).first()
    
    if not premium_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premium request not found"
        )
    
    if premium_request.status != PremiumStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already processed"
        )
    
    # Get user
    user = db.query(User).filter(User.id == premium_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Approve premium
    premium_request.status = PremiumStatus.APPROVED
    premium_request.reviewed_at = datetime.utcnow()
    premium_request.reviewed_by = admin_user.id
    premium_request.notes = approval.notes
    
    user.premium_status = PremiumStatus.APPROVED
    user.premium_valid_until = datetime.utcnow() + timedelta(days=settings.PREMIUM_VALIDITY_DAYS)
    # Set question-based quotas (700 questions per purchase)
    user.questions_limit = 700
    user.questions_used = 0
    # Keep old fields for backward compatibility (but not used)
    user.upload_quota_remaining = 0
    user.image_quota_remaining = 0
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="approve_premium",
        target_user_id=user.id,
        details={"request_id": request_id, "notes": approval.notes}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "Premium access approved", "user_id": user.id}

@router.post("/premium-requests/{request_id}/reject")
async def reject_premium_request(
    request_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reject premium request"""
    premium_request = db.query(PremiumRequest).filter(
        PremiumRequest.id == request_id
    ).first()
    
    if not premium_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premium request not found"
        )
    
    if premium_request.status != PremiumStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already processed"
        )
    
    # Get user
    user = db.query(User).filter(User.id == premium_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Reject premium
    premium_request.status = PremiumStatus.REJECTED
    premium_request.reviewed_at = datetime.utcnow()
    premium_request.reviewed_by = admin_user.id
    
    user.premium_status = PremiumStatus.REJECTED
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="reject_premium",
        target_user_id=user.id,
        details={"request_id": request_id}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "Premium request rejected", "user_id": user.id}

@router.get("/credit-requests", response_model=List[CreditRequestResponse])
async def list_credit_requests(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all credit requests"""
    requests = db.query(CreditRequest).order_by(CreditRequest.requested_at.desc()).all()
    
    result = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        result.append({
            "id": req.id,
            "user_id": req.user_id,
            "user_email": user.email if user else "Unknown",
            "requested_credits": req.requested_credits,
            "status": req.status,  # Already a string value (not an enum)
            "requested_at": req.requested_at,
            "reviewed_at": req.reviewed_at,
            "user_notes": req.user_notes,
            "notes": req.notes
        })
    
    return result

@router.post("/credit-requests/{request_id}/approve")
async def approve_credit_request(
    request_id: int,
    approval: CreditRequestApprove,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve credit request and grant additional question credits"""
    credit_request = db.query(CreditRequest).filter(
        CreditRequest.id == request_id
    ).first()
    
    if not credit_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit request not found"
        )
    
    if credit_request.status != CreditRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already processed"
        )
    
    # Get user
    user = db.query(User).filter(User.id == credit_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Approve and grant credits
    credit_request.status = CreditRequestStatus.APPROVED.value
    credit_request.reviewed_at = datetime.utcnow()
    credit_request.reviewed_by = admin_user.id
    credit_request.notes = approval.notes
    
    # Add bonus credits to user
    user.bonus_questions = (user.bonus_questions or 0) + credit_request.requested_credits
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="approve_credit_request",
        target_user_id=user.id,
        details={
            "request_id": request_id,
            "credits_granted": credit_request.requested_credits,
            "total_bonus_credits": user.bonus_questions,
            "notes": approval.notes
        }
    )
    db.add(audit_log)
    
    db.commit()
    
    return {
        "message": f"Credit request approved. {credit_request.requested_credits} credits granted.",
        "user_id": user.id,
        "total_bonus_credits": user.bonus_questions
    }

@router.post("/credit-requests/{request_id}/reject")
async def reject_credit_request(
    request_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    notes: Optional[str] = Body(None)
):
    """Reject credit request"""
    credit_request = db.query(CreditRequest).filter(
        CreditRequest.id == request_id
    ).first()
    
    if not credit_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit request not found"
        )
    
    if credit_request.status != CreditRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already processed"
        )
    
    # Get user
    user = db.query(User).filter(User.id == credit_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Reject request
    credit_request.status = CreditRequestStatus.REJECTED.value
    credit_request.reviewed_at = datetime.utcnow()
    credit_request.reviewed_by = admin_user.id
    credit_request.notes = notes
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="reject_credit_request",
        target_user_id=user.id,
        details={"request_id": request_id, "notes": notes}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "Credit request rejected", "user_id": user.id}

@router.post("/users/{user_id}/switch-to-free")
async def switch_user_to_free(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Switch a premium user back to free account"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Switch to free
    user.premium_status = PremiumStatus.REJECTED
    user.premium_valid_until = None
    user.questions_limit = 0
    user.questions_used = 0
    # Keep old fields for backward compatibility (but not used)
    user.upload_quota_remaining = 0
    user.image_quota_remaining = 0
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="switch_to_free",
        target_user_id=user.id,
        details={"switched_by": admin_user.email}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "User switched back to free account", "user_id": user.id}

@router.post("/users/{user_id}/switch-to-premium")
async def switch_user_to_premium(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Switch a free user to premium account (manual upgrade)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Switch to premium
    user.premium_status = PremiumStatus.APPROVED
    user.premium_valid_until = datetime.utcnow() + timedelta(days=settings.PREMIUM_VALIDITY_DAYS)
    # Set question-based quotas (700 questions per purchase)
    user.questions_limit = 700
    user.questions_used = 0
    # Keep old fields for backward compatibility (but not used)
    user.upload_quota_remaining = 0
    user.image_quota_remaining = 0
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="switch_to_premium",
        target_user_id=user.id,
        details={"switched_by": admin_user.email, "manual_upgrade": True}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "User upgraded to premium account", "user_id": user.id}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user account (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Log audit BEFORE deletion (so we have a record)
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="delete_user",
        target_user_id=user.id,
        details={"deleted_by": admin_user.email, "deleted_user_email": user.email}
    )
    db.add(audit_log)
    db.flush()  # Ensure audit log is saved before user deletion

    # Explicitly delete all dependent records in correct order to avoid FK violations
    # This works even without CASCADE, and is safe with CASCADE (just redundant)
    from app.models import (
        PremiumRequest, Upload, QnASet, AIUsageLog, LoginLog, 
        UsageLog, Review, PdfSplitPart
    )
    
    # Get upload IDs first (needed for usage_logs cleanup)
    upload_ids = [u.id for u in db.query(Upload.id).filter(Upload.user_id == user_id).all()]
    
    # Delete in dependency order (children before parents)
    # 1. PDF split parts (depend on uploads)
    if upload_ids:
        db.query(PdfSplitPart).filter(PdfSplitPart.parent_upload_id.in_(upload_ids)).delete(synchronize_session=False)
    db.query(PdfSplitPart).filter(PdfSplitPart.user_id == user_id).delete(synchronize_session=False)
    
    # 2. Usage logs (depend on uploads and users)
    if upload_ids:
        db.query(UsageLog).filter(UsageLog.upload_id.in_(upload_ids)).delete(synchronize_session=False)
    db.query(UsageLog).filter(UsageLog.user_id == user_id).delete(synchronize_session=False)
    
    # 3. QnA sets (depend on uploads and users)
    db.query(QnASet).filter(QnASet.user_id == user_id).delete(synchronize_session=False)
    
    # 4. AI usage logs (depend on qna_sets and users)
    db.query(AIUsageLog).filter(AIUsageLog.user_id == user_id).delete(synchronize_session=False)
    
    # 5. Uploads (depend on users)
    db.query(Upload).filter(Upload.user_id == user_id).delete(synchronize_session=False)
    
    # 6. Premium requests (depend on users)
    db.query(PremiumRequest).filter(PremiumRequest.user_id == user_id).delete(synchronize_session=False)
    db.query(PremiumRequest).filter(PremiumRequest.reviewed_by == user_id).delete(synchronize_session=False)
    
    # 7. Login logs (depend on users)
    db.query(LoginLog).filter(LoginLog.user_id == user_id).delete(synchronize_session=False)
    
    # 8. Reviews (depend on users)
    db.query(Review).filter(Review.user_id == user_id).delete(synchronize_session=False)
    
    # 9. Audit logs with target_user_id (but keep admin_id logs for history)
    db.query(AuditLog).filter(AuditLog.target_user_id == user_id).delete(synchronize_session=False)
    
    # Now safe to delete the user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully", "user_id": user_id}

@router.get("/users")
async def list_users(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with their quotas (optional period filter on created_at)"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(User).filter(User.role == UserRole.USER)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(User.created_at >= start)
    if end:
        query = query.filter(User.created_at < end)

    users = query.all()    
    # Import here to avoid circular imports
    from app.generation_tracker import get_daily_question_stats
 (Update StudyQnA backend and frontend changes)
    
    result = []
    for user in users:
        # Get daily question stats
        daily_stats = get_daily_question_stats(db, user.id)
        
        result.append({
            "id": user.id,
            "email": user.email,
            "premium_status": user.premium_status.value,
            "premium_valid_until": user.premium_valid_until,
            "questions_used": user.questions_used if user.questions_used else 0,
            "questions_limit": user.questions_limit if user.questions_limit > 0 else 700,
            "questions_remaining": max(0, (user.questions_limit if user.questions_limit > 0 else 700) - (user.questions_used if user.questions_used else 0)),
            "daily_questions_used": daily_stats.get("used", 0),
            "daily_questions_limit": daily_stats.get("limit", 0),
            "daily_questions_remaining": daily_stats.get("remaining", 0),
            "is_active": user.is_active,
            "created_at": user.created_at
        })
    
    return result

@router.get("/users/export")
async def export_users(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export users as CSV"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(User).filter(User.role == UserRole.USER)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(User.created_at >= start)
    if end:
        query = query.filter(User.created_at < end)

    users = query.order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Email", "Premium Status", "Premium Valid Until", "Upload Quota", "Image Quota", "Is Active", "Created At"])
    for user in users:

    writer.writerow(["ID", "Email", "Premium Status", "Premium Valid Until", "Questions Used", "Questions Limit", "Questions Remaining", "Is Active", "Created At"])
    for user in users:
        questions_limit = user.questions_limit if user.questions_limit > 0 else 700
        questions_used = user.questions_used if user.questions_used else 0
        questions_remaining = max(0, questions_limit - questions_used)
 
        writer.writerow([
            user.id,
            user.email,
            user.premium_status.value if user.premium_status else "",
            user.premium_valid_until.isoformat() if user.premium_valid_until else "",

            user.upload_quota_remaining,
            user.image_quota_remaining,

            questions_used,
            questions_limit,
            questions_remaining,

            user.is_active,
            user.created_at.isoformat() if user.created_at else ""
        ])

    output.seek(0)
    filename = f"users_{period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

@router.delete("/users")
async def delete_users(
    ids: List[int] = Body(..., embed=True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk delete users (dangerous)"""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user IDs provided")
    deleted = db.query(User).filter(User.id.in_(ids), User.role == UserRole.USER).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted, "ids": ids}

@router.get("/uploads")
async def list_all_uploads(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all uploads for admin (optional period filter)"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(Upload).filter(Upload.is_deleted == False)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(Upload.created_at >= start)
    if end:
        query = query.filter(Upload.created_at < end)

    uploads = query.order_by(Upload.created_at.desc()).all()
    
    result = []
    for upload in uploads:
        user = db.query(User).filter(User.id == upload.user_id).first()
        result.append({
            "id": upload.id,
            "user_id": upload.user_id,
            "user_email": user.email if user else "Unknown",
            "file_name": upload.file_name,
            "file_type": upload.file_type.value,
            "file_size": upload.file_size,
            "pages": upload.pages,
            "created_at": upload.created_at
        })
    
    return result

@router.get("/uploads/export")
async def export_uploads(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export uploads as CSV"""
    allowed = {"all", "daily", "monthly", "yearly"}
    period = (period or "all").lower()
    if period not in allowed:
        period = "all"

    query = db.query(Upload).filter(Upload.is_deleted == False)
    start = _get_period_start(period)
    end = _get_period_end(period, start)
    if start:
        query = query.filter(Upload.created_at >= start)
    if end:
        query = query.filter(Upload.created_at < end)

    uploads = query.order_by(Upload.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User Email", "File Name", "File Type", "File Size", "Pages", "Created At"])
    for upload in uploads:
        user = db.query(User).filter(User.id == upload.user_id).first()
        writer.writerow([
            upload.id,
            user.email if user else "Unknown",
            upload.file_name,
            upload.file_type.value if upload.file_type else "",
            upload.file_size,
            upload.pages or "",
            upload.created_at.isoformat() if upload.created_at else ""
        ])

    output.seek(0)
    filename = f"uploads_{period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

@router.delete("/uploads")
async def delete_uploads(
    ids: List[int] = Body(..., embed=True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk delete uploads (marks as deleted)"""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No upload IDs provided")
    delete_count = db.query(Upload).filter(Upload.id.in_(ids)).update({"is_deleted": True}, synchronize_session=False)
    db.commit()
    return {"deleted": delete_count, "ids": ids}

@router.get("/uploads/{upload_id}/view")
async def view_upload(
    upload_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Preview uploaded file (PDF or Image) - Admin only"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Read file
    try:
        file_content = read_file(upload.file_path)
        
        # Determine content type
        if upload.file_type == FileType.PDF:
            media_type = "application/pdf"
        elif upload.file_type == FileType.IMAGE:
            # Determine image type from file extension
            ext = os.path.splitext(upload.file_name)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                media_type = "image/jpeg"
            elif ext == '.png':
                media_type = "image/png"
            elif ext == '.gif':
                media_type = "image/gif"
            else:
                media_type = "image/jpeg"  # Default
        else:
            media_type = "application/octet-stream"
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{upload.file_name}"',
                "X-Content-Type-Options": "nosniff"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )

@router.post("/quota-adjust")
async def adjust_user_quota(
    adjustment: UserQuotaAdjust,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Adjust user quota"""
    user = db.query(User).filter(User.id == adjustment.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Adjust question-based quotas (PDF/image quotas are deprecated)
    if adjustment.questions_limit is not None:
        user.questions_limit = adjustment.questions_limit
    
    if adjustment.questions_used is not None:
        user.questions_used = max(0, adjustment.questions_used)
    
    if adjustment.extend_validity_days:
        if user.premium_valid_until:
            user.premium_valid_until += timedelta(days=adjustment.extend_validity_days)
        else:
            user.premium_valid_until = datetime.utcnow() + timedelta(days=adjustment.extend_validity_days)
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="adjust_quota",
        target_user_id=user.id,
        details={
            "questions_limit": adjustment.questions_limit,
            "questions_used": adjustment.questions_used,
            "extend_validity_days": adjustment.extend_validity_days
        }
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(user)
    
    questions_limit = user.questions_limit if user.questions_limit > 0 else 700
    questions_used = user.questions_used if user.questions_used else 0
    questions_remaining = max(0, questions_limit - questions_used)
    
    return {
        "message": "Quota adjusted",
        "user_id": user.id,
        "questions_limit": questions_limit,
        "questions_used": questions_used,
        "questions_remaining": questions_remaining
    }

@router.post("/users/{user_id}/reset-daily-questions")
async def reset_daily_questions(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reset daily question count for a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Reset today's daily question count
    from app.models import DailyGenerationUsage
    from datetime import datetime
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    usage = db.query(DailyGenerationUsage).filter(
        DailyGenerationUsage.user_id == user_id,
        func.date(DailyGenerationUsage.usage_date) == today
    ).first()
    
    if usage:
        usage.questions_count = 0
        usage.updated_at = datetime.utcnow()
        db.commit()
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="reset_daily_questions",
        target_user_id=user.id,
        details={"reset_by": admin_user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Daily question count reset successfully", "user_id": user.id}

@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Disable user account"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable admin user"
        )
    
    user.is_active = False
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="disable_user",
        target_user_id=user.id,
        details={}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "User disabled", "user_id": user.id}

@router.post("/users/{user_id}/enable")
async def enable_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Enable user account"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    
    # Log audit
    audit_log = AuditLog(
        admin_id=admin_user.id,
        action="enable_user",
        target_user_id=user.id,
        details={}
    )
    db.add(audit_log)
    
    db.commit()
    
    return {"message": "User enabled", "user_id": user.id}

@router.get("/usage-logs", response_model=List[UsageLogResponse])
async def get_usage_logs(
    user_id: int = None,
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get usage logs (optionally filtered by user and period)"""
    allowed_periods = {"all", "daily", "monthly", "yearly"}
    norm_period = (period or "all").lower()
    if norm_period not in allowed_periods:
        norm_period = "all"
    
    query = db.query(UsageLog)
    
    if user_id:
        query = query.filter(UsageLog.user_id == user_id)
    
    start = _get_period_start(norm_period)
    end = _get_period_end(norm_period, start)
    if start:
        query = query.filter(UsageLog.created_at >= start)
    if end:
        query = query.filter(UsageLog.created_at < end)
    
    logs = query.order_by(UsageLog.created_at.desc()).limit(200).all()
    
    # Add user email to each log
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
            "action": log.action,
            "pages": log.pages,
            "file_size": log.file_size,
            "created_at": log.created_at
        })
    
    return result

@router.get("/usage-logs/export")
async def export_usage_logs(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export usage logs as CSV (all, daily, monthly, yearly)"""
    allowed_periods = {"all", "daily", "monthly", "yearly"}
    norm_period = (period or "all").lower()
    if norm_period not in allowed_periods:
        norm_period = "all"
    
    query = db.query(UsageLog)
    start = _get_period_start(norm_period)
    end = _get_period_end(norm_period, start)
    if start:
        query = query.filter(UsageLog.created_at >= start)
    if end:
        query = query.filter(UsageLog.created_at < end)
    
    logs = query.order_by(UsageLog.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User Email", "Action", "Pages", "File Size", "Created At"])
    
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        writer.writerow([
            log.id,
            user.email if user else "Unknown",
            log.action or "",
            log.pages or "",
            log.file_size or "",
            log.created_at.isoformat() if log.created_at else ""
        ])
    
    output.seek(0)
    filename = f"usage_logs_{norm_period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.delete("/usage-logs")
async def delete_usage_logs(
    ids: List[int] = Body(..., embed=True, description="List of usage log IDs to delete"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk delete usage logs"""
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No log IDs provided")
    
    delete_count = db.query(UsageLog).filter(UsageLog.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    
    return {"deleted": delete_count, "ids": ids}

@router.get("/usage-logs/export")
async def export_usage_logs(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export usage logs as CSV (all, daily, monthly, yearly)"""
    query = db.query(UsageLog)
    start = _get_period_start(period)
    if start:
        query = query.filter(UsageLog.created_at >= start)

    logs = query.order_by(UsageLog.created_at.desc()).all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User Email", "Action", "Pages", "File Size (bytes)", "Created At"])

    for log in logs:
        user_email = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            user_email = user.email if user else None
        writer.writerow([
            log.id,
            user_email or "",
            log.action,
            log.pages or "",
            log.file_size or "",
            log.created_at.isoformat() if log.created_at else ""
        ])

    output.seek(0)
    filename = f"usage_logs_{period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/audit-logs")
async def get_audit_logs(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "admin_id": log.admin_id,
            "action": log.action,
            "target_user_id": log.target_user_id,
            "details": log.details,
            "created_at": log.created_at
        })
    
    return result

@router.get("/login-logs", response_model=List[LoginLogResponse])
async def get_login_logs(
    user_id: int = None,
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get login logs with optional user filter and time period (all/daily/monthly/yearly)"""
    allowed_periods = {"all", "daily", "monthly", "yearly"}
    norm_period = (period or "all").lower()
    if norm_period not in allowed_periods:
        norm_period = "all"

    query = db.query(LoginLog)
    
    if user_id:
        query = query.filter(LoginLog.user_id == user_id)
    
    start = _get_period_start(norm_period)
    end = _get_period_end(norm_period, start)
    if start:
        query = query.filter(LoginLog.login_at >= start)
    if end:
        query = query.filter(LoginLog.login_at < end)
    
    logs = query.order_by(LoginLog.login_at.desc()).limit(200).all()
    
    # Add user email to each log
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append({
            "id": log.id,
            "user_email": user.email if user else "Unknown",
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "device_type": log.device_type,
            "login_at": log.login_at,
            "logout_at": log.logout_at
        })
    
    return result

@router.delete("/login-logs")
async def delete_login_logs(
    ids: List[int] = Body(..., embed=True, description="List of login log IDs to delete"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Bulk delete login logs by IDs"""
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No log IDs provided"
        )
    
    delete_count = db.query(LoginLog).filter(LoginLog.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    
    return {
        "deleted": delete_count,
        "ids": ids
    }

@router.get("/login-logs/export")
async def export_login_logs(
    period: str = "all",
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export login logs as CSV (all, daily, monthly, yearly)"""
    allowed_periods = {"all", "daily", "monthly", "yearly"}
    norm_period = (period or "all").lower()
    if norm_period not in allowed_periods:
        norm_period = "all"

    query = db.query(LoginLog)
    start = _get_period_start(norm_period)
    end = _get_period_end(norm_period, start)
    if start:
        query = query.filter(LoginLog.login_at >= start)
    if end:
        query = query.filter(LoginLog.login_at < end)

    logs = query.order_by(LoginLog.login_at.desc()).all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User Email", "IP Address", "Device Type", "User Agent", "Login At", "Logout At"])

    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        writer.writerow([
            log.id,
            user.email if user else "Unknown",
            log.ip_address or "",
            log.device_type or "",
            (log.user_agent or "")[:200],  # avoid huge UA strings
            log.login_at.isoformat() if log.login_at else "",
            log.logout_at.isoformat() if log.logout_at else ""
        ])

    output.seek(0)
    filename = f"login_logs_{period}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/error-stats")
async def get_error_stats_endpoint(
    days: int = 7,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get error statistics for monitoring (admin only)"""
    if days < 1 or days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 90"
        )
    
    stats = get_error_stats(db, days)
    return stats

@router.get("/errors")
async def list_errors(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List error logs (admin only)"""
    query = db.query(ErrorLog)
    
    if severity:
        query = query.filter(ErrorLog.severity == severity)
    
    if resolved is not None:
        query = query.filter(ErrorLog.resolved == resolved)
    
    errors = query.order_by(ErrorLog.created_at.desc()).limit(limit).all()
    
    result = []
    for error in errors:
        user_email = None
        if error.user_id:
            user = db.query(User).filter(User.id == error.user_id).first()
            user_email = user.email if user else None
        
        result.append({
            "id": error.id,
            "user_id": error.user_id,
            "user_email": user_email,
            "error_type": error.error_type,
            "error_message": error.error_message,
            "endpoint": error.endpoint,
            "request_method": error.request_method,
            "ip_address": error.ip_address,
            "severity": error.severity,
            "resolved": error.resolved,
            "created_at": error.created_at.isoformat() if error.created_at else None
        })
    
    return result

@router.post("/errors/{error_id}/resolve")
async def resolve_error(
    error_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Mark an error as resolved (admin only)"""
    error = db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
    
    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error log not found"
        )
    
    error.resolved = True
    db.commit()
    
    return {"message": "Error marked as resolved", "error_id": error_id}

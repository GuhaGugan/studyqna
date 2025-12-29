from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user, get_premium_user
from app.models import User, Upload, FileType, UsageLog, PdfSplitPart
from app.schemas import UploadResponse, PdfSplitPartResponse, PdfSplitResponse, PdfSplitPartRenameRequest
from app.storage_service import save_file
# Image validation removed - only PDF uploads are supported
from app.pdf_split_service import split_pdf_into_parts, get_part_preview
from app.config import settings
from app.error_logger import log_api_error
from datetime import datetime
from PyPDF2 import PdfReader
import io
# Image processing imports removed - only PDF uploads are supported
import os
from typing import Tuple, List, Optional

router = APIRouter()

def count_pdf_pages(pdf_content: bytes) -> int:
    """Count pages in PDF"""
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        return len(pdf_reader.pages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PDF file: {str(e)}"
        )

# Image validation function removed - only PDF uploads are supported

@router.post("", response_model=UploadResponse)
async def upload_file(
    http_request: Request,
    file: UploadFile = File(...),
    subject: str = Form("general"),  # Subject selection: mathematics, english, science, social_science, general
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload PDF file with subject selection (Image uploads are not supported)"""
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
    
        # Determine file type - Only PDFs are supported
        content_type = file.content_type or ""
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        is_pdf = content_type == "application/pdf" or file_ext == ".pdf"
        
        if not is_pdf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        file_type = FileType.PDF
    
        # Validate size
        # For PDFs, allow up to MAX_BOOK_PDF_SIZE_MB for book splitting feature
        # Regular PDFs still limited to MAX_PDF_SIZE_MB, but larger ones can be split
        max_size = settings.MAX_BOOK_PDF_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF size exceeds {settings.MAX_BOOK_PDF_SIZE_MB}MB limit. Maximum size for book splitting is {settings.MAX_BOOK_PDF_SIZE_MB}MB."
            )
        
        # Check premium status for limits
        is_premium = (
            current_user.premium_status.value == "approved" and
            current_user.premium_valid_until and
            current_user.premium_valid_until > datetime.utcnow()
        )
        
        # PDF validation
        pages = count_pdf_pages(file_content)
        max_pages = settings.MAX_PDF_PAGES if is_premium else settings.MAX_FREE_PDF_PAGES
        
        # Determine if PDF is large enough for splitting (>6MB)
        is_large_pdf_for_splitting = file_size > (6 * 1024 * 1024)
        
        # Logic:
        # - PDFs ≤6MB: still subject to 40-page limit (premium) or 10-page limit (free)
        # - PDFs >6MB: can have up to 300 pages (will be split into parts)
        # - PDFs >300 pages: still blocked (too large even for splitting)
        if is_large_pdf_for_splitting:
            # Large PDFs (>6MB) can have up to 300 pages for splitting
            if pages > 300:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF exceeds 300 pages limit. Please split your book into smaller sections (max 300 pages) before uploading."
                )
        else:
            # Regular PDFs (≤6MB) are subject to normal page limits
            if pages > max_pages:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PDF exceeds {max_pages} pages limit. Please upload chapter-wise for large books."
                )
        
        # Check upload limits
        # Note: We now track by questions (700 total, 50 daily for premium) instead of PDF/image quotas
        # All users (free and premium) can upload unlimited PDFs
        # Limits are enforced by question generation (10 questions/generation, 10 daily for free users)
        # No upload quota check needed - unlimited uploads for everyone
        
        # Save file
        file_path = save_file(file_content, current_user.id, file_type.value, file.filename)
        
        # Validate subject
        valid_subjects = ["mathematics", "english", "tamil", "science", "social_science", "general"]
        if subject not in valid_subjects:
            subject = "general"  # Default to general if invalid
        
        # Subject detection is now done asynchronously after upload completes
        # This speeds up the upload process significantly
        detected_subject = None
        subject_mismatch_warning = None
        
        # Note: Subject detection moved to background to avoid blocking uploads
        # Users can still select subject manually, and detection can happen later if needed
        
        # Create upload record
        upload = Upload(
            user_id=current_user.id,
            file_name=file.filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            pages=pages if is_pdf else None,
            subject=subject  # Store selected subject (user's choice takes precedence)
        )
        db.add(upload)
        
        # Note: Quotas are now tracked by questions (700 total, 50 daily), not uploads
        # No need to decrement upload_quota_remaining or image_quota_remaining
        
        # Log usage
        usage_log = UsageLog(
            user_id=current_user.id,
            upload_id=None,  # Will be set after commit
            action="pdf_upload" if is_pdf else "image_upload",
            pages=pages if is_pdf else None,
            file_size=file_size
        )
        db.add(usage_log)
        
        db.commit()
        db.refresh(upload)
        
        usage_log.upload_id = upload.id
        db.commit()
        
        # Check if PDF is large enough to split (>6MB)
        if is_pdf and file_size > (6 * 1024 * 1024):
            # Mark as split-eligible (will be split on demand)
            # For now, just return the upload - splitting will be done via separate endpoint
            pass
        
        # Prepare response with subject validation info
        response_data = {
            "id": upload.id,
            "file_name": upload.file_name,
            "file_type": upload.file_type.value,
            "file_size": upload.file_size,
            "pages": upload.pages,
            "is_split": upload.is_split,
            "subject": upload.subject.value if hasattr(upload.subject, 'value') else str(upload.subject),
            "detected_subject": detected_subject if detected_subject != "general" else None,
            "subject_mismatch_warning": subject_mismatch_warning,
            "created_at": upload.created_at
        }
        
        return response_data
    
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Log error to database and application logs
        log_api_error(
            db,
            e,
            current_user.id,
            http_request,
            severity="error",
            additional_data={"filename": file.filename if file else None, "file_type": file_type.value if 'file_type' in locals() else None}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.delete("/{upload_id}")
async def delete_upload(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete upload (quota not refunded)"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    upload.is_deleted = True
    db.commit()
    
    return {"message": "Upload deleted"}

@router.get("", response_model=list[UploadResponse])
async def list_uploads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's uploads"""
    uploads = db.query(Upload).filter(
        Upload.user_id == current_user.id,
        Upload.is_deleted == False
    ).order_by(Upload.created_at.desc()).all()
    
    return uploads

# ==================== PDF SPLITTING ENDPOINTS ====================

@router.post("/{upload_id}/split", response_model=PdfSplitResponse)
async def split_pdf(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    target_size_mb: float = 6.0
):
    """
    Split a large PDF into smaller parts (~6MB each).
    Only works for PDFs larger than 6MB.
    """
    # Get the upload
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id,
        Upload.file_type == FileType.PDF,
        Upload.is_deleted == False
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF upload not found"
        )
    
    # Check if already split
    if upload.is_split:
        # Return existing parts
        parts = db.query(PdfSplitPart).filter(
            PdfSplitPart.parent_upload_id == upload_id
        ).order_by(PdfSplitPart.part_number).all()
        
        return PdfSplitResponse(
            parent_upload_id=upload_id,
            total_parts=len(parts),
            parts=[PdfSplitPartResponse.model_validate(p) for p in parts],
            message=f"PDF already split into {len(parts)} parts"
        )
    
    # Check if PDF is large enough to split
    if upload.file_size <= (6 * 1024 * 1024):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF is not large enough to split (must be >6MB)"
        )
    
    try:
        # Split the PDF
        parts_info = split_pdf_into_parts(
            upload.file_path,
            current_user.id,
            upload.file_name,
            target_size_mb
        )
        
        # Create database records for each part
        split_parts = []
        for part_info in parts_info:
            split_part = PdfSplitPart(
                parent_upload_id=upload.id,
                user_id=current_user.id,
                part_number=part_info["part_number"],
                file_name=part_info["file_name"],
                file_path=part_info["file_path"],
                file_size=part_info["file_size"],
                start_page=part_info["start_page"],
                end_page=part_info["end_page"],
                total_pages=part_info["total_pages"]
            )
            db.add(split_part)
            split_parts.append(split_part)
        
        # Mark upload as split
        upload.is_split = True
        db.commit()
        
        # Refresh all parts
        for part in split_parts:
            db.refresh(part)
        
        return PdfSplitResponse(
            parent_upload_id=upload.id,
            total_parts=len(split_parts),
            parts=[PdfSplitPartResponse.model_validate(p) for p in split_parts],
            message=f"PDF successfully split into {len(split_parts)} parts"
        )
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error splitting PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to split PDF: {str(e)}"
        )

@router.get("/{upload_id}/split-parts", response_model=List[PdfSplitPartResponse])
async def get_split_parts(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all split parts for a PDF upload"""
    # Verify upload belongs to user
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id,
        Upload.is_deleted == False
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Get all parts
    parts = db.query(PdfSplitPart).filter(
        PdfSplitPart.parent_upload_id == upload_id
    ).order_by(PdfSplitPart.part_number).all()
    
    return [PdfSplitPartResponse.model_validate(p) for p in parts]

@router.put("/split-parts/{part_id}/rename", response_model=PdfSplitPartResponse)
async def rename_split_part(
    part_id: int,
    request: PdfSplitPartRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rename a split part with custom name"""
    part = db.query(PdfSplitPart).filter(
        PdfSplitPart.id == part_id,
        PdfSplitPart.user_id == current_user.id
    ).first()
    
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Split part not found"
        )
    
    # Validate custom name
    if len(request.custom_name.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom name cannot be empty"
        )
    
    if len(request.custom_name) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom name must be less than 200 characters"
        )
    
    part.custom_name = request.custom_name.strip()
    db.commit()
    db.refresh(part)
    
    return PdfSplitPartResponse.model_validate(part)

@router.get("/split-parts/{part_id}/preview")
async def preview_split_part(
    part_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get preview (first 5 pages) of a split part"""
    part = db.query(PdfSplitPart).filter(
        PdfSplitPart.id == part_id,
        PdfSplitPart.user_id == current_user.id
    ).first()
    
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Split part not found"
        )
    
    try:
        preview_pdf = get_part_preview(part.file_path, max_pages=5)
        return Response(
            content=preview_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="preview_{part.file_name}"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.get("/split-parts/{part_id}/download")
async def download_split_part(
    part_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a split part as a regular upload (for QnA generation)"""
    part = db.query(PdfSplitPart).filter(
        PdfSplitPart.id == part_id,
        PdfSplitPart.user_id == current_user.id
    ).first()
    
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Split part not found"
        )
    
    # Create a temporary Upload record for this part so it can be used with QnA generation
    # This allows the part to work seamlessly with existing QnA endpoints
    from app.storage_service import read_file
    
    part_content = read_file(part.file_path)
    
    # Create upload record for this part
    part_upload = Upload(
        user_id=current_user.id,
        file_name=part.custom_name or part.file_name,
        file_path=part.file_path,
        file_type=FileType.PDF,
        file_size=part.file_size,
        pages=part.total_pages,
        is_deleted=False
    )
    db.add(part_upload)
    db.commit()
    db.refresh(part_upload)
    
    return UploadResponse.model_validate(part_upload)


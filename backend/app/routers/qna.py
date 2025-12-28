from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, Body, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.dependencies import get_current_user, get_premium_user
from app.models import User, QnASet, Upload
from app.schemas import QnAGenerateRequest, QnASetResponse
from app.ocr_service import extract_text_from_image, extract_text_from_pdf
from app.ai_service import generate_qna  # Keep for backward compatibility
from app.ai_pipeline import generate_qna_pipeline
from app.download_service import generate_pdf, generate_docx, generate_txt, _generate_pdf_playwright_async
from app.download_service import PLAYWRIGHT_AVAILABLE
from app.generation_tracker import check_daily_generation_limit, increment_daily_generation_count
from app.error_logger import log_api_error
from app.font_manager import detect_language
from app.models import PdfSplitPart
import asyncio
from app.config import settings
from typing import Optional

router = APIRouter()

@router.post("/generate", response_model=QnASetResponse)
async def generate_qna_endpoint(
    http_request: Request,
    request: QnAGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate Q/A from uploaded file or multiple split parts"""
    
    # Check daily generation limit BEFORE processing
    try:
        can_generate, used, limit, message = check_daily_generation_limit(db, current_user)
        if not can_generate:
            # Log the limit exceeded event
            try:
                log_api_error(
                    db,
                    HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message),
                    current_user.id,
                    http_request,
                    severity="warning"
                )
            except:
                pass  # Don't fail if logging fails
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )
    except HTTPException:
        raise
    except Exception as e:
        # Log error but don't block generation (fail open)
        try:
            log_api_error(db, e, current_user.id, http_request, severity="warning")
        except:
            pass
        # Continue with generation if limit check fails
    
    # Initialize selected_subject with default value
    selected_subject = "general"
    
    # Handle multi-select: if part_ids provided, use those instead of upload_id
    if request.part_ids and len(request.part_ids) > 0:
        # Multi-select mode: combine text from multiple parts
        from app.models import PdfSplitPart
        
        parts = db.query(PdfSplitPart).filter(
            PdfSplitPart.id.in_(request.part_ids),
            PdfSplitPart.user_id == current_user.id
        ).all()
        
        if len(parts) != len(request.part_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more split parts not found"
            )
        
        # Combine text from all selected parts and store part info for source tracking
        combined_text = []
        part_info_map = {}  # Map to store part info by part_number
        for part in sorted(parts, key=lambda p: p.part_number):
            part_text = extract_text_from_pdf(part.file_path)
            if part_text:
                part_marker = f"--- Part {part.part_number} (Pages {part.start_page}-{part.end_page}) ---"
                combined_text.append(f"\n\n{part_marker}\n\n")
                combined_text.append(part_text)
                # Store part info for source tracking
                part_info_map[part.part_number] = {
                    "part_number": part.part_number,
                    "start_page": part.start_page,
                    "end_page": part.end_page,
                    "marker": part_marker
                }
        
        text_content = "".join(combined_text)
        
        # Use the first part's parent upload for reference
        upload = db.query(Upload).filter(Upload.id == parts[0].parent_upload_id).first()
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent upload not found"
            )
        
        # Get subject from request or first part's parent upload (request takes precedence)
        first_part = parts[0]
        if first_part and first_part.parent_upload:
            parent_upload_subject = getattr(first_part.parent_upload, 'subject', None)
            if parent_upload_subject:
                # Handle both enum and string types
                parent_subject_value = parent_upload_subject.value if hasattr(parent_upload_subject, 'value') else str(parent_upload_subject)
            else:
                parent_subject_value = None
            selected_subject = request.subject if request.subject and request.subject != "general" else (parent_subject_value or "general")
        else:
            selected_subject = request.subject if request.subject and request.subject != "general" else "general"
    else:
        # Single upload mode (existing functionality)
        if not request.upload_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either upload_id or part_ids must be provided"
            )
        
        # Get upload
        upload = db.query(Upload).filter(
            Upload.id == request.upload_id,
            Upload.user_id == current_user.id,
            Upload.is_deleted == False
        ).first()
        
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found"
            )
        
        # Extract text
        if upload.file_type.value == "pdf":
            text_content = extract_text_from_pdf(upload.file_path)
        else:
            text_content = extract_text_from_image(upload.file_path)
        
        # Get subject from upload or request (request takes precedence)
        upload_subject = getattr(upload, 'subject', None)
        if upload_subject:
            # Handle both enum and string types
            upload_subject_value = upload_subject.value if hasattr(upload_subject, 'value') else str(upload_subject)
        else:
            upload_subject_value = None
        selected_subject = request.subject if request.subject and request.subject != "general" else (upload_subject_value or "general")
    
    # Check premium status (single check)
    from datetime import datetime
    is_premium = (
        current_user.premium_status.value == "approved" and
        current_user.premium_valid_until and
        current_user.premium_valid_until > datetime.utcnow()
    )
    
    # Note: We now track by questions (700 total, 50 daily) instead of PDF/image quotas
    # Upload quotas are no longer checked - users can upload unlimited files
    # Limits are enforced by total_questions_limit and daily_questions_limit
    
    # Validate number of questions based on user plan (per generation)
    # For multi-part selections, allow higher limits based on marks pattern
    if request.part_ids and len(request.part_ids) > 0:
        # Multi-part mode: calculate max based on marks pattern
        # Pattern per part: 1 mark (12), 2 marks (6), 3 marks (4), 5 marks (3), 10 marks (2), mixed (16)
        part_count = len(request.part_ids)
        if request.marks and request.marks != "mixed":
            marks = int(request.marks) if isinstance(request.marks, str) else request.marks
            questions_per_part = {
                1: 12,
                2: 6,
                3: 4,
                5: 3,
                10: 2
            }.get(marks, 16)
        else:
            questions_per_part = 16  # Mixed pattern
        max_questions = part_count * questions_per_part if is_premium else min(part_count * questions_per_part, 3)
    else:
        # Single upload mode: standard limits
        max_questions = 15 if is_premium else 3  # Reduced from 20 to 15 for premium users
    
    if request.num_questions > max_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question count exceeds your plan limit. Maximum {max_questions} questions allowed per generation."
        )
    
    if request.num_questions < 1 or not isinstance(request.num_questions, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question count. Must be a positive integer."
        )
    
    # Text content is already extracted above (either from single upload or combined parts)
    if not text_content or len(text_content.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract sufficient text from file"
        )
    
    # Check total and daily question limits BEFORE generation
    from app.models import QnASet
    from datetime import datetime
    
    # Refresh user from database to get latest reset timestamp (in case admin just reset it)
    db.refresh(current_user)
    
    # Get user's question limits (admin-configurable, defaults: 700 total, 50 daily)
    total_limit = current_user.total_questions_limit or 700
    daily_limit = current_user.daily_questions_limit or 50
    
    # Count total questions (after reset timestamp if set)
    if current_user.total_questions_reset_at:
        reset_timestamp_total = current_user.total_questions_reset_at
        total_qna_sets = db.query(QnASet).filter(
            QnASet.user_id == current_user.id,
            QnASet.created_at >= reset_timestamp_total
        ).all()
    else:
        total_qna_sets = db.query(QnASet).filter(
            QnASet.user_id == current_user.id
        ).all()
    
    total_questions_used = 0
    for qna_set in total_qna_sets:
        if qna_set.qna_json and isinstance(qna_set.qna_json, dict):
            questions = qna_set.qna_json.get("questions", [])
            if isinstance(questions, list):
                total_questions_used += len(questions)
    
    # Determine the reset timestamp - use daily_questions_reset_at if set, otherwise use today's start
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    # If reset timestamp is set and is today or later, use it
    if current_user.daily_questions_reset_at:
        if current_user.daily_questions_reset_at.date() >= datetime.utcnow().date():
            reset_timestamp = current_user.daily_questions_reset_at
        else:
            # Reset timestamp is from a previous day, use today's start instead
            reset_timestamp = today_start
    else:
        reset_timestamp = today_start
    
    # Count questions generated after reset timestamp
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
    
    print(f"🔍 Total questions check: used={total_questions_used}, limit={total_limit}")
    print(f"🔍 Daily questions check: used={daily_questions_used}, limit={daily_limit}, reset_timestamp={reset_timestamp}")
    
    # Calculate how many questions will be generated
    if request.custom_distribution and len(request.custom_distribution) > 0:
        questions_to_generate = sum(item.count for item in request.custom_distribution)
    else:
        questions_to_generate = request.num_questions
    
    # Check if generating these questions would exceed total limit
    if total_questions_used + questions_to_generate > total_limit:
        remaining = max(0, total_limit - total_questions_used)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Total question limit exceeded. You have used {total_questions_used} of {total_limit} questions. "
                  f"You can generate {remaining} more questions. Please contact admin to increase your limit."
        )
    
    # Check if generating these questions would exceed daily limit
    if daily_questions_used + questions_to_generate > daily_limit:
        remaining = max(0, daily_limit - daily_questions_used)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily question limit exceeded. You have used {daily_questions_used} of {daily_limit} questions today. "
                  f"You can generate {remaining} more questions today. Please wait until tomorrow or contact admin to reset your daily limit."
        )
    
    # Generate Q/A with error handling
    try:
        # Handle custom distribution if provided
        if request.custom_distribution and len(request.custom_distribution) > 0:
            # Use custom distribution directly
            distribution_list = [
                {
                    "marks": item.marks,
                    "count": item.count,
                    "type": item.type
                }
                for item in request.custom_distribution
            ]
            
            # Calculate total from custom distribution
            total_custom = sum(item.count for item in request.custom_distribution)
            
            # Validate total doesn't exceed limit
            if total_custom > max_questions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Total questions in custom distribution ({total_custom}) exceeds your plan limit ({max_questions})"
                )
            
            remaining_questions = max_questions
            
            # Generate with custom distribution - NO RETRIES, accept quality questions immediately
            # Get number of parts for dynamic content limit
            num_parts = len(request.part_ids) if request.part_ids else None
            
            try:
                # Use pipeline for better accuracy and cost control
                qna_data = generate_qna_pipeline(
                    text_content=text_content,
                    difficulty=request.difficulty.value,
                    qna_type=request.qna_type.value,
                    num_questions=total_custom,
                    marks_pattern="custom",  # Special marker for custom
                    target_language=request.target_language or "english",
                    remaining_questions=remaining_questions,
                    distribution_list=distribution_list,
                    subject=selected_subject,  # Pass selected subject
                    num_parts=num_parts,  # Pass number of parts for dynamic content limit
                    use_pipeline=True  # Enable two-step pipeline
                )
                
                # Accept whatever quality questions we got - no retries
                questions_count = len(qna_data.get("questions", []))
                if questions_count < total_custom:
                    print(f"INFO: Generated {questions_count} quality questions (requested {total_custom}). Accepting result - quality over quantity.")
                    
            except ValueError as e:
                error_msg = str(e)
                # Accept format repetition and fewer questions - quality over quantity
                if ("format repetition" in error_msg.lower() or "Format repetition" in error_msg or 
                    "AI generated only" in error_msg or "fewer questions" in error_msg.lower()):
                    print(f"INFO: {error_msg}. Accepting questions - quality over quantity.")
                    # qna_data should already be set from generate_qna before the exception
                    if not qna_data:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to generate Q/A. Please try again."
                        )
                else:
                    raise  # Re-raise if it's a different error
            except Exception as e:
                # For any other error, raise it
                raise
            
            # Check if we have valid data after retries
            if not qna_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate Q/A after multiple retry attempts. Please try again."
                )
            
            # Store actual vs requested counts for frontend notification
            if qna_data and "questions" in qna_data:
                actual_count = len(qna_data["questions"])
                if "qna_json" not in qna_data:
                    qna_data["qna_json"] = {}
                qna_data["qna_json"]["actual_question_count"] = actual_count
                qna_data["qna_json"]["requested_question_count"] = total_custom
        else:
            # Use standard marks pattern (existing logic)
            # Convert marks to string pattern if needed
            marks_pattern = None
            if request.marks is not None:
                if isinstance(request.marks, str):
                    marks_pattern = request.marks
                elif isinstance(request.marks, list):
                    # If list provided, convert to pattern string
                    if len(request.marks) == 1:
                        marks_pattern = str(request.marks[0])
                    else:
                        marks_pattern = "mixed"
                else:
                    marks_pattern = str(request.marks)
            
            # Generate Q/A
            # Adjust marks pattern based on question type for realistic exam patterns
            adjusted_marks_pattern = marks_pattern or "mixed"
            
            # If MCQ type and marks are high (5 or 10), adjust to realistic MCQ marks
            if request.qna_type.value == "mcq" and marks_pattern in ["5", "10"]:
                # MCQs should be 1-2 marks, not 5-10
                adjusted_marks_pattern = "2"  # Use 2 marks for MCQ
                print(f"⚠️  Adjusted marks from {marks_pattern} to 2 for MCQ type (MCQs are typically 1-2 marks)")
            
            # Note: We respect user's explicit marks selection for descriptive questions
            # If user wants 1-mark descriptive, we allow it (AI will generate 1-2 line answers)
            
            # Calculate remaining questions (use max_questions as limit)
            remaining_questions = max_questions
            
            # Build distribution list from marks pattern
            from app.ai_service import _build_distribution_list
            distribution_list = _build_distribution_list(
                adjusted_marks_pattern,
                request.qna_type.value,
                request.num_questions
            )
            
            # Debug: Print distribution list to verify it's correct
            print(f"Distribution List: {distribution_list}")
            print(f"Marks Pattern: {adjusted_marks_pattern}, Question Type: {request.qna_type.value}")
            
            # Ensure distribution doesn't exceed remaining questions
            total_distribution = sum(item.get("count", 0) for item in distribution_list)
            if total_distribution > remaining_questions:
                # Scale down proportionally
                scale = remaining_questions / total_distribution
                for item in distribution_list:
                    item["count"] = max(1, int(item["count"] * scale))
                # Adjust to exact match
                total_after_scale = sum(item.get("count", 0) for item in distribution_list)
                if total_after_scale < remaining_questions and distribution_list:
                    distribution_list[0]["count"] += (remaining_questions - total_after_scale)
            
            # Generate Q/A - NO RETRIES, accept quality questions immediately
            try:
                # Use pipeline for better accuracy and cost control
                qna_data = generate_qna_pipeline(
                    text_content=text_content,
                    difficulty=request.difficulty.value,
                    qna_type=request.qna_type.value,
                    num_questions=request.num_questions,
                    marks_pattern=adjusted_marks_pattern,
                    target_language=request.target_language or "english",
                    remaining_questions=remaining_questions,
                    distribution_list=distribution_list,
                    subject=selected_subject,  # Pass selected subject
                    num_parts=num_parts,  # Pass number of parts for dynamic content limit
                    use_pipeline=True  # Enable two-step pipeline
                )
                
                # Accept whatever quality questions we got - no retries
                questions_count = len(qna_data.get("questions", []))
                if questions_count < request.num_questions:
                    print(f"INFO: Generated {questions_count} quality questions (requested {request.num_questions}). Accepting result - quality over quantity.")
                    
            except ValueError as e:
                error_msg = str(e)
                # Accept format repetition and fewer questions - quality over quantity
                if ("format repetition" in error_msg.lower() or "Format repetition" in error_msg or 
                    "AI generated only" in error_msg or "fewer questions" in error_msg.lower()):
                    print(f"INFO: {error_msg}. Accepting questions - quality over quantity.")
                    # qna_data should already be set from generate_qna before the exception
                    if not qna_data:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to generate Q/A. Please try again."
                        )
                else:
                    raise  # Re-raise if it's a different error
            except Exception as e:
                # For any other error, raise it
                raise
            
            # Check if we have valid data after retries
            if not qna_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate Q/A after multiple retry attempts. Please try again."
                )
            
            # Store actual vs requested counts for frontend notification
            if qna_data and "questions" in qna_data:
                actual_count = len(qna_data["questions"])
                if "qna_json" not in qna_data:
                    qna_data["qna_json"] = {}
                qna_data["qna_json"]["actual_question_count"] = actual_count
                qna_data["qna_json"]["requested_question_count"] = request.num_questions
            
            # Post-process validation: Enforce exact marks from distribution list
            if qna_data and "questions" in qna_data:
                # Build a list of expected (marks, type) pairs from distribution_list
                # This ensures we enforce the exact distribution requested
                expected_distribution = []
                for dist_item in distribution_list:
                    dist_type = dist_item.get("type", "").lower()
                    dist_marks = dist_item.get("marks", 0)
                    dist_count = dist_item.get("count", 0)
                    for _ in range(dist_count):
                        expected_distribution.append((dist_marks, dist_type))
                
                print(f"🔍 Expected Distribution: {expected_distribution}")
                print(f"🔍 Total questions generated: {len(qna_data['questions'])}")
                
                # Now enforce marks on each question based on expected distribution
                questions = qna_data["questions"]
                for idx, q in enumerate(questions):
                    q_type = q.get("type", "").lower()
                    # Ensure marks is an integer for comparison
                    q_marks = int(q.get("marks", 0))
                    
                    print(f"🔍 Question {idx+1}: type={q_type}, marks={q_marks} (type: {type(q_marks)})")
                    
                    # If we have an expected distribution for this index, enforce it
                    if idx < len(expected_distribution):
                        expected_marks, expected_type = expected_distribution[idx]
                        # Ensure expected_marks is an integer
                        expected_marks = int(expected_marks)
                        
                        print(f"🔍 Expected for Q{idx+1}: marks={expected_marks} (type: {type(expected_marks)}), type={expected_type}")
                        
                        # Fix marks if they don't match - THIS IS CRITICAL
                        if q_marks != expected_marks:
                            print(f"✅ FIXING question {idx+1}: Changed marks from {q_marks} to {expected_marks} (as per distribution)")
                            q["marks"] = expected_marks
                            q_marks = expected_marks  # Update for subsequent checks
                        else:
                            print(f"✅ Question {idx+1} already has correct marks: {q_marks}")
                        
                        # Fix type if it doesn't match (but be lenient - descriptive vs short is okay)
                        if expected_type == "descriptive" and q_type not in ["descriptive", "long"]:
                            print(f"✅ FIXING question {idx+1}: Changed type from {q_type} to descriptive (as per distribution)")
                            q["type"] = "descriptive"
                            # Remove options if converting from MCQ
                            if "options" in q:
                                del q["options"]
                    else:
                        # If we have more questions than expected, use the last expected marks/type
                        if expected_distribution:
                            expected_marks, expected_type = expected_distribution[-1]
                            if q_marks != expected_marks:
                                print(f"✅ FIXING question {idx+1} (extra): Changed marks from {q_marks} to {expected_marks}")
                                q["marks"] = expected_marks
                    
                    # Safety checks
                    # Fix MCQs with unrealistic marks
                    if q_type == "mcq" and q_marks > 2:
                        print(f"⚠️  Fixing MCQ question: Changed marks from {q_marks} to 2")
                        q["marks"] = 2
                    
                    # Ensure 10-mark questions are descriptive
                    if q_marks == 10 and q_type == "mcq":
                        print(f"⚠️  Converting 10-mark MCQ to descriptive question")
                        q["type"] = "descriptive"
                        if "options" in q:
                            del q["options"]
                
                print(f"✅ Post-processing complete. Final questions:")
                for idx, q in enumerate(questions):
                    print(f"   Q{idx+1}: type={q.get('type')}, marks={q.get('marks')}")
            
            # Link AI usage log to QnA set after creation
            if qna_data:
                # This will be linked after QnASet is created below
                pass
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
            severity="error"
        )
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Error generating Q/A: {str(e)}")
        print(f"❌ Traceback:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Q/A: {str(e)}"
        )
    
    # Ensure qna_data is defined
    if 'qna_data' not in locals():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Q/A: No data generated"
        )
    
    # Add source tracking for multi-part selections
    if request.part_ids and len(request.part_ids) > 0 and 'part_info_map' in locals():
        questions = qna_data.get("questions", [])
        total_questions = len(questions)
        total_parts = len(part_info_map)
        
        if total_parts > 0 and total_questions > 0:
            # Distribute questions evenly across parts
            questions_per_part = total_questions // total_parts
            remainder = total_questions % total_parts
            
            part_numbers = sorted(part_info_map.keys())
            question_idx = 0
            
            for part_idx, part_num in enumerate(part_numbers):
                part_info = part_info_map[part_num]
                # Calculate how many questions for this part
                questions_for_this_part = questions_per_part + (1 if part_idx < remainder else 0)
                
                # Calculate page range for this part
                start_page = part_info["start_page"]
                end_page = part_info["end_page"]
                total_pages_in_part = end_page - start_page + 1
                
                # Assign source info to questions with exact page numbers
                for i in range(questions_for_this_part):
                    if question_idx < total_questions:
                        if "source" not in questions[question_idx]:
                            questions[question_idx]["source"] = {}
                        
                        # Calculate exact page number by distributing questions across the page range
                        if questions_for_this_part > 1:
                            # Distribute evenly across pages
                            page_offset = int((i * total_pages_in_part) / questions_for_this_part)
                            exact_page = start_page + page_offset
                        else:
                            # Single question: use middle page of the range
                            exact_page = start_page + (total_pages_in_part // 2)
                        
                        # Ensure page is within range
                        exact_page = max(start_page, min(exact_page, end_page))
                        
                        questions[question_idx]["source"]["part_number"] = part_info["part_number"]
                        questions[question_idx]["source"]["start_page"] = part_info["start_page"]
                        questions[question_idx]["source"]["end_page"] = part_info["end_page"]
                        questions[question_idx]["source"]["exact_page"] = exact_page
                        questions[question_idx]["source"]["page_range"] = f"Pages {part_info['start_page']}-{part_info['end_page']}"
                        question_idx += 1
            
            # Update qna_data with source-tracked questions
            qna_data["questions"] = questions
    
    # Prepare settings JSON
    settings_json = {
        "difficulty": request.difficulty.value,
        "qna_type": request.qna_type.value,
        "num_questions": request.num_questions,
        "output_format": request.output_format.value,
        "include_answers": request.include_answers,
        "marks": request.marks,
        "target_language": request.target_language or "english"
    }
    
    # Decrement upload quota when generating questions (1 generation = 1 upload consumed)
    # This protects against unlimited generation from saved uploads
    try:
        from datetime import datetime
        is_premium = (
            current_user.premium_status.value == "approved" and
            current_user.premium_valid_until and
            current_user.premium_valid_until > datetime.utcnow()
        )
        
        if is_premium:
            # Decrement quota based on upload file type
            if upload.file_type.value == "pdf":
                if current_user.upload_quota_remaining > 0:
                    current_user.upload_quota_remaining -= 1
                    print(f"📊 Decremented PDF upload quota: {current_user.upload_quota_remaining + 1} -> {current_user.upload_quota_remaining}")
                else:
                    # Should not happen if validation is correct, but log it
                    print(f"⚠️  Warning: PDF quota already exhausted, but generation proceeded")
            else:
                # Image upload
                if current_user.image_quota_remaining > 0:
                    current_user.image_quota_remaining -= 1
                    print(f"📊 Decremented Image upload quota: {current_user.image_quota_remaining + 1} -> {current_user.image_quota_remaining}")
                else:
                    # Should not happen if validation is correct, but log it
                    print(f"⚠️  Warning: Image quota already exhausted, but generation proceeded")
            
            db.commit()
            db.refresh(current_user)
    except Exception as e:
        log_api_error(db, e, current_user.id, http_request, severity="warning")
        print(f"⚠️  Failed to decrement upload quota: {e}")
        # Don't fail the generation if quota decrement fails
    
    # Save Q/A set (always save with answers)
    # Ensure qna_data is valid before saving
    if not qna_data or not isinstance(qna_data, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid Q/A data generated. Please try again."
        )
    
    qna_set = QnASet(
        user_id=current_user.id,
        upload_id=upload.id,
        settings_json=settings_json,
        qna_json=qna_data
    )
    db.add(qna_set)
    db.commit()
    db.refresh(qna_set)
    
    # Log usage for generation action (to match profile tab counts)
    try:
        from app.models import UsageLog
        usage_log = UsageLog(
            user_id=current_user.id,
            upload_id=upload.id,
            action="pdf_generation" if upload.file_type.value == "pdf" else "image_generation",
            pages=None,
            file_size=None
        )
        db.add(usage_log)
        db.commit()
        print(f"📝 Logged generation usage: {usage_log.action}")
    except Exception as e:
        log_api_error(db, e, current_user.id, http_request, severity="warning")
        print(f"⚠️  Failed to log generation usage: {e}")
    
    # Link AI usage log to this QnA set if available
    try:
        from app.models import AIUsageLog
        usage_log_id = qna_data.get("_usage_log_id") if qna_data else None
        if usage_log_id:
            usage_log = db.query(AIUsageLog).filter(AIUsageLog.id == usage_log_id).first()
            if usage_log:
                usage_log.user_id = current_user.id
                usage_log.qna_set_id = qna_set.id
                db.commit()
    except Exception as e:
        log_api_error(db, e, current_user.id, http_request, severity="warning")
        print(f"⚠️  Failed to link AI usage log: {e}")
    
    # Increment daily generation count (after successful generation)
    try:
        increment_daily_generation_count(db, current_user.id)
    except Exception as e:
        # Log but don't fail the request if increment fails
        log_api_error(db, e, current_user.id, http_request, severity="warning")
        print(f"⚠️  Failed to increment generation count: {e}")
    
    # Remove internal field from response
    if qna_data and "_usage_log_id" in qna_data:
        del qna_data["_usage_log_id"]
    
    # Add actual vs requested counts to qna_json for frontend notification (if not already added)
    if qna_data and "qna_json" in qna_data:
        if "actual_question_count" in qna_data["qna_json"]:
            qna_set.qna_json["actual_question_count"] = qna_data["qna_json"]["actual_question_count"]
            qna_set.qna_json["requested_question_count"] = qna_data["qna_json"].get("requested_question_count", request.num_questions)
    
    return qna_set

@router.get("/sets", response_model=list[QnASetResponse])
async def list_qna_sets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's saved Q/A sets"""
    sets = db.query(QnASet).filter(
        QnASet.user_id == current_user.id
    ).order_by(QnASet.created_at.desc()).all()
    
    # Filter out sets with None qna_json and provide default empty dict for invalid sets
    valid_sets = []
    for s in sets:
        if s.qna_json is None:
            # Skip sets with None qna_json (likely from failed generations)
            continue
        if not isinstance(s.qna_json, dict):
            # Skip sets with invalid qna_json type
            continue
        valid_sets.append(s)
    
    return valid_sets

@router.delete("/sets/{set_id}")
async def delete_qna_set(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a saved Q/A set for the current user"""
    qna_set = db.query(QnASet).filter(
        QnASet.id == set_id,
        QnASet.user_id == current_user.id
    ).first()
    
    if not qna_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q/A set not found"
        )
    
    db.delete(qna_set)
    db.commit()
    
    return {"message": "Q/A set deleted", "id": set_id}

@router.get("/sets/{set_id}", response_model=QnASetResponse)
async def get_qna_set(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific Q/A set"""
    qna_set = db.query(QnASet).filter(
        QnASet.id == set_id,
        QnASet.user_id == current_user.id
    ).first()
    
    if not qna_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q/A set not found"
        )
    
    return qna_set

@router.get("/sets/{set_id}/download")
async def download_qna_set(
    set_id: int,
    format: str,  # pdf, docx, txt
    output_format: str,  # questions_only, questions_answers, answers_only
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download Q/A set in specified format"""
    
    # Check premium
    from datetime import datetime
    is_premium = (
        current_user.premium_status.value == "approved" and
        current_user.premium_valid_until and
        current_user.premium_valid_until > datetime.utcnow()
    )
    
    if not is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium access required for downloads"
        )
    
    # Get Q/A set
    qna_set = db.query(QnASet).filter(
        QnASet.id == set_id,
        QnASet.user_id == current_user.id
    ).first()
    
    if not qna_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q/A set not found"
        )
    
    # Generate file
    title = f"Generated Questions - Set {set_id}"
    
    # Get target language from settings
    target_language = qna_set.settings_json.get("target_language", "english")
    
    if format == "pdf":
        # Try Playwright first if available (best quality)
        if PLAYWRIGHT_AVAILABLE:
            try:
                # Build HTML for Playwright (same as generate_pdf does)
                from app.download_service import LANGUAGE_TO_FONT_NAME, FONT_NAME_MAP, is_rtl
                import os
                import html as html_escape
                import unicodedata
                
                font_name = LANGUAGE_TO_FONT_NAME.get(target_language, "NotoLatin")
                is_rtl_lang = is_rtl(target_language)
                
                # Get font file path (relative to download_service.py location)
                import app.download_service as ds_module
                base_dir = os.path.join(os.path.dirname(ds_module.__file__), "fonts")
                font_file = FONT_NAME_MAP.get(font_name, "NotoSans-Regular.ttf")
                font_path = os.path.abspath(os.path.join(base_dir, font_file))
                
                def normalize_text(text: str) -> str:
                    if not isinstance(text, str):
                        return text
                    return unicodedata.normalize("NFC", text)
                
                # Load font as base64
                font_base64 = None
                if os.path.exists(font_path):
                    import base64
                    with open(font_path, 'rb') as f:
                        font_data = f.read()
                        font_base64 = base64.b64encode(font_data).decode('utf-8')
                
                # Helper function to convert structured answer to formatted text
                def format_structured_answer(answer, marks):
                    """Convert structured answer (dict) to formatted text string"""
                    if isinstance(answer, dict):
                        # Check for English literature format (introduction, explanation, analysis, conclusion)
                        if answer.get("introduction") or answer.get("explanation") or answer.get("analysis") or answer.get("conclusion"):
                            parts = []
                            if answer.get("introduction"):
                                parts.append(f"Introduction: {answer.get('introduction')}")
                            if answer.get("explanation"):
                                parts.append(f"Explanation: {answer.get('explanation')}")
                            if answer.get("analysis"):
                                parts.append(f"Analysis: {answer.get('analysis')}")
                            if answer.get("conclusion"):
                                parts.append(f"Conclusion: {answer.get('conclusion')}")
                            return "\n".join(parts)
                        
                        # Check for Science format (definition, explanation, example, conclusion)
                        if answer.get("definition") and (answer.get("explanation") or answer.get("example") or answer.get("conclusion")):
                            if not (answer.get("formula") or answer.get("given") or answer.get("steps")):
                                parts = []
                                if answer.get("definition"):
                                    parts.append(f"Definition: {answer.get('definition')}")
                                if answer.get("explanation"):
                                    parts.append(f"Explanation: {answer.get('explanation')}")
                                if answer.get("example"):
                                    parts.append(f"Example: {answer.get('example')}")
                                if answer.get("conclusion"):
                                    parts.append(f"Conclusion: {answer.get('conclusion')}")
                                return "\n".join(parts)
                        
                        # Check for Social Science format (background, context, key_points, explanation, conclusion)
                        if answer.get("background") or answer.get("context") or answer.get("key_points"):
                            parts = []
                            if answer.get("background"):
                                parts.append(f"Background: {answer.get('background')}")
                            if answer.get("context"):
                                parts.append(f"Context: {answer.get('context')}")
                            if answer.get("key_points"):
                                kp = answer.get("key_points")
                                if isinstance(kp, list):
                                    parts.append(f"Key Points: {' '.join(str(v) for v in kp)}")
                                else:
                                    parts.append(f"Key Points: {kp}")
                            if answer.get("explanation"):
                                parts.append(f"Explanation: {answer.get('explanation')}")
                            if answer.get("conclusion"):
                                parts.append(f"Conclusion: {answer.get('conclusion')}")
                            return "\n".join(parts)
                        
                        # Board-style format (post-processed 10-mark math)
                        if (
                            answer.get("substitution") is not None
                            or answer.get("calculation") is not None
                            or answer.get("final_answer") is not None
                        ):
                            parts = []
                            if answer.get("given"):
                                parts.append(f"Given: {answer.get('given')}")
                            if answer.get("formula"):
                                parts.append(f"Formula: {answer.get('formula')}")
                            if answer.get("substitution"):
                                parts.append(f"Substitution: {answer.get('substitution')}")
                            if answer.get("calculation"):
                                parts.append(f"Calculation:\n{answer.get('calculation')}")
                            if answer.get("final_answer"):
                                parts.append(f"{answer.get('final_answer')}")
                            return "\n".join(parts)

                        # Original structured format (Math and other subjects)
                        parts = []
                        if answer.get("given"):
                            parts.append(f"Given: {answer.get('given')}")
                        if answer.get("definition"):
                            parts.append(f"Definition: {answer.get('definition')}")
                        if answer.get("formula"):
                            parts.append(f"Formula/Theorem: {answer.get('formula')}")
                        if answer.get("coefficients"):
                            parts.append(f"Coefficients: {answer.get('coefficients')}")
                        if answer.get("steps") and isinstance(answer.get("steps"), list):
                            parts.append("Step-by-step Working:")
                            for i, step in enumerate(answer.get("steps", []), 1):
                                parts.append(f"Step {i}: {step}")
                        if answer.get("function_values") and isinstance(answer.get("function_values"), list):
                            parts.append("Function Values:")
                            for value in answer.get("function_values", []):
                                parts.append(f"  • {value}")
                        if answer.get("final"):
                            parts.append(f"Final Conclusion: {answer.get('final')}")
                        return "\n".join(parts) if parts else ""
                    return str(answer) if answer else ""
                
                # Helper function to escape HTML while preserving LaTeX
                def escape_html_preserve_latex(text) -> str:
                    """Escape HTML but preserve LaTeX expressions for KaTeX"""
                    # Handle dict format
                    if isinstance(text, dict):
                        text = format_structured_answer(text, 0)
                    
                    if not text:
                        return ""
                    
                    # Convert to string if not already
                    text = str(text)
                    
                    import re
                    
                    # First, convert escaped LaTeX delimiters to single backslash for KaTeX
                    # JSON stores as \\( and \\), but KaTeX needs \( and \)
                    text = text.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
                    text = text.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
                    
                    # Pattern to match LaTeX expressions (inline and display math)
                    # Match \(...\) and \[...\] patterns
                    latex_pattern = r'\\(?:\([^)]*\)|\[[^\]]*\])'
                    placeholders = {}
                    placeholder_idx = 0
                    
                    def replace_latex(match):
                        nonlocal placeholder_idx
                        placeholder = f"__LATEX_{placeholder_idx}__"
                        placeholders[placeholder] = match.group(0)
                        placeholder_idx += 1
                        return placeholder
                    
                    # Find and replace all LaTeX expressions with placeholders
                    text_with_placeholders = re.sub(latex_pattern, replace_latex, text)
                    
                    # Escape HTML
                    escaped = html_escape.escape(text_with_placeholders)
                    
                    # Restore LaTeX expressions (they're safe for HTML)
                    for placeholder, latex_expr in placeholders.items():
                        escaped = escaped.replace(placeholder, latex_expr)
                    
                    return escaped
                
                # Build HTML
                html_parts = []
                font_src = f"url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype')" if font_base64 else ""
                
                css_content = f"""
                @page {{ size: A4; margin: 1in; }}
                @font-face {{ font-family: '{font_name}'; src: {font_src}; font-weight: normal; font-style: normal; }}
                body, * {{ font-family: '{font_name}' !important; }}
                body {{ font-size: 12pt; line-height: 1.8; color: #000000; direction: {'rtl' if is_rtl_lang else 'ltr'}; margin: 0; padding: 0; }}
                .title {{ font-size: 18pt; font-weight: 700; color: #000000; text-align: center; margin-bottom: 30pt; margin-top: 0; text-transform: uppercase; letter-spacing: 1pt; }}
                .question-box {{ border: none; padding: 0; margin-bottom: 20pt; }}
                .question-label {{ font-weight: 700; font-size: 12pt; margin-right: 8pt; display: inline; }}
                .question-text {{ font-weight: 400; font-size: 12pt; margin-bottom: 12pt; line-height: 1.8; display: inline; }}
                .options {{ margin: 8pt 0 8pt 20pt; padding: 0; list-style: none; }}
                .option {{ margin: 6pt 0; font-size: 12pt; line-height: 1.8; }}
                .option-label {{ font-weight: 400; margin-right: 8pt; }}
                .marks {{ font-style: normal; font-size: 10pt; color: #000000; margin-top: 8pt; margin-left: 20pt; }}
                .answer-box {{ border: none; padding: 0; margin-bottom: 20pt; margin-top: 10pt; }}
                .answer-label {{ font-weight: 400; font-size: 12pt; color: #000000; margin-right: 8pt; display: inline; }}
                .answer-text {{ font-weight: 400; font-size: 12pt; color: #000000; line-height: 1.8; display: inline; }}
                """
                
                # Add KaTeX script for LaTeX rendering (better than MathJax for PDF)
                katex_script = """
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOzG8j7q1aI2+fiEYHrTZ+8uBZ4mX16o8qEDmO1CsQrMdZengsGa4s9Q2x0M" crossorigin="anonymous"></script>
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" integrity="sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05" crossorigin="anonymous"
                    onload="renderMathInElement(document.body, {
                        delimiters: [
                            {left: '\\\\(', right: '\\\\)', display: false},
                            {left: '\\\\[', right: '\\\\]', display: true}
                        ],
                        throwOnError: false
                    });"></script>
                """
                
                html_parts.append(f"""<!DOCTYPE html>
<html lang="{target_language}" dir="{'rtl' if is_rtl_lang else 'ltr'}">
<head>
<meta charset="UTF-8">
<style>{css_content}</style>
{katex_script}
</head>
<body><div class="title">{html_escape.escape(normalize_text(title))}</div>""")
                
                for idx, q in enumerate(qna_set.qna_json.get("questions", []), 1):
                    question_text = normalize_text(q.get("question", ""))
                    html_parts.append(f'<div class="question-box"><span class="question-label">Q{idx}.</span><div class="question-text">{escape_html_preserve_latex(question_text)}</div>')
                    
                    if q.get("type") == "mcq" and q.get("options"):
                        html_parts.append('<div class="options">')
                        for i, opt in enumerate(q.get("options", [])):
                            opt = normalize_text(opt)
                            option_label = chr(65 + i)
                            html_parts.append(f'<div class="option"><span class="option-label">{option_label}.</span><span>{escape_html_preserve_latex(opt)}</span></div>')
                        html_parts.append('</div>')
                    
                    if q.get("marks"):
                        marks = normalize_text(str(q.get("marks")))
                        html_parts.append(f'<div class="marks">Marks: {html_escape.escape(marks)}</div>')
                    
                    html_parts.append('</div>')
                    
                    if output_format in ["questions_answers", "answers_only"]:
                        # Try correct_answer first, then answer field as fallback
                        correct_answer = q.get("correct_answer") or q.get("answer")
                        
                        # Only add answer if it exists and is not empty
                        if correct_answer and correct_answer != "N/A" and str(correct_answer).strip():
                            answer_label = "✓ Answer:" if not is_rtl_lang else ":الإجابة ✓"
                            answer_label = normalize_text(answer_label)
                            
                            # Convert structured answer to text if needed
                            if isinstance(correct_answer, dict):
                                answer_text = format_structured_answer(correct_answer, q.get("marks", 0))
                            else:
                                answer_text = normalize_text(str(correct_answer))
                            
                            # Only add if formatted answer is not empty
                            if answer_text and answer_text.strip():
                                html_parts.append(f'<div class="answer-box"><div class="answer-label">{html_escape.escape(answer_label)}</div><div class="answer-text">{escape_html_preserve_latex(answer_text)}</div></div>')
                
                html_parts.append('</body></html>')
                html_string = '\n'.join(html_parts)
                
                print("🎭 Using Playwright for PDF generation (best quality)...")
                content = await _generate_pdf_playwright_async(html_string, font_path, font_name)
                print("✅ Playwright PDF generated successfully!")
            except Exception as e:
                print(f"⚠️  Playwright error: {e}, falling back to generate_pdf...")
                import traceback
                traceback.print_exc()
                content = generate_pdf(qna_set.qna_json, output_format, title, target_language)
        else:
            content = generate_pdf(qna_set.qna_json, output_format, title, target_language)
        media_type = "application/pdf"
        filename = f"questions_set_{set_id}.pdf"
    elif format == "docx":
        content = generate_docx(qna_set.qna_json, output_format, title)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"questions_set_{set_id}.docx"
    elif format == "txt":
        content = generate_txt(qna_set.qna_json, output_format, title)
        media_type = "text/plain"
        filename = f"questions_set_{set_id}.txt"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use pdf, docx, or txt"
        )
    
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/sets/{set_id}/download")
async def download_edited_qna_set(
    set_id: int,
    format: str = Query(..., description="File format: pdf, docx, or txt"),
    output_format: str = Query(..., description="Output format: questions_only, questions_answers, or answers_only"),
    edited_data: dict = Body(..., description="Edited QnA data with questions array"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download edited Q/A set in specified format (POST endpoint for edited content)"""
    
    # Check premium
    from datetime import datetime
    is_premium = (
        current_user.premium_status.value == "approved" and
        current_user.premium_valid_until and
        current_user.premium_valid_until > datetime.utcnow()
    )
    
    if not is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium access required for downloads"
        )
    
    # Verify the set exists and belongs to user (for security)
    qna_set = db.query(QnASet).filter(
        QnASet.id == set_id,
        QnASet.user_id == current_user.id
    ).first()
    
    if not qna_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q/A set not found"
        )
    
    # Use edited data if provided, otherwise fall back to stored data
    qna_json = edited_data.get("questions") if edited_data.get("questions") else qna_set.qna_json
    # If questions is provided, wrap it in the expected structure
    if isinstance(qna_json, list):
        qna_json = {"questions": qna_json}
    elif not isinstance(qna_json, dict) or "questions" not in qna_json:
        # Fallback to stored data
        qna_json = qna_set.qna_json
    
    # Get target language from edited data or stored settings
    target_language = edited_data.get("target_language") or qna_set.settings_json.get("target_language", "english")
    
    # Generate file
    title = f"Generated Questions - Set {set_id}"
    
    if format == "pdf":
        # Try Playwright first if available (best quality)
        if PLAYWRIGHT_AVAILABLE:
            try:
                # Build HTML for Playwright (same as GET endpoint)
                from app.download_service import LANGUAGE_TO_FONT_NAME, FONT_NAME_MAP, is_rtl
                import os
                import html as html_escape
                import unicodedata
                
                font_name = LANGUAGE_TO_FONT_NAME.get(target_language, "NotoLatin")
                is_rtl_lang = is_rtl(target_language)
                
                # Get font file path
                import app.download_service as ds_module
                base_dir = os.path.join(os.path.dirname(ds_module.__file__), "fonts")
                font_file = FONT_NAME_MAP.get(font_name, "NotoSans-Regular.ttf")
                font_path = os.path.abspath(os.path.join(base_dir, font_file))
                
                def normalize_text(text: str) -> str:
                    if not isinstance(text, str):
                        return text
                    return unicodedata.normalize("NFC", text)
                
                # Load font as base64
                font_base64 = None
                if os.path.exists(font_path):
                    import base64
                    with open(font_path, 'rb') as f:
                        font_data = f.read()
                        font_base64 = base64.b64encode(font_data).decode('utf-8')
                
                # Helper function to convert structured answer to formatted text
                def format_structured_answer(answer, marks):
                    """Convert structured answer (dict) to formatted text string"""
                    if isinstance(answer, dict):
                        # Check for English literature format (introduction, explanation, analysis, conclusion)
                        if answer.get("introduction") or answer.get("explanation") or answer.get("analysis") or answer.get("conclusion"):
                            parts = []
                            if answer.get("introduction"):
                                parts.append(f"Introduction: {answer.get('introduction')}")
                            if answer.get("explanation"):
                                parts.append(f"Explanation: {answer.get('explanation')}")
                            if answer.get("analysis"):
                                parts.append(f"Analysis: {answer.get('analysis')}")
                            if answer.get("conclusion"):
                                parts.append(f"Conclusion: {answer.get('conclusion')}")
                            return "\n".join(parts)
                        
                        # Check for Science format (definition, explanation, example, conclusion)
                        if answer.get("definition") and (answer.get("explanation") or answer.get("example") or answer.get("conclusion")):
                            if not (answer.get("formula") or answer.get("given") or answer.get("steps")):
                                parts = []
                                if answer.get("definition"):
                                    parts.append(f"Definition: {answer.get('definition')}")
                                if answer.get("explanation"):
                                    parts.append(f"Explanation: {answer.get('explanation')}")
                                if answer.get("example"):
                                    parts.append(f"Example: {answer.get('example')}")
                                if answer.get("conclusion"):
                                    parts.append(f"Conclusion: {answer.get('conclusion')}")
                                return "\n".join(parts)
                        
                        # Check for Social Science format (background, context, key_points, explanation, conclusion)
                        if answer.get("background") or answer.get("context") or answer.get("key_points"):
                            parts = []
                            if answer.get("background"):
                                parts.append(f"Background: {answer.get('background')}")
                            if answer.get("context"):
                                parts.append(f"Context: {answer.get('context')}")
                            if answer.get("key_points"):
                                kp = answer.get("key_points")
                                if isinstance(kp, list):
                                    parts.append(f"Key Points: {' '.join(str(v) for v in kp)}")
                                else:
                                    parts.append(f"Key Points: {kp}")
                            if answer.get("explanation"):
                                parts.append(f"Explanation: {answer.get('explanation')}")
                            if answer.get("conclusion"):
                                parts.append(f"Conclusion: {answer.get('conclusion')}")
                            return "\n".join(parts)
                        
                        # Board-style format (post-processed 10-mark math)
                        if (
                            answer.get("substitution") is not None
                            or answer.get("calculation") is not None
                            or answer.get("final_answer") is not None
                        ):
                            parts = []
                            if answer.get("given"):
                                parts.append(f"Given: {answer.get('given')}")
                            if answer.get("formula"):
                                parts.append(f"Formula: {answer.get('formula')}")
                            if answer.get("substitution"):
                                parts.append(f"Substitution: {answer.get('substitution')}")
                            if answer.get("calculation"):
                                parts.append(f"Calculation:\n{answer.get('calculation')}")
                            if answer.get("final_answer"):
                                parts.append(f"{answer.get('final_answer')}")
                            return "\n".join(parts)

                        # Original structured format (Math and other subjects)
                        parts = []
                        if answer.get("given"):
                            parts.append(f"Given: {answer.get('given')}")
                        if answer.get("definition"):
                            parts.append(f"Definition: {answer.get('definition')}")
                        if answer.get("formula"):
                            parts.append(f"Formula/Theorem: {answer.get('formula')}")
                        if answer.get("coefficients"):
                            parts.append(f"Coefficients: {answer.get('coefficients')}")
                        if answer.get("steps") and isinstance(answer.get("steps"), list):
                            parts.append("Step-by-step Working:")
                            for i, step in enumerate(answer.get("steps", []), 1):
                                parts.append(f"Step {i}: {step}")
                        if answer.get("function_values") and isinstance(answer.get("function_values"), list):
                            parts.append("Function Values:")
                            for value in answer.get("function_values", []):
                                parts.append(f"  • {value}")
                        if answer.get("final"):
                            parts.append(f"Final Conclusion: {answer.get('final')}")
                        return "\n".join(parts) if parts else ""
                    return str(answer) if answer else ""
                
                # Helper function to escape HTML while preserving LaTeX
                def escape_html_preserve_latex(text) -> str:
                    """Escape HTML but preserve LaTeX expressions for KaTeX"""
                    # Handle dict format
                    if isinstance(text, dict):
                        text = format_structured_answer(text, 0)
                    
                    if not text:
                        return ""
                    
                    # Convert to string if not already
                    text = str(text)
                    
                    import re
                    
                    # First, convert escaped LaTeX delimiters to single backslash for KaTeX
                    text = text.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
                    text = text.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
                    
                    # Pattern to match LaTeX expressions
                    latex_pattern = r'\\(?:\([^)]*\)|\[[^\]]*\])'
                    placeholders = {}
                    placeholder_idx = 0
                    
                    def replace_latex(match):
                        nonlocal placeholder_idx
                        placeholder = f"__LATEX_{placeholder_idx}__"
                        placeholders[placeholder] = match.group(0)
                        placeholder_idx += 1
                        return placeholder
                    
                    # Find and replace all LaTeX expressions with placeholders
                    text_with_placeholders = re.sub(latex_pattern, replace_latex, text)
                    
                    # Escape HTML
                    escaped = html_escape.escape(text_with_placeholders)
                    
                    # Restore LaTeX expressions
                    for placeholder, latex_expr in placeholders.items():
                        escaped = escaped.replace(placeholder, latex_expr)
                    
                    return escaped
                
                # Build HTML
                html_parts = []
                font_src = f"url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype')" if font_base64 else ""
                
                css_content = f"""
                @page {{ size: A4; margin: 1in; }}
                @font-face {{ font-family: '{font_name}'; src: {font_src}; font-weight: normal; font-style: normal; }}
                body, * {{ font-family: '{font_name}' !important; }}
                body {{ font-size: 12pt; line-height: 1.8; color: #000000; direction: {'rtl' if is_rtl_lang else 'ltr'}; margin: 0; padding: 0; }}
                .title {{ font-size: 18pt; font-weight: 700; color: #000000; text-align: center; margin-bottom: 30pt; margin-top: 0; text-transform: uppercase; letter-spacing: 1pt; }}
                .question-box {{ border: none; padding: 0; margin-bottom: 20pt; }}
                .question-label {{ font-weight: 700; font-size: 12pt; margin-right: 8pt; display: inline; }}
                .question-text {{ font-weight: 400; font-size: 12pt; margin-bottom: 12pt; line-height: 1.8; display: inline; }}
                .options {{ margin: 8pt 0 8pt 20pt; padding: 0; list-style: none; }}
                .option {{ margin: 6pt 0; font-size: 12pt; line-height: 1.8; }}
                .option-label {{ font-weight: 400; margin-right: 8pt; }}
                .marks {{ font-style: normal; font-size: 10pt; color: #000000; margin-top: 8pt; margin-left: 20pt; }}
                .answer-box {{ border: none; padding: 0; margin-bottom: 20pt; margin-top: 10pt; }}
                .answer-label {{ font-weight: 400; font-size: 12pt; color: #000000; margin-right: 8pt; display: inline; }}
                .answer-text {{ font-weight: 400; font-size: 12pt; color: #000000; line-height: 1.8; display: inline; }}
                """
                
                # Add KaTeX script for LaTeX rendering
                katex_script = """
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOzG8j7q1aI2+fiEYHrTZ+8uBZ4mX16o8qEDmO1CsQrMdZengsGa4s9Q2x0M" crossorigin="anonymous"></script>
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" integrity="sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05" crossorigin="anonymous"
                    onload="renderMathInElement(document.body, {{
                        delimiters: [
                            {{left: '\\\\(', right: '\\\\)', display: false}},
                            {{left: '\\\\[', right: '\\\\]', display: true}}
                        ],
                        throwOnError: false
                    }});"></script>
                """
                
                html_parts.append(f"""<!DOCTYPE html>
<html lang="{target_language}" dir="{'rtl' if is_rtl_lang else 'ltr'}">
<head>
<meta charset="UTF-8">
<style>{css_content}</style>
{katex_script}
</head>
<body><div class="title">{html_escape.escape(normalize_text(title))}</div>""")
                
                for idx, q in enumerate(qna_json.get("questions", []), 1):
                    question_text = normalize_text(q.get("question", ""))
                    html_parts.append(f'<div class="question-box"><span class="question-label">Q{idx}.</span><div class="question-text">{escape_html_preserve_latex(question_text)}</div>')
                    
                    if q.get("type") == "mcq" and q.get("options"):
                        html_parts.append('<div class="options">')
                        for i, opt in enumerate(q.get("options", [])):
                            opt = normalize_text(opt)
                            option_label = chr(65 + i)
                            html_parts.append(f'<div class="option"><span class="option-label">{option_label}.</span><span>{escape_html_preserve_latex(opt)}</span></div>')
                        html_parts.append('</div>')
                    
                    if q.get("marks"):
                        marks = normalize_text(str(q.get("marks")))
                        html_parts.append(f'<div class="marks">Marks: {html_escape.escape(marks)}</div>')
                    
                    html_parts.append('</div>')
                    
                    if output_format in ["questions_answers", "answers_only"]:
                        # Try correct_answer first, then answer field as fallback
                        correct_answer = q.get("correct_answer") or q.get("answer")
                        
                        # Only add answer if it exists and is not empty
                        if correct_answer and correct_answer != "N/A" and str(correct_answer).strip():
                            answer_label = "✓ Answer:" if not is_rtl_lang else ":الإجابة ✓"
                            answer_label = normalize_text(answer_label)
                            
                            # Convert structured answer to text if needed
                            if isinstance(correct_answer, dict):
                                answer_text = format_structured_answer(correct_answer, q.get("marks", 0))
                            else:
                                answer_text = normalize_text(str(correct_answer))
                            
                            # Only add if formatted answer is not empty
                            if answer_text and answer_text.strip():
                                html_parts.append(f'<div class="answer-box"><div class="answer-label">{html_escape.escape(answer_label)}</div><div class="answer-text">{escape_html_preserve_latex(answer_text)}</div></div>')
                
                html_parts.append('</body></html>')
                html_string = '\n'.join(html_parts)
                
                print("🎭 Using Playwright for PDF generation (edited content)...")
                content = await _generate_pdf_playwright_async(html_string, font_path, font_name)
                print("✅ Playwright PDF generated successfully (edited)!")
            except Exception as e:
                print(f"⚠️  Playwright error: {e}, falling back to generate_pdf...")
                import traceback
                traceback.print_exc()
                content = generate_pdf(qna_json, output_format, title, target_language)
        else:
            content = generate_pdf(qna_json, output_format, title, target_language)
        media_type = "application/pdf"
        filename = f"questions_set_{set_id}.pdf"
    elif format == "docx":
        content = generate_docx(qna_json, output_format, title)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"questions_set_{set_id}.docx"
    elif format == "txt":
        content = generate_txt(qna_json, output_format, title)
        media_type = "text/plain"
        filename = f"questions_set_{set_id}.txt"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use pdf, docx, or txt"
        )
    
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/detect-language")
async def detect_content_language(
    upload_id: Optional[int] = Query(None),
    part_ids: Optional[str] = Query(None),  # Comma-separated part IDs
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect the content language from an upload or parts"""
    try:
        text_content = ""
        
        if part_ids:
            # Multi-select mode: combine text from multiple parts
            part_id_list = [int(pid.strip()) for pid in part_ids.split(',') if pid.strip()]
            
            parts = db.query(PdfSplitPart).filter(
                PdfSplitPart.id.in_(part_id_list),
                PdfSplitPart.user_id == current_user.id
            ).all()
            
            if len(parts) != len(part_id_list):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more split parts not found"
                )
            
            # Combine text from all selected parts
            combined_text = []
            for part in sorted(parts, key=lambda p: p.part_number):
                part_text = extract_text_from_pdf(part.file_path)
                if part_text:
                    combined_text.append(part_text)
            
            text_content = "".join(combined_text)
        elif upload_id:
            # Single upload mode
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
            
            # Extract text sample
            if upload.file_type.value == "pdf":
                text_content = extract_text_from_pdf(upload.file_path)
            else:
                text_content = extract_text_from_image(upload.file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either upload_id or part_ids must be provided"
            )
        
        if not text_content or not text_content.strip():
            return {"detected_language": "english", "confidence": "low"}
        
        # Detect language from text
        detected_language = detect_language(text_content, "english")
        
        return {"detected_language": detected_language}
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error but return default
        try:
            log_api_error(db, e, current_user.id, None, severity="warning")
        except:
            pass
        return {"detected_language": "english", "error": "Could not detect language"}


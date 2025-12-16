from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import enum
from app.models import DifficultyLevel, QnAType, OutputFormat, PremiumStatus, FileType
from typing import Literal

# Subject type for validation
SubjectType = Literal["mathematics", "english", "tamil", "science", "social_science", "general"]

# Auth Schemas
class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

# User Schemas
class UserBase(BaseModel):
    email: str

class UserResponse(UserBase):
    id: int
    role: str
    premium_status: str
    premium_valid_until: Optional[datetime]
    upload_quota_remaining: int
    image_quota_remaining: int
    is_active: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    """User profile with usage statistics"""
    id: int
    email: str
    role: str
    created_at: datetime
    premium_status: str
    premium_valid_until: Optional[datetime]
    premium_request_date: Optional[datetime]
    usage_stats: Dict[str, Any]
    
    class Config:
        from_attributes = True

# Upload Schemas
class UploadResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    pages: Optional[int]
    subject: Optional[str] = "general"  # Subject: mathematics, english, tamil, science, social_science, general
    is_split: Optional[bool] = False
    detected_subject: Optional[str] = None  # Subject detected from content (for validation)
    subject_mismatch_warning: Optional[str] = None  # Warning message if mismatch detected
    created_at: datetime
    
    class Config:
        from_attributes = True

# PDF Split Part Schemas
class PdfSplitPartResponse(BaseModel):
    id: int
    parent_upload_id: int
    part_number: int
    custom_name: Optional[str]
    file_name: str
    file_size: int
    start_page: int
    end_page: int
    total_pages: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PdfSplitPartRenameRequest(BaseModel):
    custom_name: str

class PdfSplitResponse(BaseModel):
    """Response when PDF is split into parts"""
    parent_upload_id: int
    total_parts: int
    parts: List[PdfSplitPartResponse]
    message: str

# QnA Schemas
class DistributionItem(BaseModel):
    """Single distribution item: marks, count, and type"""
    marks: int
    count: int
    type: str  # "mcq", "short", "descriptive"

class QnAGenerateRequest(BaseModel):
    upload_id: Optional[int] = None  # Optional: can use part_ids instead
    part_ids: Optional[List[int]] = None  # Optional: list of split part IDs for multi-select
    difficulty: DifficultyLevel
    qna_type: QnAType
    num_questions: int
    output_format: OutputFormat
    include_answers: bool = True
    marks: Optional[Union[str, List[int]]] = None  # Accept string pattern ("mixed", "1", "2", etc.) or list of integers
    target_language: str = "english"  # Language code: english, tamil, hindi, arabic, spanish, telugu, kannada, malayalam, etc.
    custom_distribution: Optional[List[DistributionItem]] = None  # Custom distribution list for teachers
    subject: Optional[SubjectType] = "general"  # Subject selection: mathematics, english, science, social_science, general (defaults to upload's subject if not provided)

class QnASetResponse(BaseModel):
    id: int
    upload_id: Optional[int]
    settings_json: Dict[str, Any]
    qna_json: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Premium Request Schemas
class PremiumRequestCreate(BaseModel):
    pass

class PremiumRequestResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    status: str
    requested_at: datetime
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PremiumRequestApprove(BaseModel):
    notes: Optional[str] = None

# Admin Schemas
class UserQuotaAdjust(BaseModel):
    user_id: int
    pdf_limit: Optional[int] = None  # New field
    image_limit: Optional[int] = None  # New field
    upload_quota: Optional[int] = None  # Keep for backward compatibility
    image_quota: Optional[int] = None  # Keep for backward compatibility
    extend_validity_days: Optional[int] = None

class UsageLogResponse(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str] = None
    action: str
    pages: Optional[int]
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Review Schemas
class ReviewCreate(BaseModel):
    rating: int  # 1-5
    message: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    rating: int
    message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginLogResponse(BaseModel):
    id: int
    user_email: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_type: Optional[str]
    login_at: datetime
    logout_at: Optional[datetime]
    
    class Config:
        from_attributes = True


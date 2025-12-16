from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class PremiumStatus(str, enum.Enum):
    FREE = "free"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QnAType(str, enum.Enum):
    MCQ = "mcq"
    DESCRIPTIVE = "descriptive"
    MIXED = "mixed"

class OutputFormat(str, enum.Enum):
    QUESTIONS_ONLY = "questions_only"
    QUESTIONS_ANSWERS = "questions_answers"
    ANSWERS_ONLY = "answers_only"

class FileType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"

class Subject(str, enum.Enum):
    MATHEMATICS = "mathematics"
    ENGLISH = "english"
    TAMIL = "tamil"
    SCIENCE = "science"
    SOCIAL_SCIENCE = "social_science"
    GENERAL = "general"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    premium_status = Column(SQLEnum(PremiumStatus), default=PremiumStatus.FREE)
    premium_valid_until = Column(DateTime, nullable=True)
    upload_quota_remaining = Column(Integer, default=0)
    image_quota_remaining = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    uploads = relationship("Upload", back_populates="user")
    qna_sets = relationship("QnASet", back_populates="user")
    premium_requests = relationship("PremiumRequest", back_populates="user", primaryjoin="User.id == PremiumRequest.user_id")
    usage_logs = relationship("UsageLog", back_populates="user")
    reviews = relationship("Review", back_populates="user")

class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    pages = Column(Integer, nullable=True)  # for PDFs
    subject = Column(String, nullable=True, default="general")  # Subject selection by teacher: mathematics, english, science, social_science, general
    is_deleted = Column(Boolean, default=False)
    is_split = Column(Boolean, default=False)  # True if this PDF was split into parts
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="uploads")
    qna_sets = relationship("QnASet", back_populates="upload")
    split_parts = relationship("PdfSplitPart", back_populates="parent_upload", cascade="all, delete-orphan")

class QnASet(Base):
    __tablename__ = "qna_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=True)
    settings_json = Column(JSON, nullable=False)  # difficulty, type, format, etc.
    qna_json = Column(JSON, nullable=False)  # full Q/A data with answers
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="qna_sets")
    upload = relationship("Upload", back_populates="qna_sets")

class PremiumRequest(Base):
    __tablename__ = "premium_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(PremiumStatus), default=PremiumStatus.PENDING)
    requested_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="premium_requests", foreign_keys=[user_id])

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=True)
    action = Column(String, nullable=False)  # "pdf_upload", "image_upload", "qna_generate"
    pages = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reviews")

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system usage
    qna_set_id = Column(Integer, ForeignKey("qna_sets.id"), nullable=True)
    model = Column(String, nullable=False)  # e.g., "gpt-4-turbo-preview"
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(String, nullable=True)  # Estimated cost in USD
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="ai_usage_logs")
    qna_set = relationship("QnASet", backref="ai_usage_logs")

class LoginLog(Base):
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String, nullable=True)  # IPv4 or IPv6 address
    user_agent = Column(String, nullable=True)  # Browser/device info
    device_type = Column(String, nullable=True)  # "mobile", "desktop", "tablet", "unknown"
    login_at = Column(DateTime, server_default=func.now())
    logout_at = Column(DateTime, nullable=True)  # When user logged out
    
    # Relationships
    user = relationship("User", backref="login_logs")

class PdfSplitPart(Base):
    """Represents a split part of a large PDF book"""
    __tablename__ = "pdf_split_parts"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    part_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    custom_name = Column(String, nullable=True)  # User-defined name for the part
    file_name = Column(String, nullable=False)  # Generated filename
    file_path = Column(String, nullable=False)  # Storage path
    file_size = Column(Integer, nullable=False)  # in bytes
    start_page = Column(Integer, nullable=False)  # First page number (1-indexed)
    end_page = Column(Integer, nullable=False)  # Last page number (1-indexed)
    total_pages = Column(Integer, nullable=False)  # Pages in this part
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    parent_upload = relationship("Upload", back_populates="split_parts")
    user = relationship("User", backref="pdf_split_parts")

class DailyGenerationUsage(Base):
    """Tracks daily generation usage per user"""
    __tablename__ = "daily_generation_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    usage_date = Column(DateTime, nullable=False, index=True)  # Date (UTC, date only)
    generation_count = Column(Integer, default=0, nullable=False)  # Number of generations today
    last_reset_at = Column(DateTime, nullable=True)  # When quota was last reset
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="daily_generation_usage")
    
    # Unique constraint: one record per user per day
    __table_args__ = (
        UniqueConstraint('user_id', 'usage_date', name='uq_user_daily_usage'),
    )

class ErrorLog(Base):
    """Tracks application errors for monitoring"""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for system errors
    error_type = Column(String, nullable=False, index=True)  # e.g., "HTTPException", "ValueError", "DatabaseError"
    error_message = Column(Text, nullable=False)
    error_traceback = Column(Text, nullable=True)  # Full traceback
    endpoint = Column(String, nullable=True)  # API endpoint where error occurred
    request_method = Column(String, nullable=True)  # GET, POST, etc.
    request_path = Column(String, nullable=True)  # Full request path
    ip_address = Column(String, nullable=True)  # Client IP
    user_agent = Column(String, nullable=True)  # Browser/device info
    request_data = Column(JSON, nullable=True)  # Request payload (sanitized)
    severity = Column(String, nullable=False, default="error", index=True)  # "error", "warning", "critical"
    resolved = Column(Boolean, default=False, index=True)  # Whether error has been addressed
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", backref="error_logs")


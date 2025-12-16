"""
Error Logging and Monitoring System
"""
from sqlalchemy.orm import Session
from app.models import ErrorLog
from datetime import datetime
import logging
import traceback
from typing import Optional, Dict, Any
from fastapi import Request
import json

# Configure application logger
app_logger = logging.getLogger("studyqna")
app_logger.setLevel(logging.INFO)

# Create file handler for error logs
try:
    import os
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/error.log")
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)
except Exception as e:
    print(f"Warning: Could not set up file logging: {e}")

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
app_logger.addHandler(console_handler)

def sanitize_request_data(data: Any) -> Any:
    """Sanitize request data to remove sensitive information"""
    if not isinstance(data, dict):
        return str(data)[:500]  # Limit length
    
    sanitized = {}
    sensitive_keys = ['password', 'token', 'secret', 'api_key', 'otp', 'authorization']
    
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_request_data(value)
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            sanitized[key] = [sanitize_request_data(item) for item in value[:5]]  # Limit list size
        else:
            sanitized[key] = str(value)[:200] if value else value  # Limit string length
    
    return sanitized

def log_error(
    db: Session,
    error: Exception,
    error_type: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    severity: str = "error",
    additional_data: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Log an error to the database and application logs
    
    Args:
        db: Database session
        error: Exception object
        error_type: Type of error (e.g., "HTTPException", "ValueError")
        user_id: Optional user ID if error is user-specific
        request: Optional FastAPI Request object
        severity: Error severity ("error", "warning", "critical")
        additional_data: Optional additional data to log
    
    Returns:
        Error log ID if successful, None otherwise
    """
    try:
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # Extract request information if available
        endpoint = None
        request_method = None
        request_path = None
        ip_address = None
        user_agent = None
        request_data = None
        
        if request:
            endpoint = f"{request.method} {request.url.path}"
            request_method = request.method
            request_path = str(request.url)
            
            # Get IP address
            ip_address = (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                request.headers.get("X-Real-IP") or
                request.headers.get("CF-Connecting-IP") or
                request.headers.get("True-Client-IP") or
                request.client.host if request.client else None
            )
            
            user_agent = request.headers.get("User-Agent")
            
            # Try to get request body (if available)
            try:
                if hasattr(request, '_json'):
                    request_data = sanitize_request_data(request._json)
                elif hasattr(request, 'body'):
                    # For async requests, body might not be directly accessible
                    pass
            except Exception:
                pass
        
        # Merge additional data
        if additional_data:
            if request_data:
                request_data.update(sanitize_request_data(additional_data))
            else:
                request_data = sanitize_request_data(additional_data)
        
        # Create error log entry
        error_log = ErrorLog(
            user_id=user_id,
            error_type=error_type,
            error_message=error_message[:1000],  # Limit message length
            error_traceback=error_traceback[:5000] if error_traceback else None,  # Limit traceback length
            endpoint=endpoint,
            request_method=request_method,
            request_path=request_path[:500] if request_path else None,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            request_data=request_data,
            severity=severity,
            resolved=False
        )
        
        db.add(error_log)
        db.commit()
        db.refresh(error_log)
        
        # Also log to application logger
        log_message = f"Error [{error_type}]: {error_message}"
        if user_id:
            log_message += f" | User: {user_id}"
        if endpoint:
            log_message += f" | Endpoint: {endpoint}"
        
        if severity == "critical":
            app_logger.critical(log_message)
        elif severity == "warning":
            app_logger.warning(log_message)
        else:
            app_logger.error(log_message)
        
        return error_log.id
    
    except Exception as log_error:
        # Fallback: log to console if database logging fails
        print(f"CRITICAL: Failed to log error to database: {log_error}")
        print(f"Original error: {error}")
        app_logger.critical(f"Failed to log error: {log_error} | Original: {error}")
        return None

def log_api_error(
    db: Session,
    error: Exception,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    severity: str = "error"
) -> Optional[int]:
    """Convenience function to log API errors"""
    error_type = type(error).__name__
    return log_error(db, error, error_type, user_id, request, severity)

def get_error_stats(db: Session, days: int = 7) -> Dict[str, Any]:
    """
    Get error statistics for monitoring
    
    Args:
        db: Database session
        days: Number of days to look back
    
    Returns:
        Dictionary with error statistics
    """
    try:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total errors
        total_errors = db.query(ErrorLog).filter(
            ErrorLog.created_at >= cutoff_date
        ).count()
        
        # Errors by severity
        critical_errors = db.query(ErrorLog).filter(
            ErrorLog.created_at >= cutoff_date,
            ErrorLog.severity == "critical"
        ).count()
        
        error_count = db.query(ErrorLog).filter(
            ErrorLog.created_at >= cutoff_date,
            ErrorLog.severity == "error"
        ).count()
        
        warning_count = db.query(ErrorLog).filter(
            ErrorLog.created_at >= cutoff_date,
            ErrorLog.severity == "warning"
        ).count()
        
        # Errors by type (top 5)
        from sqlalchemy import func
        error_types = db.query(
            ErrorLog.error_type,
            func.count(ErrorLog.id).label('count')
        ).filter(
            ErrorLog.created_at >= cutoff_date
        ).group_by(
            ErrorLog.error_type
        ).order_by(
            func.count(ErrorLog.id).desc()
        ).limit(5).all()
        
        # Unresolved errors
        unresolved = db.query(ErrorLog).filter(
            ErrorLog.created_at >= cutoff_date,
            ErrorLog.resolved == False
        ).count()
        
        return {
            "total_errors": total_errors,
            "critical": critical_errors,
            "errors": error_count,
            "warnings": warning_count,
            "unresolved": unresolved,
            "top_error_types": [{"type": et[0], "count": et[1]} for et in error_types],
            "period_days": days
        }
    
    except Exception as e:
        app_logger.error(f"Error getting error stats: {e}")
        return {
            "total_errors": 0,
            "critical": 0,
            "errors": 0,
            "warnings": 0,
            "unresolved": 0,
            "top_error_types": [],
            "period_days": days
        }



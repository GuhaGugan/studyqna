"""
Enhanced email validation with RFC compliance and DNS MX record lookup
"""
import re
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from typing import Tuple

# Common email domain patterns
VALID_EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
)

# Blocked/invalid patterns
INVALID_PATTERNS = [
    r'^test@',  # Test emails
    r'@test\.',  # Test domains
    r'@example\.',  # Example domains
    r'@localhost',  # Localhost
    r'@127\.0\.0\.1',  # IP addresses
    r'\.{2,}',  # Consecutive dots
    r'^\.|\.$',  # Starting or ending with dot
    r'@{2,}',  # Multiple @ symbols
    r'^\s|\s$',  # Leading/trailing spaces
]

def validate_email_address(email: str) -> Tuple[bool, str]:
    """
    Validate email address with strict RFC compliance and DNS MX record check
    
    Returns:
        (is_valid, error_message)
    """
    # Basic format check
    if not email or not isinstance(email, str):
        return False, "Email address is required"
    
    email = email.strip().lower()
    
    # Check for empty after strip
    if not email:
        return False, "Email address cannot be empty"
    
    # Check basic format pattern
    if not VALID_EMAIL_PATTERN.match(email):
        return False, "Invalid email format. Please enter a valid email address."
    
    # Check for invalid patterns
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, email, re.IGNORECASE):
            return False, "Invalid email address. Please use a valid email."
    
    # Check for common typos
    if email.count('@') != 1:
        return False, "Invalid email format. Email must contain exactly one @ symbol."
    
    # Split and validate parts
    parts = email.split('@')
    if len(parts) != 2:
        return False, "Invalid email format. Please enter a valid email address."
    
    local_part, domain = parts
    
    # Validate local part (before @)
    if not local_part or len(local_part) > 64:
        return False, "Invalid email format. Local part is invalid."
    
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "Invalid email format. Email cannot start or end with a dot."
    
    # Validate domain (after @)
    if not domain or len(domain) > 255:
        return False, "Invalid email format. Domain is invalid."
    
    if '.' not in domain:
        return False, "Invalid email format. Domain must contain a dot."
    
    # Check for valid TLD (at least 2 characters)
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        return False, "Invalid email format. Domain must have a valid TLD."
    
    tld = domain_parts[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False, "Invalid email format. Domain must have a valid TLD."
    
    # RFC-compliant validation with deliverability check
    try:
        validation = validate_email(
            email,
            check_deliverability=True,  # Check MX records
            timeout=10,  # Increased timeout for better reliability
            allow_smtputf8=False  # Disable SMTPUTF8 for compatibility
        )
        
        # Additional check: verify the normalized email
        normalized_email = validation.normalized
        if normalized_email != email:
            # Email was normalized, which is fine, but log it
            pass
        
        # Double-check MX records
        domain = email.split('@')[1]
        try:
            mx_records = dns.resolver.resolve(domain, 'MX', lifetime=10)
            if len(mx_records) == 0:
                return False, "Invalid or unreachable email address. The domain does not accept emails."
        except dns.resolver.NXDOMAIN:
            return False, "Invalid or unreachable email address. The domain does not exist."
        except dns.resolver.NoAnswer:
            # Some domains use A records instead of MX, check that
            try:
                dns.resolver.resolve(domain, 'A', lifetime=5)
            except:
                return False, "Invalid or unreachable email address. The domain does not exist."
        except Exception as dns_error:
            # DNS lookup failed, but email format is valid
            # Allow it but log the warning
            print(f"⚠️  DNS lookup warning for {email}: {dns_error}")
        
        # Email is valid
        return True, ""
        
    except EmailNotValidError as e:
        # Extract user-friendly error message
        error_msg = str(e).lower()
        
        if "domain name does not exist" in error_msg or "the domain name" in error_msg:
            return False, "Invalid or unreachable email address. The domain does not exist."
        elif "not deliverable" in error_msg or "does not accept email" in error_msg:
            return False, "Invalid or unreachable email address. The domain does not accept emails."
        elif "local part" in error_msg or "username" in error_msg:
            return False, "Invalid email format. The username part is invalid."
        elif "too long" in error_msg:
            return False, "Invalid email format. Email address is too long."
        else:
            return False, "Invalid or unreachable email address. Please use a valid email address."
            
    except Exception as e:
        # Last resort: basic format validation passed, but advanced checks failed
        print(f"⚠️  Email validation error for {email}: {e}")
        return False, "Invalid or unreachable email address. Please use a valid email address."

def check_mx_record(domain: str) -> bool:
    """
    Check if domain has MX records
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX', lifetime=5)
        return len(mx_records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
        return False


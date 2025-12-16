import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from app.config import settings
from cryptography.fernet import Fernet
import base64
import hashlib

# Generate encryption key (in production, store securely)
_encryption_key = None

def get_encryption_key():
    """Get or generate encryption key"""
    global _encryption_key
    if _encryption_key is None:
        # In production, load from secure storage
        key_file = Path(settings.STORAGE_PATH) / ".encryption_key"
        if key_file.exists():
            _encryption_key = key_file.read_bytes()
        else:
            _encryption_key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_bytes(_encryption_key)
    return _encryption_key

def ensure_storage_path(user_id: int, file_type: str):
    """Ensure storage directory exists with proper permissions"""
    base_path = Path(settings.STORAGE_PATH)
    user_path = base_path / "uploads" / f"user_{user_id}" / file_type
    
    user_path.mkdir(parents=True, exist_ok=True)
    
    # Set permissions (chmod 700 equivalent on Windows)
    if os.name != 'nt':  # Unix-like systems
        os.chmod(user_path, 0o700)
        os.chmod(user_path.parent, 0o700)
        os.chmod(base_path / "uploads", 0o700)
    
    return user_path

def save_file(file_content: bytes, user_id: int, file_type: str, original_filename: str) -> str:
    """
    Save file with UUID name and return the file path
    """
    storage_dir = ensure_storage_path(user_id, file_type)
    
    # Generate UUID filename
    file_ext = Path(original_filename).suffix
    uuid_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = storage_dir / uuid_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Encrypt if enabled
    if settings.ENCRYPT_STORAGE:
        encrypt_file(file_path)
    
    return str(file_path)

def encrypt_file(file_path: Path):
    """Encrypt file using Fernet"""
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        with open(file_path, "rb") as f:
            data = f.read()
        
        encrypted_data = fernet.encrypt(data)
        
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
    except Exception as e:
        print(f"Encryption error: {e}")

def decrypt_file(file_path: Path) -> bytes:
    """Decrypt file using Fernet"""
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
        
        return fernet.decrypt(encrypted_data)
    except Exception as e:
        print(f"Decryption error: {e}")
        # If decryption fails, try reading as plain file
        with open(file_path, "rb") as f:
            return f.read()

def read_file(file_path: str) -> bytes:
    """Read file (with decryption if needed)"""
    path = Path(file_path)
    if settings.ENCRYPT_STORAGE:
        return decrypt_file(path)
    else:
        with open(path, "rb") as f:
            return f.read()

def delete_file(file_path: str):
    """Delete file securely"""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"File deletion error: {e}")



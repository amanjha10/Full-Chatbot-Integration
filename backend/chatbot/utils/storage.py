# chatbot/utils/storage.py
"""
Storage backend configuration for file uploads
Supports both local development and production S3/MinIO
"""

import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage
import mimetypes
import hashlib
from datetime import datetime


class ChatFileStorage:
    """
    Storage-agnostic interface for chat file uploads
    Automatically switches between local and S3 based on configuration
    """
    
    def __init__(self):
        self.use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
        if self.use_s3:
            self.storage = S3ChatFileStorage()
        else:
            self.storage = default_storage
    
    def save(self, name, content, max_length=None):
        """Save file and return the stored name"""
        return self.storage.save(name, content, max_length)
    
    def delete(self, name):
        """Delete file"""
        return self.storage.delete(name)
    
    def exists(self, name):
        """Check if file exists"""
        return self.storage.exists(name)
    
    def url(self, name):
        """Get file URL"""
        if self.use_s3:
            return self.storage.url(name)
        else:
            return f"{settings.MEDIA_URL}{name}"
    
    def size(self, name):
        """Get file size"""
        return self.storage.size(name)
    
    def get_available_name(self, name, max_length=None):
        """Get available filename"""
        return self.storage.get_available_name(name, max_length)


class S3ChatFileStorage(S3Boto3Storage):
    """
    Custom S3 storage for chat files with security features
    """
    
    def __init__(self):
        super().__init__(
            bucket_name=getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'chatbot-files'),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
            access_key=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            secret_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            custom_domain=getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None),
            file_overwrite=False,
            default_acl='private',  # Private by default for security
            querystring_auth=True,  # Use signed URLs
            querystring_expire=3600,  # URLs expire in 1 hour
        )
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Generate signed URL for private file access
        """
        if expire is None:
            expire = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600)
        
        return super().url(name, parameters, expire, http_method)


def generate_secure_filename(original_filename, company_id, session_id):
    """
    Generate secure filename with company/session isolation
    Format: {company_id}/{session_id_prefix}/{date}/{hash}_{filename}
    """
    # Sanitize original filename
    import re
    safe_filename = re.sub(r'[^\w\-_\.]', '_', original_filename)
    
    # Generate hash for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    hash_input = f"{company_id}_{session_id}_{timestamp}_{safe_filename}"
    file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    # Create path structure
    date_path = datetime.now().strftime('%Y/%m/%d')
    session_prefix = session_id[:8] if len(session_id) > 8 else session_id
    
    filename = f"{company_id}/{session_prefix}/{date_path}/{file_hash}_{safe_filename}"
    
    return filename


def get_file_mime_type(filename):
    """Get MIME type for file"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def validate_file_security(file_content, filename):
    """
    Basic file security validation
    Returns (is_safe, reason)
    """
    # Check file size (already handled in serializer)
    
    # Check for executable file signatures
    dangerous_signatures = [
        b'\x4d\x5a',  # PE executable (Windows .exe)
        b'\x7f\x45\x4c\x46',  # ELF executable (Linux)
        b'\xfe\xed\xfa',  # Mach-O executable (macOS)
        b'\xcf\xfa\xed\xfe',  # Mach-O executable (macOS)
    ]
    
    file_start = file_content[:10] if hasattr(file_content, '__getitem__') else b''
    
    for signature in dangerous_signatures:
        if file_start.startswith(signature):
            return False, "Executable files are not allowed"
    
    # Check filename extensions
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.pkg', '.dmg', '.sh', '.ps1'
    ]
    
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext in dangerous_extensions:
        return False, f"File extension '{file_ext}' is not allowed"
    
    return True, None


class FileUploadManager:
    """
    High-level file upload manager with security and storage abstraction
    """
    
    def __init__(self):
        self.storage = ChatFileStorage()
    
    def save_chat_file(self, uploaded_file, company_id, session_id):
        """
        Save uploaded file with security checks and proper naming
        Returns file info dict
        """
        # Security validation
        file_content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer
        
        is_safe, reason = validate_file_security(file_content, uploaded_file.name)
        if not is_safe:
            raise ValueError(f"File security check failed: {reason}")
        
        # Generate secure filename
        secure_filename = generate_secure_filename(
            uploaded_file.name, 
            company_id, 
            session_id
        )
        
        # Save file
        saved_path = self.storage.save(secure_filename, ContentFile(file_content))
        
        # Get file info
        file_info = {
            'original_name': uploaded_file.name,
            'stored_name': saved_path,
            'file_path': saved_path,
            'file_size': uploaded_file.size,
            'mime_type': get_file_mime_type(uploaded_file.name),
            'url': self.storage.url(saved_path),
            'company_id': company_id,
            'session_id': session_id
        }
        
        return file_info
    
    def delete_file(self, file_path):
        """Delete file from storage"""
        try:
            self.storage.delete(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_url(self, file_path, expire_seconds=3600):
        """Get file URL (signed if using S3)"""
        return self.storage.url(file_path)


# Storage settings for different environments
def get_storage_settings():
    """
    Get storage settings based on environment
    """
    if getattr(settings, 'USE_S3_STORAGE', False):
        return {
            'STORAGE_TYPE': 'S3',
            'BUCKET_NAME': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'chatbot-files'),
            'REGION': getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
            'SIGNED_URLS': True,
            'URL_EXPIRY': getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600),
        }
    else:
        return {
            'STORAGE_TYPE': 'LOCAL',
            'MEDIA_ROOT': settings.MEDIA_ROOT,
            'MEDIA_URL': settings.MEDIA_URL,
            'SIGNED_URLS': False,
        }


# Example usage in views:
"""
from .utils.storage import FileUploadManager

def upload_view(request):
    manager = FileUploadManager()
    file_info = manager.save_chat_file(
        uploaded_file=request.FILES['file'],
        company_id='COMP_123',
        session_id='session_456'
    )
    return JsonResponse(file_info)
"""

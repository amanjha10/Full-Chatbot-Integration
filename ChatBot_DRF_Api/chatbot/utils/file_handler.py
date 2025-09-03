# chatbot/utils/file_handler.py
import os
import uuid
import mimetypes
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime


class FileUploadHandler:
    """Handle file uploads with validation and storage"""
    
    @staticmethod
    def validate_file(uploaded_file):
        """Validate uploaded file"""
        # Check file size
        if uploaded_file.size > settings.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        
        # Check file extension
        file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            return False, f"File type '{file_extension}' is not allowed"
        
        # Check if file has content
        if uploaded_file.size == 0:
            return False, "File is empty"
        
        return True, "File is valid"
    
    @staticmethod
    def generate_filename(original_filename, company_id):
        """Generate a unique filename"""
        # Get file extension
        file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
        
        # Generate unique filename
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean original filename (remove special characters)
        clean_name = ''.join(c for c in original_filename if c.isalnum() or c in '._-')[:50]
        
        filename = f"{company_id}_{timestamp}_{unique_id}_{clean_name}"
        
        if file_extension:
            filename = f"{filename}.{file_extension}" if not filename.endswith(f'.{file_extension}') else filename
            
        return filename
    
    @staticmethod
    def get_file_type(filename):
        """Determine file type based on extension"""
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        image_types = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        document_types = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'xls', 'xlsx', 'csv', 'ppt', 'pptx']
        audio_types = ['mp3', 'wav', 'ogg', 'm4a']
        video_types = ['mp4', 'avi', 'mov', 'wmv', 'flv']
        archive_types = ['zip', 'rar', '7z', 'tar', 'gz']
        
        if extension in image_types:
            return 'image'
        elif extension in document_types:
            return 'document'
        elif extension in audio_types:
            return 'audio'
        elif extension in video_types:
            return 'video'
        elif extension in archive_types:
            return 'archive'
        else:
            return 'other'
    
    @staticmethod
    def save_file(uploaded_file, company_id, session_id):
        """Save file to storage and return file info"""
        # Validate file
        is_valid, message = FileUploadHandler.validate_file(uploaded_file)
        if not is_valid:
            raise ValueError(message)
        
        # Generate filename and path
        filename = FileUploadHandler.generate_filename(uploaded_file.name, company_id)
        file_path = f"uploads/{company_id}/{session_id[:8]}/{filename}"
        
        # Save file
        saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        
        # Get file info
        file_info = {
            'original_name': uploaded_file.name,
            'filename': filename,
            'filepath': saved_path,
            'file_size': uploaded_file.size,
            'file_type': FileUploadHandler.get_file_type(uploaded_file.name),
            'content_type': uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0],
            'url': f"{settings.MEDIA_URL}{saved_path}"
        }
        
        return file_info
    
    @staticmethod
    def delete_file(filepath):
        """Delete file from storage"""
        try:
            if default_storage.exists(filepath):
                default_storage.delete(filepath)
                return True, "File deleted successfully"
            return False, "File not found"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    @staticmethod
    def get_file_info(filepath):
        """Get file information"""
        try:
            if default_storage.exists(filepath):
                size = default_storage.size(filepath)
                url = f"{settings.MEDIA_URL}{filepath}"
                return {
                    'exists': True,
                    'size': size,
                    'url': url
                }
            return {'exists': False}
        except Exception as e:
            return {'exists': False, 'error': str(e)}

# chatbot/utils/security.py
"""
Security utilities for file upload and WebSocket authentication
"""
import time
import hashlib
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.contrib.auth.models import AnonymousUser


class RateLimiter:
    """Rate limiting for file uploads"""
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def is_rate_limited(request, action='upload', limit=None):
        """Check if request is rate limited"""
        if limit is None:
            limit = getattr(settings, 'CHAT_UPLOAD_RATE_LIMIT', 10)
        
        # Create cache key based on IP and user
        ip = RateLimiter.get_client_ip(request)
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        cache_key = f"rate_limit_{action}_{ip}_{user_id}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, 60)  # 1 minute window
        return False


def rate_limit(action='upload', limit=None):
    """Rate limiting decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if RateLimiter.is_rate_limited(request, action, limit):
                return Response({
                    'error': 'Rate limit exceeded. Please try again later.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class FileValidator:
    """File validation utilities"""
    
    @staticmethod
    def validate_file_type(file, allowed_types=None):
        """Validate file MIME type"""
        if allowed_types is None:
            allowed_types = getattr(settings, 'CHAT_ALLOWED_FILE_TYPES', [])
        
        if file.content_type not in allowed_types:
            return False, f"File type '{file.content_type}' not allowed"
        return True, None
    
    @staticmethod
    def validate_file_size(file, max_size=None):
        """Validate file size"""
        if max_size is None:
            max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 25 * 1024 * 1024)
        
        if file.size > max_size:
            return False, f"File too large. Maximum size is {max_size // (1024*1024)}MB"
        return True, None
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename to prevent directory traversal"""
        import os
        import re
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename


class WebSocketAuth:
    """WebSocket authentication utilities"""
    
    @staticmethod
    def authenticate_websocket(scope):
        """Authenticate WebSocket connection"""
        try:
            # Try to get token from query string
            query_string = scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                for param in query_string.split('&'):
                    if param.startswith('token='):
                        token = param.split('=', 1)[1]
                        break
            
            if token:
                # Validate JWT token
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    user = User.objects.get(id=payload['user_id'])
                    return user
                except (jwt.InvalidTokenError, User.DoesNotExist):
                    pass
            
            # Try session authentication
            if 'session' in scope:
                session = scope['session']
                user_id = session.get('_auth_user_id')
                if user_id:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    try:
                        return User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        pass
            
            return AnonymousUser()
            
        except Exception:
            return AnonymousUser()
    
    @staticmethod
    def validate_room_access(user, company_id, session_id):
        """Validate user has access to the room"""
        # For now, allow access if user is authenticated or if it's a valid session
        # In production, add proper authorization logic
        if user.is_authenticated:
            return True
        
        # Check if session exists and is valid
        try:
            from chatbot.models import ChatSession
            session = ChatSession.objects.get(session_id=session_id, company_id=company_id)
            return True
        except ChatSession.DoesNotExist:
            return False


def generate_signed_url(file_path, expiry_minutes=60):
    """Generate signed URL for private file access"""
    import time
    import hmac
    from urllib.parse import quote
    
    # Create expiry timestamp
    expiry = int(time.time()) + (expiry_minutes * 60)
    
    # Create signature
    message = f"{file_path}:{expiry}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Return signed URL
    return f"/media/secure/{quote(file_path)}?expires={expiry}&signature={signature}"


def validate_signed_url(file_path, expires, signature):
    """Validate signed URL"""
    import time
    import hmac
    
    # Check expiry
    if int(time.time()) > int(expires):
        return False
    
    # Validate signature
    message = f"{file_path}:{expires}"
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

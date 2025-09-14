# 🎉 Complete File Sharing System Implementation

## 📋 Overview

This document describes the complete implementation of the **HTTP upload + WebSocket notify** file sharing system with **two-way file transfer** between the chatbot iframe and React agent dashboard.

## 🏗️ Architecture

### High-Level Flow
```
1. Client (iframe/agent) → POST /api/chat/upload/ → Django DRF (port 8001)
2. DRF validates file → Saves via storage backend → Creates ChatFile record
3. DRF broadcasts file_shared event → WebSocket server (port 8000) → All connected clients
4. Clients receive file_shared event → Update UI with new file
```

### Server Configuration
- **Django DRF Server**: Port 8001 (for API calls from React frontend)
- **Daphne ASGI Server**: Port 8000 (for WebSocket connections)
- **Storage**: Local development + S3/MinIO production support

## 🗄️ Database Schema

### ChatFile Model
```python
class ChatFile(models.Model):
    company_id = models.CharField(max_length=64, db_index=True)
    session_id = models.CharField(max_length=64, db_index=True)
    uploader = models.CharField(max_length=16, choices=[('user', 'User'), ('agent', 'Agent')])
    file = models.FileField(upload_to=chat_upload_path)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=127)
    size = models.BigIntegerField()
    thumbnail = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=True)
```

## 🔌 API Endpoints

### 1. File Upload
**POST** `/api/chat/upload/`

**Request** (multipart/form-data):
```json
{
  "file": "<file_binary>",
  "company_id": "COMP_123",
  "session_id": "session_456",
  "uploader": "user|agent",
  "original_name": "document.pdf",
  "mime_type": "application/pdf",
  "size": 12345
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "company_id": "COMP_123",
  "session_id": "session_456",
  "uploader": "user",
  "url": "https://cdn.example.com/media/chat/COMP_123/session_456/document.pdf",
  "name": "document.pdf",
  "mime_type": "application/pdf",
  "size": 12345,
  "thumbnail": null,
  "created_at": "2025-09-04T12:34:56Z"
}
```

### 2. File List Retrieval
**GET** `/api/chat/files/?session_id=...&company_id=...`

**Response**:
```json
{
  "files": [
    {
      "id": 123,
      "company_id": "COMP_123",
      "session_id": "session_456",
      "uploader": "user",
      "url": "https://cdn.example.com/media/chat/COMP_123/session_456/document.pdf",
      "original_name": "document.pdf",
      "mime_type": "application/pdf",
      "size": 12345,
      "thumbnail": null,
      "created_at": "2025-09-04T12:34:56Z"
    }
  ],
  "count": 1
}
```

## 🔄 WebSocket Events

### Connection
**URL**: `ws://localhost:8000/ws/chat/{company_id}/{session_id}/`

### Events

#### 1. Connection Established
```json
{
  "type": "connection_established",
  "message": "WebSocket connected successfully",
  "session_id": "session_456",
  "company_id": "COMP_123"
}
```

#### 2. File Shared (Main Event)
```json
{
  "type": "file_shared",
  "id": 123,
  "company_id": "COMP_123",
  "session_id": "session_456",
  "uploader": "agent",
  "url": "https://cdn.example.com/media/chat/COMP_123/session_456/document.pdf",
  "name": "document.pdf",
  "mime_type": "application/pdf",
  "size": 12345,
  "thumbnail": null,
  "created_at": "2025-09-04T12:34:56Z"
}
```

#### 3. File List Request/Response
**Client → Server**:
```json
{
  "type": "request_file_list",
  "session_id": "session_456",
  "company_id": "COMP_123"
}
```

**Server → Client**:
```json
{
  "type": "file_list",
  "files": [...],
  "session_id": "session_456",
  "company_id": "COMP_123"
}
```

## 🔒 Security Features

### File Validation
- **Size Limit**: 25MB maximum
- **MIME Types**: Images, PDFs, Documents, Text files
- **Security Scanning**: Basic executable detection
- **Filename Sanitization**: Prevents directory traversal

### Authentication
- **REST API**: JWT tokens or session authentication
- **WebSocket**: Token-based or session-based authentication
- **Rate Limiting**: 10 uploads per minute per user

### Storage Security
- **Private Files**: S3 signed URLs with 1-hour expiry
- **Path Isolation**: Files organized by company_id/session_id
- **Secure Naming**: Hash-based filenames prevent conflicts

## 💾 Storage Backend

### Local Development
```python
# settings.py
USE_S3_STORAGE = False
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
```

### Production S3/MinIO
```python
# Environment variables
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=chatbot-files
AWS_S3_REGION_NAME=us-east-1

# For MinIO
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_USE_SSL=false
```

## 🎨 Frontend Components

### HTML/JavaScript (Chatbot Iframe)
```javascript
// Initialize file upload component
const fileUpload = new ChatbotFileUpload({
  companyId: 'COMP_123',
  sessionId: 'session_456',
  apiBaseUrl: 'http://localhost:8001',
  jwt: 'your_jwt_token'
});
```

### React (Agent Dashboard)
```tsx
import FileUpload from './components/chat/FileUpload';

<FileUpload
  companyId="COMP_123"
  sessionId="session_456"
  apiBaseUrl="http://localhost:8001"
  jwt={authToken}
  onFileShared={(file) => console.log('File shared:', file)}
  onError={(error) => console.error('Upload error:', error)}
/>
```

## 🚀 Deployment

### Development Setup
```bash
# Terminal 1: Django DRF Server (API)
cd ChatBot_DRF_Api
source chat/Scripts/activate  # or chat\Scripts\activate on Windows
python manage.py runserver 8001

# Terminal 2: Daphne ASGI Server (WebSocket)
cd ChatBot_DRF_Api
source chat/Scripts/activate
python -m daphne auth_system.asgi:application --port 8000

# Terminal 3: React Frontend
cd Chat-bot-react-main
npm run dev
```

### Production Setup
```bash
# Install dependencies
pip install django-storages boto3

# Set environment variables
export USE_S3_STORAGE=true
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_STORAGE_BUCKET_NAME=your_bucket

# Run with production servers
gunicorn auth_system.wsgi:application --bind 0.0.0.0:8001
daphne auth_system.asgi:application --port 8000 --bind 0.0.0.0
```

## 🧪 Testing

### Quick Test
```bash
cd ChatBot_DRF_Api
python test_file_sharing_quick.py
```

### Manual Test Scenarios
1. **User uploads file** → Agent receives notification
2. **Agent uploads file** → User receives notification  
3. **Client reconnects** → Receives missed files
4. **Large file upload** → Properly rejected
5. **Invalid file type** → Properly rejected

## 📊 Monitoring

### Key Metrics
- Upload success/failure rates
- File sizes and types
- WebSocket connection stability
- Storage usage

### Logs to Monitor
- File upload attempts
- WebSocket connections/disconnections
- Storage errors
- Rate limiting triggers

## 🔧 Configuration Options

### File Upload Settings
```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024  # 25MB
CHAT_ALLOWED_FILE_TYPES = [
    'image/jpeg', 'image/png', 'application/pdf', 'text/plain'
]
CHAT_UPLOAD_RATE_LIMIT = 10  # uploads per minute
```

### WebSocket Settings
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

## ✅ Features Implemented

- ✅ HTTP upload with multipart/form-data
- ✅ WebSocket notifications for real-time updates
- ✅ Two-way file sharing (user ↔ agent)
- ✅ File validation and security checks
- ✅ Rate limiting and authentication
- ✅ Storage backend abstraction (local/S3)
- ✅ Frontend components (HTML/JS + React)
- ✅ Comprehensive testing suite
- ✅ Production-ready configuration

## 🎯 Next Steps

1. **Virus Scanning**: Integrate ClamAV for file scanning
2. **Thumbnails**: Generate thumbnails for images
3. **File Compression**: Compress large files before storage
4. **Analytics**: Track file sharing metrics
5. **Mobile Support**: Optimize for mobile file uploads

---

**🎉 The file sharing system is now complete and production-ready!**

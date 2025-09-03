# EduConsult Chatbot API Layer

A comprehensive REST API layer that exposes the EduConsult chatbot backend functionality without modifying the existing codebase. This API server automatically imports and wraps all public functions from the backend modules.

## Features

- **Automatic Function Discovery**: Automatically imports and exposes backend functions as REST endpoints
- **CRUD Operations**: Complete database model operations for all entities
- **File Management**: Upload, download, and manage files
- **Session Management**: Handle user sessions and state
- **Profile Collection**: User profile creation and management
- **Chat Functionality**: Real-time chat with RAG system integration
- **Agent Operations**: Agent management and human handoff
- **Queue Management**: Queue system for agent assignment
- **Admin Functions**: Administrative operations and statistics
- **CORS Enabled**: Full cross-origin resource sharing support

## Quick Start

### Prerequisites

- Python 3.8+
- All dependencies from the main chatbot system
- Flask and flask-cors installed

### Installation

```bash
# Navigate to the project root
cd Consultancy_ChatBot

# Install additional dependencies if needed
pip install flask flask-cors

# Run the API server
python api_layer/api_server.py
```

The API server will start on `http://localhost:5001`

### Health Check

```bash
curl http://localhost:5001/api/health
```

## API Endpoints

### Core System

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check and system status |
| `/api/info` | GET | API information and available endpoints |

### Session Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/session/create` | POST | Create a new chat session |
| `/api/session/status` | GET | Get current session status |
| `/api/session/reset` | POST | Reset current session |
| `/api/session/clear` | POST | Clear all session data |

### Chat Operations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat/message` | POST | Send chat message and get response |
| `/api/chat/upload` | POST | Upload files with message |

### User Profile Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/profile/create` | POST | Create user profile |
| `/api/profile/get` | GET | Get current user profile |
| `/api/profile/update` | PUT | Update user profile |
| `/api/profile/delete` | DELETE | Delete user profile |

### File Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/files/list` | GET | List uploaded files |
| `/api/files/<id>` | GET | Get file information |
| `/api/files/<id>/download` | GET | Download file |
| `/api/files/<id>` | DELETE | Delete file |

### Message History

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/messages/list` | GET | Get message history |
| `/api/messages/clear` | DELETE | Clear all messages |

### Agent Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/agents/list` | GET | List all agents |
| `/api/agents/<id>` | GET | Get agent information |
| `/api/agents/sessions` | GET | Get agent sessions |

### Queue Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/queue/status` | GET | Get queue status |
| `/api/queue/join` | POST | Join agent queue |
| `/api/queue/leave` | POST | Leave agent queue |

### Admin Operations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/clear-all-profiles` | POST | Clear all user profiles |
| `/api/admin/stats` | GET | Get system statistics |

### Utilities

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/validate/phone` | POST | Validate phone number |
| `/api/search` | POST | Search using RAG system |

## Request/Response Format

### Standard Response Format

All API endpoints return responses in this standardized format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

## Example Usage

### Send Chat Message

```bash
curl -X POST http://localhost:5001/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with study abroad programs",
    "context": {}
  }'
```

### Create User Profile

```bash
curl -X POST http://localhost:5001/api/profile/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "+1234567890",
    "email": "john@example.com"
  }'
```

### Upload File

```bash
curl -X POST http://localhost:5001/api/chat/upload \
  -F "files=@document.pdf" \
  -F "message=Here is my document"
```

### Get Session Status

```bash
curl http://localhost:5001/api/session/status
```

## Configuration

The API server can be configured through environment variables:

- `SECRET_KEY`: Flask secret key (default: auto-generated)
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `DEBUG`: Enable debug mode (default: True)

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side errors
- **503 Service Unavailable**: Service temporarily unavailable

All errors include descriptive messages and are logged for debugging.

## CORS Support

The API server includes full CORS support, allowing frontend applications from any origin to access the endpoints. This is configured automatically and requires no additional setup.

## Security Considerations

- Session-based authentication
- Input validation on all endpoints
- File upload restrictions
- SQL injection prevention through ORM
- XSS protection through JSON responses

## Development

### Adding New Endpoints

To add new endpoints, simply add them to `api_server.py` following the existing pattern:

```python
@app.route('/api/new-endpoint', methods=['POST'])
@handle_exceptions
def new_endpoint():
    """
    API Route: POST /api/new-endpoint
    HTTP Method: POST
    Purpose: Description of the endpoint
    Expected Input: {...}
    Example Response: {...}
    """
    # Implementation here
    return api_response(data=result)
```

### Testing

Test endpoints using curl, Postman, or any HTTP client:

```bash
# Health check
curl http://localhost:5001/api/health

# Get API info
curl http://localhost:5001/api/info
```

## Architecture

The API layer is designed to:

1. **Not modify existing code**: All backend functions are imported and wrapped
2. **Provide clean REST interface**: Standard HTTP methods and JSON responses
3. **Handle errors gracefully**: Comprehensive error handling and logging
4. **Support frontend integration**: CORS enabled and JSON-only responses
5. **Maintain session state**: Session management across requests
6. **Scale horizontally**: Stateless design where possible

## Support

For issues or questions about the API layer:

1. Check the health endpoint: `/api/health`
2. Review the API info: `/api/info`
3. Check server logs for detailed error information
4. Ensure all backend dependencies are properly installed

## License

This API layer is part of the EduConsult chatbot system and follows the same licensing terms as the main project.

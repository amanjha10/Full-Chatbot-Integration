# Enhanced Chatbot System Documentation

## Overview

This document describes the enhanced multi-tenant chatbot system with comprehensive admin dashboard, agent management, real-time communication, and company isolation features.

## System Architecture

### Backend (Django REST Framework)
- **Authentication System**: JWT-based authentication with role-based access control
- **Admin Dashboard**: Comprehensive management interface for admins
- **Agent Dashboard**: Specialized interface for customer service agents
- **Human Handoff**: Seamless escalation from bot to human agents
- **Real-time Communication**: WebSocket-based chat system
- **Company Isolation**: Multi-tenant architecture with strict data isolation

### Frontend (React + TypeScript)
- **Role-based Routing**: Different interfaces for SuperAdmin, Admin, and Agent roles
- **Real-time Dashboard**: Live statistics and session management
- **Chat Interface**: Modern, responsive chat components
- **Company Context**: Comprehensive company isolation in the frontend

## Key Features

### 1. Enhanced Admin Dashboard

#### Statistics and Analytics
- **Real-time Metrics**: Live session counts, agent status, user statistics
- **Company-specific Data**: Filtered by company for proper isolation
- **Interactive Charts**: Visual representation of key metrics

#### Session Management
- **Pending Sessions**: View and assign pending customer sessions
- **Active Sessions**: Monitor ongoing conversations
- **Session Assignment**: Intelligent agent assignment based on availability
- **Priority Handling**: High, Medium, Low priority classification

#### User Profile Management
- **Favorites System**: Mark important users as favorites
- **Bulk Operations**: Export user data, clear non-favorites
- **Search and Filter**: Advanced filtering capabilities
- **Data Export**: CSV export functionality

### 2. Agent Dashboard

#### Personal Statistics
- **Performance Metrics**: Sessions handled, response times
- **Status Management**: Available, Busy, Offline status
- **Daily/Total Counts**: Track productivity over time

#### Session Handling
- **Accept Sessions**: One-click session acceptance
- **Real-time Chat**: Integrated chat interface
- **Session Completion**: Mark sessions as complete
- **File Sharing**: Support for file attachments

### 3. Real-time Communication System

#### WebSocket Implementation
- **Company-isolated Channels**: Separate channels per company
- **Message Types**: Chat messages, typing indicators, system notifications
- **Connection Management**: Auto-reconnection, connection status
- **File Support**: File upload and sharing capabilities

#### Chat Features
- **Typing Indicators**: Real-time typing status
- **Message History**: Persistent chat history
- **Agent Notifications**: Join/leave notifications
- **Error Handling**: Graceful error recovery

### 4. Company Isolation and Multi-tenancy

#### Backend Isolation
- **Model-level Filtering**: Automatic company_id filtering
- **API Endpoints**: Company-aware data access
- **Permission Checks**: Role and company-based permissions
- **WebSocket Isolation**: Company-specific WebSocket channels

#### Frontend Isolation
- **Company Context**: React context for company management
- **API Interceptors**: Automatic company_id injection
- **Access Validation**: Client-side company access checks
- **Error Handling**: Company access violation handling

## API Endpoints

### Admin Dashboard
```
GET  /api/admin-dashboard/dashboard-stats/          # Dashboard statistics
GET  /api/admin-dashboard/pending-sessions/         # Pending sessions
POST /api/admin-dashboard/assign-session/           # Assign session to agent
GET  /api/admin-dashboard/user-profiles/            # User profiles
POST /api/admin-dashboard/user-profiles/toggle-favorite/  # Toggle favorite
POST /api/admin-dashboard/user-profiles/clear-non-favorites/  # Clear profiles
GET  /api/admin-dashboard/available-agents/         # Available agents
```

### Agent Dashboard
```
GET  /api/agent-dashboard/stats/                    # Agent statistics
GET  /api/agent-dashboard/pending-sessions/         # Agent's pending sessions
GET  /api/agent-dashboard/active-sessions/          # Agent's active sessions
POST /api/agent-dashboard/accept-session/           # Accept a session
POST /api/agent-dashboard/complete-session/         # Complete a session
```

### Authentication
```
POST /api/auth/login/                               # User login
GET  /api/auth/profile/                             # User profile
GET  /api/auth/list-admins/                         # List companies (SuperAdmin)
GET  /api/auth/super-admin-stats/                   # SuperAdmin statistics
```

## WebSocket Endpoints

### Chat Communication
```
ws://localhost:8000/ws/chat/{company_id}/{session_id}/
```

#### Message Types
- `chat_message`: Regular chat messages
- `typing_indicator`: Typing status updates
- `system_message`: System notifications
- `agent_joined`: Agent join notifications
- `agent_left`: Agent leave notifications
- `error`: Error messages

## Installation and Setup

### Backend Setup
1. **Install Dependencies**
   ```bash
   cd ChatBot_DRF_Api
   pip install -r requirements.txt
   ```

2. **Database Migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create SuperAdmin**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup
1. **Install Dependencies**
   ```bash
   cd Chat-bot-react-main
   npm install
   ```

2. **Environment Configuration**
   ```bash
   # Create .env file
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

3. **Run Development Server**
   ```bash
   npm run dev
   ```

### WebSocket Setup
1. **Install Redis** (for WebSocket channel layer)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

2. **Configure Django Channels**
   - Already configured in `settings.py`
   - Uses Redis as channel layer backend

## Testing

### Company Isolation Testing
Run the comprehensive test script:
```bash
cd ChatBot_DRF_Api
python test_company_isolation.py
```

This tests:
- Admin data isolation
- Agent access restrictions
- SuperAdmin global access
- Cross-company access prevention

### Manual Testing Checklist

#### Admin Dashboard
- [ ] Dashboard loads with correct statistics
- [ ] Pending sessions show only company-specific data
- [ ] Session assignment works correctly
- [ ] User profiles are company-filtered
- [ ] Favorites system functions properly
- [ ] Export functionality works

#### Agent Dashboard
- [ ] Agent statistics display correctly
- [ ] Pending sessions are agent-specific
- [ ] Session acceptance works
- [ ] Real-time chat functions
- [ ] Session completion works
- [ ] File sharing works

#### Real-time Communication
- [ ] WebSocket connections establish
- [ ] Messages send and receive correctly
- [ ] Typing indicators work
- [ ] File uploads function
- [ ] Connection recovery works
- [ ] Company isolation maintained

#### Company Isolation
- [ ] Users see only their company data
- [ ] API calls include company context
- [ ] WebSocket channels are isolated
- [ ] SuperAdmin can access all companies
- [ ] Cross-company access is prevented

## Security Considerations

### Authentication
- JWT tokens with expiration
- Role-based access control
- Company-based data isolation
- Secure password handling

### Data Protection
- Company-specific data filtering
- API endpoint protection
- WebSocket channel isolation
- Input validation and sanitization

### Best Practices
- Regular token refresh
- Secure WebSocket connections (WSS in production)
- HTTPS enforcement
- CORS configuration
- Rate limiting (recommended)

## Deployment

### Production Considerations
1. **Environment Variables**
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`
   - Set secure `SECRET_KEY`
   - Configure database credentials

2. **WebSocket Configuration**
   - Use WSS (secure WebSocket)
   - Configure proper CORS settings
   - Set up Redis cluster for scaling

3. **Static Files**
   - Configure static file serving
   - Use CDN for better performance
   - Optimize frontend build

4. **Database**
   - Use production database (PostgreSQL recommended)
   - Set up database backups
   - Configure connection pooling

## Troubleshooting

### Common Issues

#### WebSocket Connection Failed
- Check Redis server is running
- Verify WebSocket URL format
- Check CORS configuration
- Ensure proper authentication

#### Company Data Not Filtered
- Verify company_id in localStorage
- Check API interceptor configuration
- Validate backend filtering logic
- Test with different user roles

#### Session Assignment Failed
- Check agent availability
- Verify company matching
- Test with proper permissions
- Check database constraints

### Debug Tools
- Browser Developer Tools for WebSocket debugging
- Django Debug Toolbar for API debugging
- Redis CLI for channel layer debugging
- Network tab for API request inspection

## Future Enhancements

### Planned Features
1. **Advanced Analytics**: Detailed reporting and analytics
2. **Mobile App**: React Native mobile application
3. **AI Integration**: Enhanced chatbot capabilities
4. **Video Chat**: WebRTC-based video communication
5. **Multi-language**: Internationalization support

### Scalability Improvements
1. **Microservices**: Break into smaller services
2. **Load Balancing**: Horizontal scaling support
3. **Caching**: Redis-based caching layer
4. **CDN Integration**: Global content delivery
5. **Database Sharding**: Company-based data sharding

## Support and Maintenance

### Monitoring
- Set up application monitoring
- Configure error tracking
- Monitor WebSocket connections
- Track performance metrics

### Backup Strategy
- Regular database backups
- File storage backups
- Configuration backups
- Disaster recovery plan

### Updates
- Regular security updates
- Feature updates and enhancements
- Bug fixes and improvements
- Performance optimizations

---

For technical support or questions, please refer to the development team or create an issue in the project repository.

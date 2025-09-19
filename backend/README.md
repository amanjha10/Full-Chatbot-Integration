# 🚀 Django Multi-tenant Chatbot System

A comprehensive Django REST Framework chatbot system with complete multi-tenant support, role-based access control, and company-based data isolation.

## ✨ Key Features

### 🏢 Multi-tenant Architecture
- **Complete Company Isolation**: Each company's data is completely separated
- **Company-based Authentication**: JWT tokens include company context
- **Role-based Access Control**: SUPERADMIN > ADMIN > AGENT hierarchy
- **Secure Data Filtering**: All queries filtered by company_id

### 💬 Chatbot System
- **AI-powered Conversations**: Intelligent chatbot with RAG integration
- **6-step Profile Collection**: Systematic user information gathering
- **Session Management**: Persistent chat sessions with company context
- **Human Handoff**: Seamless escalation to human agents
- **📁 File Upload Support**: Upload and share files in chat messages

### 📁 File Upload Features (NEW!)
- **Multi-format Support**: Images, documents, audio, video, archives
- **Secure Storage**: Company-isolated file storage with 10MB limit
- **Chat Integration**: Send text, attachments, or both in messages
- **Agent Access**: Agents can view and download user attachments
- **File Validation**: Type and size validation with error handling

### 👥 User Management
- **SuperAdmin**: Manages all companies and plans
- **Admin**: Manages company-specific agents and sessions
- **Agent**: Handles assigned customer sessions

### 🔐 Security Features
- **JWT Authentication**: Secure token-based authentication
- **Company Isolation**: Cross-company access prevention
- **Role-based Permissions**: Granular access control
- **Password Management**: Secure password generation and reset

## 🏗️ System Architecture

```
SuperAdmin
├── Creates Admin Users (with company_id)
│
Admin (Company A)
├── Creates Agents (Company A only)
├── Views Profiles (Company A only)
├── Manages Sessions (Company A only)
│
Agent (Company A)
├── Handles Assigned Sessions (Company A only)
├── Sends Messages (Company A sessions only)
├── Updates Status (Own status only)
```

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd django-chatbot-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Start Development Server
```bash
python manage.py runserver
```

## 📚 Documentation

### 📖 Main Documentation
- **[📋 Complete API Documentation](docs/COMPLETE_API_DOCUMENTATION.md)** - Full API reference
- **[🧪 Step-by-Step Testing Guide](docs/STEP_BY_STEP_TESTING_GUIDE.md)** - Comprehensive testing
- **[📋 Quick API Reference](docs/QUICK_API_REFERENCE.md)** - Quick reference guide
- **[🚀 Deployment Setup Guide](docs/DEPLOYMENT_SETUP_GUIDE.md)** - Production deployment

### 🔧 Implementation Details
- **[🏢 Company Isolation Complete](docs/COMPANY_ISOLATION_COMPLETE.md)** - Multi-tenant architecture
- **[🔐 Unified Login Documentation](docs/UNIFIED_LOGIN_DOCUMENTATION.md)** - Authentication system
- **[👥 Admin Dashboard API](docs/ADMIN_DASHBOARD_API.md)** - Admin functionality

### 🧪 Testing Resources
- **[🧪 Complete Testing Guide](docs/COMPLETE_TESTING_GUIDE.md)** - Full testing procedures
- **[📮 Postman API Testing Guide](docs/POSTMAN_API_TESTING_GUIDE.md)** - Postman setup
- **See `tests/` directory for Python test scripts and Postman collections**

## 🌐 API Endpoints Overview

### 🔑 Authentication
- `POST /api/auth/login/` - Universal login for all roles
- `POST /api/auth/token/refresh/` - Refresh JWT token

### 🏢 SuperAdmin APIs
- `POST /api/auth/create-admin/` - Create admin with company
- `GET /api/auth/list-admins/` - List all admins
- `PUT /api/auth/update-admin/{id}/` - Update admin
- `DELETE /api/auth/delete-admin/{id}/` - Delete admin

### 👥 Admin Dashboard APIs
- `POST /api/admin-dashboard/create-agent/` - Create company agent
- `GET /api/admin-dashboard/list-agents/` - List company agents
- `GET /api/admin-dashboard/user-profiles/` - View company profiles

### 👨‍💼 Agent APIs
- `POST /api/admin-dashboard/agent-first-login/` - Setup password
- `GET /api/human-handoff/agent/sessions/` - View assigned sessions
- `POST /api/human-handoff/agent/send-message/` - Send message

### 💬 Chatbot APIs
- `POST /api/chatbot/chat/` - Send chat message (now supports attachments!)
- `POST /api/chatbot/upload/` - Upload files for chat messages (NEW!)
- `POST /api/chatbot/create-profile/` - Create user profile
- `GET /api/chatbot/session-status/` - Check session status

### 🔄 Human Handoff APIs
- `POST /api/human-handoff/escalate/` - Escalate to human
- `POST /api/human-handoff/assign/` - Assign to agent
- `GET /api/human-handoff/sessions/` - List escalated sessions

## 🧪 Testing

### Quick Test
```bash
# Test SuperAdmin login
python tests/simple_login_test.py

# Test complete system
python tests/test_complete_system_final.py

# Test company isolation
python tests/test_company_isolation_complete.py
```

### Postman Testing
1. Import `tests/Complete_Chatbot_System_API.postman_collection.json`
2. Set up environment variables
3. Follow the testing guide in `docs/STEP_BY_STEP_TESTING_GUIDE.md`

## 🏢 Multi-tenant Example

### Company A (Tesla)
- Admin: `admin@tesla.com` (company_id: TES001)
- Agent: `john@tesla.com` (can only see Tesla sessions)
- Sessions: All prefixed with TES001

### Company B (SpaceX)
- Admin: `admin@spacex.com` (company_id: SPA001)  
- Agent: `jane@spacex.com` (can only see SpaceX sessions)
- Sessions: All prefixed with SPA001

### Isolation Guarantee
- Tesla admin cannot see SpaceX agents
- SpaceX agent cannot access Tesla sessions
- All data queries filtered by company_id

## 📊 Project Structure

```
├── docs/                          # 📚 All documentation
├── tests/                         # 🧪 Test scripts and Postman collections
├── auth_system/                   # ⚙️ Django project settings
├── authentication/                # 🔐 User authentication app
├── admin_dashboard/               # 👥 Admin and agent management
├── chatbot/                       # 💬 Chatbot functionality
├── human_handoff/                 # 🔄 Human agent handoff
├── websocket_chat/                # 🔌 WebSocket support (optional)
├── manage.py                      # 🐍 Django management
├── requirements.txt               # 📦 Python dependencies
└── .gitignore                     # 🚫 Git ignore rules
```

## 🚀 Production Deployment

See **[Deployment Setup Guide](docs/DEPLOYMENT_SETUP_GUIDE.md)** for:
- Production settings configuration
- Database setup (PostgreSQL recommended)
- Nginx and Gunicorn configuration
- SSL and security settings
- Monitoring and maintenance

## 🔧 Development

### Environment Variables
Create `.env` file:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=chatbot_system
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### Database Models
- **User**: Custom user with role and company_id
- **Agent**: Company-specific agents
- **ChatSession**: Sessions with company context
- **UserProfile**: User profiles linked to companies
- **HumanHandoff**: Escalation management

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Documentation**: Check `docs/` directory
- **Testing**: Use `tests/` directory resources
- **Issues**: Create GitHub issues for bugs or features
- **API Reference**: See `docs/QUICK_API_REFERENCE.md`

---

**🚀 Ready to build multi-tenant chatbot systems with complete company isolation!**

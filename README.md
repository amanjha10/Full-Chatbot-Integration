# Full Chatbot Integration

A complete real-time chatbot system with agent dashboard, file sharing, and WebSocket communication.

## 🚀 Features

- **Real-time Chat**: WebSocket-based communication between users and agents
- **File Sharing**: Upload and share files with image previews (like Messenger)
- **Agent Dashboard**: React-based dashboard for agents to manage conversations
- **User Chatbot**: HTML/JavaScript chatbot widget for websites
- **Human Handoff**: Seamless escalation from bot to human agents
- **Redis Integration**: Cross-process communication and session management
- **Production Ready**: Clean console output, error handling, and deduplication

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Server  │    │   DRF Server    │    │ WebSocket Server│
│   Port: 6379    │◄──►│   Port: 8001    │    │   Port: 8000    │
│                 │    │                 │    │                 │
│ Channel Layer   │    │ • File Upload   │    │ • WebSocket     │
│ Communication   │    │ • API Endpoints │    │ • Real-time     │
│                 │    │ • Media Serving │    │   Notifications │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Redis Server**
- **Git**

## 🛠️ Installation Guide

### For macOS

#### 1. Install System Dependencies

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python (if not already installed)
brew install python

# Install Node.js
brew install node

# Install Redis
brew install redis
```

#### 2. Clone Repository

```bash
git clone https://github.com/amanjha10/Full-Chatbot-Integration.git
cd Full-Chatbot-Integration
```

#### 3. Backend Setup (Django + DRF)

```bash
# Navigate to backend directory
cd ChatBot_DRF_Api

# Create virtual environment
python3 -m venv chat
source chat/bin/activate  # On macOS/Linux

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

#### 4. Frontend Setup (React Agent Dashboard)

```bash
# Navigate to frontend directory
cd ../Chat-bot-react-main

# Install Node.js dependencies
npm install

# Build for production (optional)
npm run build
```

#### 5. Start Redis Server

```bash
# Start Redis server
brew services start redis

# Or run Redis in foreground
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

## 🚀 Running the Application

### Development Mode (3 Servers)

Open 3 terminal windows:

#### Terminal 1: Start Redis
```bash
redis-server
```

#### Terminal 2: Start Django DRF Server
```bash
cd ChatBot_DRF_Api
source chat/bin/activate
python manage.py runserver 8001
```

#### Terminal 3: Start WebSocket Server
```bash
cd ChatBot_DRF_Api
source chat/bin/activate
python -m daphne auth_system.asgi:application --port 8000
```

#### Terminal 4: Start React Development Server (Optional)
```bash
cd Chat-bot-react-main
npm start
```

### Production Mode (Single Server)

```bash
# Start Redis
redis-server &

# Start unified server (handles both HTTP and WebSocket)
cd ChatBot_DRF_Api
source chat/bin/activate
python -m daphne auth_system.asgi:application --port 8001
```

## 🌐 Access Points

- **Chatbot Widget**: `file:///.../New folder/chatbot-iframe.html`
- **Agent Dashboard**: `http://localhost:3000` (if React dev server is running)
- **Django Admin**: `http://localhost:8001/admin/`
- **API Endpoints**: `http://localhost:8001/api/`

## 📁 Project Structure

```
Full-Chatbot-Integration/
├── ChatBot_DRF_Api/           # Django backend
│   ├── auth_system/           # Main Django project
│   ├── chatbot/              # Chatbot app
│   ├── human_handoff/        # Agent management
│   ├── media/                # Uploaded files
│   ├── chat/                 # Virtual environment (gitignored)
│   └── requirements.txt      # Python dependencies
├── Chat-bot-react-main/      # React agent dashboard
│   ├── src/                  # React source code
│   ├── public/               # Static files
│   ├── node_modules/         # Node dependencies (gitignored)
│   └── package.json          # Node dependencies
├── New folder/               # HTML chatbot widget
│   └── chatbot-iframe.html   # Chatbot interface
└── README.md                 # This file
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in `ChatBot_DRF_Api/` directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Redis Configuration

The application uses Redis for:
- **Channel Layers**: Cross-process WebSocket communication
- **Session Storage**: User session management
- **File Notifications**: Real-time file sharing events

Default Redis configuration:
- **Host**: 127.0.0.1
- **Port**: 6379
- **Database**: 0

## 🔧 API Endpoints

### Chatbot API
- `POST /api/chatbot/chat/` - Send message to chatbot
- `POST /api/chat/upload/` - Upload files
- `GET /api/chat/files/{session_id}/` - Get session files

### Agent API
- `POST /api/human-handoff/agent/send-message/` - Agent send message
- `GET /api/human-handoff/sessions/` - Get agent sessions
- `POST /api/human-handoff/escalate/` - Escalate to human

### WebSocket Endpoints
- `ws://localhost:8000/ws/chat/{company_id}/{session_id}/` - Chat WebSocket
- `ws://localhost:8000/ws/agent/{agent_id}/` - Agent WebSocket
- `ws://localhost:8000/ws/config/{company_id}/` - Config WebSocket

## 🧪 Testing

### Test File Upload
```bash
cd ChatBot_DRF_Api
source chat/bin/activate
python test_websocket_file_sharing.py
```

### Test Agent-to-User Communication
```bash
python test_agent_to_chatbot.py
```

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check if Redis is running
   redis-cli ping

   # Start Redis if not running
   brew services start redis
   ```

2. **WebSocket Connection Failed**
   - Ensure WebSocket server is running on port 8000
   - Check if session is escalated for agent connections

3. **File Upload 404 Error**
   - Verify DRF server is running on port 8001
   - Check MEDIA_URL and MEDIA_ROOT settings

4. **CORS Errors**
   - Update CORS_ALLOWED_ORIGINS in settings.py
   - Ensure frontend URL is whitelisted

### Logs Location
- **Django Logs**: Console output
- **WebSocket Logs**: Console output
- **Redis Logs**: `/usr/local/var/log/redis.log` (macOS)

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in settings.py
- [ ] Configure proper SECRET_KEY
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Configure Redis with persistence
- [ ] Set up reverse proxy (Nginx)
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

# 🚀 Startup Guide for Chatbot System

## Port Configuration
- **Port 8000**: Daphne (WebSocket server for real-time communication)
- **Port 8001**: Django DRF (REST API server)
- **Port 5173**: React Frontend (Vite dev server)
- **Port 8080**: HTML Chatbot (Live Server)

## 🔧 Starting the Servers

### 1. Start Django DRF Server (Port 8001)
```bash
cd "ChatBot_DRF_Api"
env\Scripts\activate
python manage.py runserver 8001
```

### 2. Start Daphne WebSocket Server (Port 8000)
```bash
cd "ChatBot_DRF_Api"
env\Scripts\activate
daphne -b 0.0.0.0 auth_system.asgi:application --port 8000
```

### 3. Start React Frontend (Port 5173)
```bash
cd "Chat-bot-react-main"
npm run dev
```

### 4. Start HTML Chatbot (Port 8080)
```bash
cd "New folder"
# Use Live Server extension in VS Code or any static server
# Make sure it runs on port 8080
```

## 🧪 Testing URLs

### Admin/Agent Login & Dashboard
- **Login**: http://localhost:5173/login
- **Admin Dashboard**: http://localhost:5173/app/dashboard
- **Agent Management**: http://localhost:5173/app/agent-management
- **User Management**: http://localhost:5173/app/user-management
- **Agent Dashboard**: http://localhost:5173/agent/dashboard

### HTML Chatbot
- **Chatbot**: http://localhost:8080/hello.html
- **Direct Iframe**: http://localhost:8080/chatbot-iframe.html

### API Endpoints
- **REST API**: http://localhost:8001/api/
- **WebSocket**: ws://localhost:8000/ws/

## 🔍 Troubleshooting

### If Chatbot Shows "Connection Error":
1. Check if Django DRF is running on port 8001
2. Check if Daphne is running on port 8000
3. Check browser console for specific errors

### If Login Redirects After Refresh:
1. Check browser localStorage for auth tokens
2. Check console for AuthStore debug messages
3. Verify token is not expired

### If Human Handoff Not Working:
1. Check if sessions appear in admin dashboard
2. Verify WebSocket connection to port 8000
3. Check Django logs for handoff session creation

## 📝 Default Test Credentials

### Admin Login
- **Email**: admin@test.com
- **Password**: admin123

### Agent Login (after creation)
- **Email**: nath@gmail.com
- **Password**: nath123

### Company ID
- **Default**: TEST001

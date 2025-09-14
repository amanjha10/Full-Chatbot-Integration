# Quick Start Guide

## 🚀 For macOS Users

### One-Command Setup
```bash
# Clone and setup everything
git clone https://github.com/amanjha10/Full-Chatbot-Integration.git
cd Full-Chatbot-Integration
chmod +x setup_macos.sh
./setup_macos.sh
```

### Manual Setup (if script fails)

1. **Install Dependencies**
   ```bash
   # Install Homebrew
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install required packages
   brew install python node redis
   ```

2. **Setup Backend**
   ```bash
   cd ChatBot_DRF_Api
   python3 -m venv chat
   source chat/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   ```

3. **Setup Frontend**
   ```bash
   cd ../Chat-bot-react-main
   npm install
   ```

4. **Start Services**
   ```bash
   # Terminal 1: Redis
   redis-server
   
   # Terminal 2: Django API Server
   cd ChatBot_DRF_Api
   source chat/bin/activate
   python manage.py runserver 8001
   
   # Terminal 3: WebSocket Server
   cd ChatBot_DRF_Api
   source chat/bin/activate
   python -m daphne auth_system.asgi:application --port 8000
   
   # Terminal 4: React Dev Server (optional)
   cd Chat-bot-react-main
   npm start
   ```

## 🐧 For Linux Users

Replace `brew` commands with your package manager:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip nodejs npm redis-server
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip nodejs npm redis
```

## 🪟 For Windows Users

1. **Install Dependencies**
   - Download Python from python.org
   - Download Node.js from nodejs.org
   - Download Redis from GitHub releases or use WSL

2. **Use WSL (Recommended)**
   ```bash
   wsl --install
   # Then follow Linux instructions
   ```

3. **Or use Windows directly**
   - Use `python -m venv chat` instead of `python3 -m venv chat`
   - Use `chat\Scripts\activate` instead of `source chat/bin/activate`

## 🧪 Test the Installation

1. **Test File Upload**
   ```bash
   cd ChatBot_DRF_Api
   source chat/bin/activate  # or chat\Scripts\activate on Windows
   python test_websocket_file_sharing.py
   ```

2. **Test Agent Communication**
   ```bash
   python test_agent_to_chatbot.py
   ```

## 🌐 Access Points

- **Chatbot**: Open `New folder/chatbot-iframe.html` in browser
- **Agent Dashboard**: http://localhost:3000
- **API**: http://localhost:8001/api/
- **Admin**: http://localhost:8001/admin/

## 🔧 Common Issues

**Redis not starting:**
```bash
# macOS
brew services restart redis

# Linux
sudo systemctl restart redis

# Windows
# Download Redis for Windows or use WSL
```

**Port already in use:**
```bash
# Find process using port
lsof -i :8001  # macOS/Linux
netstat -ano | findstr :8001  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

**Virtual environment issues:**
```bash
# Remove and recreate
rm -rf ChatBot_DRF_Api/chat
cd ChatBot_DRF_Api
python3 -m venv chat
source chat/bin/activate
pip install -r requirements.txt
```

## 📱 Production Deployment

For production, use:
```bash
# Single server mode
redis-server &
cd ChatBot_DRF_Api
source chat/bin/activate
python -m daphne auth_system.asgi:application --port 8001
```

## 🆘 Need Help?

1. Check the main [README.md](README.md) for detailed documentation
2. Look at the troubleshooting section
3. Create an issue on GitHub
4. Check server logs for error messages

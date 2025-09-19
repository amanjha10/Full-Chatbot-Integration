# 🚀 Production Deployment Guide

## Server Information
- **IP Address**: 157.180.118.12
- **Domain**: bot.spell.com.np
- **Username**: root
- **Password**: q=vd]3#^7G9T%NV6m,

## 📋 Pre-Deployment Checklist

### ✅ Configuration Status
- [x] Environment files created (.env.production)
- [x] React application built (dist/ folder)
- [x] TypeScript errors fixed
- [x] Dynamic URL detection implemented
- [x] Production settings configured
- [x] Deployment script ready

### ⚠️ Known Issues (Acceptable for Production)
The following localhost references are **intentional** and will work correctly:

1. **Environment Files**: Contain localhost for database/Redis (services run locally on server)
2. **JavaScript Files**: Use dynamic detection - localhost for dev, domain for production
3. **Comments**: Some commented examples contain localhost (no impact)

## 🛠️ Deployment Steps

### Step 1: Connect to Server
```bash
ssh root@157.180.118.12
# Password: q=vd]3#^7G9T%NV6m,
```

### Step 2: Run Automated Deployment
```bash
# Clone the repository
git clone https://github.com/amanjha10/Full-Chatbot-Integration.git
cd Full-Chatbot-Integration

# Make deployment script executable
chmod +x deploy.sh

# Run deployment (this will take 10-15 minutes)
sudo bash deploy.sh
```

### Step 3: Verify Deployment
```bash
# Check service status
supervisorctl status

# Check logs
tail -f /var/log/chatbot_django.log
tail -f /var/log/chatbot_websocket.log
tail -f /var/log/chromadb.log

# Test the application
curl http://bot.spell.com.np
curl http://157.180.118.12
```

## 🌐 Application URLs

### Main Application
- **Frontend**: https://bot.spell.com.np
- **Admin Dashboard**: https://bot.spell.com.np/admin/
- **API**: https://bot.spell.com.np/api/

### Development URLs (for reference)
- **React Dev**: http://localhost:5173
- **Django API**: http://localhost:8001
- **WebSocket**: ws://localhost:8000

## 🔧 Architecture Overview

### Services Running on Server
1. **Nginx** (Port 80/443) - Web server and reverse proxy
2. **Django/Gunicorn** (Port 8001) - API backend
3. **Daphne** (Port 8000) - WebSocket server
4. **ChromaDB** (Port 8002) - Vector database
5. **PostgreSQL** (Port 5432) - Main database
6. **Redis** (Port 6379) - Caching and sessions

### File Structure on Server
```
/var/www/chatbot/
├── ChatBot_DRF_Api/          # Django backend
│   ├── chat/                 # Python virtual environment
│   ├── static/               # Static files
│   ├── media/                # Uploaded files
│   └── .env                  # Production environment
├── Chat-bot-react-main/      # React frontend
│   └── dist/                 # Built React files
└── deploy.sh                 # Deployment script
```

## 🔐 Security Configuration

### Firewall Rules
- Port 22 (SSH) - Open
- Port 80 (HTTP) - Open
- Port 443 (HTTPS) - Open
- All other ports - Closed

### SSL Certificate (TODO)
Currently running on HTTP. To enable HTTPS:
1. Obtain SSL certificate (Let's Encrypt recommended)
2. Update Nginx configuration
3. Update environment variables to use HTTPS URLs

## 📊 Monitoring and Logs

### Service Management
```bash
# Restart all services
supervisorctl restart all

# Restart specific service
supervisorctl restart chatbot_django
supervisorctl restart chatbot_websocket
supervisorctl restart chromadb

# View service status
supervisorctl status
```

### Log Files
- **Django**: `/var/log/chatbot_django.log`
- **WebSocket**: `/var/log/chatbot_websocket.log`
- **ChromaDB**: `/var/log/chromadb.log`
- **Nginx Access**: `/var/log/nginx/access.log`
- **Nginx Error**: `/var/log/nginx/error.log`

## 🐛 Troubleshooting

### Common Issues

#### 1. Services Not Starting
```bash
# Check supervisor logs
supervisorctl tail -f chatbot_django
supervisorctl tail -f chatbot_websocket

# Check system logs
journalctl -u supervisor
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
systemctl status postgresql

# Test database connection
sudo -u postgres psql -d chatbot_django -c "SELECT 1;"
```

#### 3. Permission Issues
```bash
# Fix file permissions
chown -R www-data:www-data /var/www/chatbot
chmod -R 755 /var/www/chatbot
```

#### 4. Nginx Configuration Issues
```bash
# Test Nginx configuration
nginx -t

# Reload Nginx
systemctl reload nginx
```

### Health Check Commands
```bash
# Check all services
curl http://localhost:8001/api/
curl http://localhost:8000/
curl http://localhost:8002/api/v1/heartbeat

# Check external access
curl http://bot.spell.com.np
curl http://157.180.118.12
```

## 🔄 Updates and Maintenance

### Updating the Application
```bash
cd /var/www/chatbot
git pull origin main

# Restart services
supervisorctl restart all

# Check status
supervisorctl status
```

### Database Migrations
```bash
cd /var/www/chatbot/ChatBot_DRF_Api
source chat/bin/activate
python manage.py migrate
```

### Static Files Update
```bash
cd /var/www/chatbot/ChatBot_DRF_Api
source chat/bin/activate
python manage.py collectstatic --noinput
```

## 📞 Support Information

### Default Admin Credentials
- **Username**: admin
- **Password**: Check database or reset using Django management commands

### Important Configuration Files
- **Nginx**: `/etc/nginx/sites-available/chatbot`
- **Supervisor**: `/etc/supervisor/conf.d/chatbot.conf`
- **Django Settings**: `/var/www/chatbot/ChatBot_DRF_Api/auth_system/settings.py`
- **Environment**: `/var/www/chatbot/ChatBot_DRF_Api/.env`

## ✅ Post-Deployment Verification

1. **Frontend Access**: Visit https://bot.spell.com.np
2. **Admin Panel**: Visit https://bot.spell.com.np/admin/
3. **API Health**: Check https://bot.spell.com.np/api/
4. **WebSocket**: Test chat functionality
5. **File Upload**: Test file upload in chatbot
6. **Multi-tenancy**: Test with different company IDs

## 🎯 Performance Optimization

### Recommended Settings
- **Gunicorn Workers**: 3 (adjust based on CPU cores)
- **Database Connections**: Monitor and adjust pool size
- **Redis Memory**: Monitor usage and adjust maxmemory
- **Nginx Caching**: Static files cached for 1 year

### Monitoring Tools
- **System Resources**: htop, iotop
- **Database**: PostgreSQL logs and pg_stat_activity
- **Application**: Django debug toolbar (development only)
- **Web Server**: Nginx access logs analysis

# Enhanced Chatbot System - Deployment Guide

## Overview

This guide covers the deployment of the enhanced multi-tenant chatbot system with admin dashboard, agent management, real-time communication, and company isolation features.

## Prerequisites

### System Requirements
- **Server**: Ubuntu 20.04+ or CentOS 8+ (minimum 4GB RAM, 2 CPU cores)
- **Database**: PostgreSQL 12+ or MySQL 8+
- **Cache**: Redis 6+
- **Web Server**: Nginx 1.18+
- **SSL Certificate**: Let's Encrypt or commercial SSL
- **Domain**: Configured domain name

### Software Dependencies
- Python 3.9+
- Node.js 16+
- npm or yarn
- Git

## Production Environment Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx redis-server postgresql postgresql-contrib git certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash chatbot
sudo usermod -aG sudo chatbot
```

### 2. Database Setup

#### PostgreSQL Configuration
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
ALTER USER chatbot_user CREATEDB;
\q

# Configure PostgreSQL for production
sudo nano /etc/postgresql/12/main/postgresql.conf
# Uncomment and modify:
# listen_addresses = 'localhost'
# max_connections = 100

sudo nano /etc/postgresql/12/main/pg_hba.conf
# Add line:
# local   chatbot_db      chatbot_user                    md5

sudo systemctl restart postgresql
```

#### Redis Configuration
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf
# Modify:
# bind 127.0.0.1
# maxmemory 256mb
# maxmemory-policy allkeys-lru

sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 3. Application Deployment

#### Backend Deployment
```bash
# Switch to application user
sudo su - chatbot

# Clone repository
git clone https://github.com/your-repo/enhanced-chatbot.git
cd enhanced-chatbot/ChatBot_DRF_Api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Create production settings
cp auth_system/settings.py auth_system/settings_prod.py
```

#### Production Settings Configuration
```python
# auth_system/settings_prod.py
import os
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chatbot_db',
        'USER': 'chatbot_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Redis for channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATIC_ROOT = '/home/chatbot/static/'
MEDIA_ROOT = '/home/chatbot/media/'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com",
]

# WebSocket settings
ASGI_APPLICATION = 'auth_system.asgi.application'
```

#### Environment Variables
```bash
# Create environment file
nano /home/chatbot/.env

# Add variables:
export SECRET_KEY='your-very-secure-secret-key'
export DB_PASSWORD='your_secure_password'
export DJANGO_SETTINGS_MODULE='auth_system.settings_prod'

# Load environment
echo "source /home/chatbot/.env" >> /home/chatbot/.bashrc
source /home/chatbot/.env
```

#### Database Migration and Static Files
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test the application
python manage.py runserver 0.0.0.0:8000
```

#### Frontend Deployment
```bash
# Navigate to frontend directory
cd /home/chatbot/enhanced-chatbot/Chat-bot-react-main

# Install dependencies
npm install

# Create production environment file
nano .env.production
# Add:
VITE_API_BASE_URL=https://your-domain.com/api

# Build for production
npm run build

# Move build files
sudo mkdir -p /var/www/chatbot
sudo cp -r dist/* /var/www/chatbot/
sudo chown -R www-data:www-data /var/www/chatbot
```

### 4. Web Server Configuration

#### Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/chatbot

# Add configuration:
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/chatbot;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /home/chatbot/static/;
    }

    location /media/ {
        alias /home/chatbot/media/;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### SSL Certificate
```bash
# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 5. Process Management

#### Gunicorn Configuration
```bash
# Create Gunicorn configuration
nano /home/chatbot/gunicorn.conf.py

# Add configuration:
bind = "127.0.0.1:8000"
workers = 3
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
user = "chatbot"
group = "chatbot"
```

#### Systemd Service Files
```bash
# Create Gunicorn service
sudo nano /etc/systemd/system/chatbot.service

# Add service configuration:
[Unit]
Description=Chatbot Gunicorn daemon
After=network.target

[Service]
User=chatbot
Group=chatbot
WorkingDirectory=/home/chatbot/enhanced-chatbot/ChatBot_DRF_Api
Environment="PATH=/home/chatbot/enhanced-chatbot/ChatBot_DRF_Api/venv/bin"
ExecStart=/home/chatbot/enhanced-chatbot/ChatBot_DRF_Api/venv/bin/gunicorn --config /home/chatbot/gunicorn.conf.py auth_system.asgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable chatbot
sudo systemctl start chatbot
sudo systemctl status chatbot
```

### 6. Monitoring and Logging

#### Log Configuration
```bash
# Create log directories
sudo mkdir -p /var/log/chatbot
sudo chown chatbot:chatbot /var/log/chatbot

# Configure Django logging in settings_prod.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/chatbot/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

#### Health Check Script
```bash
# Create health check script
nano /home/chatbot/health_check.sh

#!/bin/bash
# Health check script
curl -f http://localhost:8000/api/health/ || exit 1

chmod +x /home/chatbot/health_check.sh

# Add to crontab
crontab -e
# Add line:
# */5 * * * * /home/chatbot/health_check.sh
```

## Security Hardening

### 1. Firewall Configuration
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Database Security
```bash
# Secure PostgreSQL
sudo -u postgres psql
ALTER USER postgres PASSWORD 'secure_postgres_password';
\q

# Update pg_hba.conf for security
sudo nano /etc/postgresql/12/main/pg_hba.conf
# Change 'trust' to 'md5' for local connections
```

### 3. Application Security
- Regular security updates
- Strong passwords and keys
- Rate limiting implementation
- Input validation
- HTTPS enforcement

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
nano /home/chatbot/backup_db.sh

#!/bin/bash
BACKUP_DIR="/home/chatbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -h localhost -U chatbot_user chatbot_db > $BACKUP_DIR/chatbot_db_$DATE.sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

chmod +x /home/chatbot/backup_db.sh

# Schedule daily backups
crontab -e
# Add line:
# 0 2 * * * /home/chatbot/backup_db.sh
```

### 2. File Backup
```bash
# Backup media files and configurations
tar -czf /home/chatbot/backups/files_$(date +%Y%m%d).tar.gz /home/chatbot/media /home/chatbot/.env
```

## Maintenance

### 1. Updates
```bash
# Update application
cd /home/chatbot/enhanced-chatbot
git pull origin main

# Update backend
cd ChatBot_DRF_Api
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart chatbot

# Update frontend
cd ../Chat-bot-react-main
npm install
npm run build
sudo cp -r dist/* /var/www/chatbot/
```

### 2. Monitoring
- Monitor system resources (CPU, RAM, disk)
- Check application logs regularly
- Monitor database performance
- Track WebSocket connections
- Monitor SSL certificate expiration

## Troubleshooting

### Common Issues
1. **502 Bad Gateway**: Check Gunicorn service status
2. **WebSocket Connection Failed**: Verify Redis and Nginx WebSocket config
3. **Database Connection Error**: Check PostgreSQL service and credentials
4. **Static Files Not Loading**: Verify Nginx static file configuration
5. **SSL Issues**: Check certificate validity and Nginx SSL config

### Debug Commands
```bash
# Check service status
sudo systemctl status chatbot
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server

# View logs
sudo journalctl -u chatbot -f
tail -f /var/log/nginx/error.log
tail -f /var/log/chatbot/django.log

# Test connections
curl -I https://your-domain.com
redis-cli ping
psql -h localhost -U chatbot_user -d chatbot_db -c "SELECT 1;"
```

## Performance Optimization

### 1. Database Optimization
- Regular VACUUM and ANALYZE
- Proper indexing
- Connection pooling
- Query optimization

### 2. Caching
- Redis caching for frequently accessed data
- Browser caching for static files
- CDN for global content delivery

### 3. Application Optimization
- Code profiling and optimization
- Database query optimization
- Static file compression
- Image optimization

---

This deployment guide provides a comprehensive setup for production deployment. Adjust configurations based on your specific requirements and infrastructure.

#!/bin/bash

# Production Deployment Script for Full Chatbot Integration
# Server: 157.180.118.12 (bot.spell.com.np)

set -e  # Exit on any error

echo "🚀 Starting Full Chatbot Integration Deployment..."
echo "=================================================="

# Configuration
DOMAIN="bot.spell.com.np"
SERVER_IP="157.180.118.12"
PROJECT_DIR="/var/www/chatbot"
DJANGO_DIR="$PROJECT_DIR/ChatBot_DRF_Api"
REACT_DIR="$PROJECT_DIR/Chat-bot-react-main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "Step 1: System Updates and Dependencies"
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx supervisor git curl

print_status "Step 2: Create Project Directory"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

print_status "Step 3: Clone/Update Repository"
if [ -d ".git" ]; then
    print_status "Updating existing repository..."
    git pull origin main
else
    print_status "Cloning repository..."
    git clone https://github.com/amanjha10/Full-Chatbot-Integration.git .
fi

print_status "Step 4: Setup Python Virtual Environment"
cd $DJANGO_DIR
python3 -m venv chat
source chat/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt

print_status "Step 5: Setup Environment Variables"
cp .env.production .env
# Generate a secure secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
sed -i "s/your-production-secret-key-here-generate-new-one/$SECRET_KEY/" .env

print_status "Step 6: Database Setup"
sudo -u postgres createdb chatbot_django 2>/dev/null || print_warning "Database already exists"
sudo -u postgres createuser django_user 2>/dev/null || print_warning "User already exists"
sudo -u postgres psql -c "ALTER USER django_user PASSWORD 'django_secure_2024';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_django TO django_user;" 2>/dev/null || true

print_status "Step 7: Django Setup"
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py loaddata initial_data.json 2>/dev/null || print_warning "No initial data fixture found"

print_status "Step 8: Setup Nginx"
cat > /etc/nginx/sites-available/chatbot << 'EOF'
server {
    listen 80;
    server_name bot.spell.com.np 157.180.118.12;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bot.spell.com.np 157.180.118.12;
    
    # SSL Configuration (you'll need to add SSL certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # For now, comment out SSL and use HTTP only
    # Remove the listen 443 ssl line above and uncomment the line below for HTTP only
    # listen 80;
    
    client_max_body_size 100M;
    
    # Serve React build files
    location / {
        root /var/www/chatbot/Chat-bot-react-main/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Django API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /var/www/chatbot/ChatBot_DRF_Api/staticfiles/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Media files
    location /media/ {
        alias /var/www/chatbot/ChatBot_DRF_Api/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # WebSocket connections
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
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

print_status "Step 9: Setup Supervisor for Django and WebSocket"
cat > /etc/supervisor/conf.d/chatbot.conf << EOF
[program:chatbot_django]
command=$DJANGO_DIR/chat/bin/gunicorn auth_system.wsgi:application --bind 127.0.0.1:8001 --workers 3
directory=$DJANGO_DIR
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/chatbot_django.log

[program:chatbot_websocket]
command=$DJANGO_DIR/chat/bin/daphne -b 127.0.0.1 -p 8000 auth_system.asgi:application
directory=$DJANGO_DIR
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/chatbot_websocket.log

[program:chromadb]
command=$DJANGO_DIR/chat/bin/python chromadb_server.py
directory=$DJANGO_DIR
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/chromadb.log
EOF

print_status "Step 10: Set Permissions"
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

print_status "Step 11: Start Services"
systemctl enable redis-server
systemctl start redis-server
systemctl enable postgresql
systemctl start postgresql
systemctl enable nginx
systemctl start nginx
systemctl enable supervisor
systemctl start supervisor

supervisorctl reread
supervisorctl update
supervisorctl start all

print_status "Step 12: Setup Firewall"
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

print_status "Deployment Complete! 🎉"
echo "=================================================="
echo "🌐 Your chatbot is now available at:"
echo "   http://$DOMAIN"
echo "   http://$SERVER_IP"
echo ""
echo "📊 Admin Dashboard:"
echo "   http://$DOMAIN/admin/"
echo ""
echo "🔧 Service Status:"
supervisorctl status
echo ""
echo "📝 Log Files:"
echo "   Django: /var/log/chatbot_django.log"
echo "   WebSocket: /var/log/chatbot_websocket.log"
echo "   ChromaDB: /var/log/chromadb.log"
echo "   Nginx: /var/log/nginx/access.log"
echo ""
print_warning "Note: SSL certificates need to be configured for HTTPS"
print_warning "Update the Nginx configuration with your SSL certificates"

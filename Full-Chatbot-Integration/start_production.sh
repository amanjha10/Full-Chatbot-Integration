#!/bin/bash

# 🚀 Production Startup Script for Django + ChromaDB + React Chatbot System
# ========================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a service in background
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    local log_file=$4
    
    print_status "Starting $service_name on port $port..."
    
    if check_port $port; then
        print_warning "$service_name already running on port $port"
        return 0
    fi
    
    # Start the service in background
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    
    # Wait a moment and check if the service started
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_status "$service_name started successfully (PID: $pid)"
        echo $pid > "${service_name,,}.pid"
        return 0
    else
        print_error "Failed to start $service_name"
        return 1
    fi
}

# Main startup function
main() {
    print_header "🚀 STARTING PRODUCTION CHATBOT SYSTEM"
    print_header "====================================="
    
    # Check if we're in the right directory
    if [ ! -f "ChatBot_DRF_Api/manage.py" ]; then
        print_error "Please run this script from the Full-Chatbot-Integration directory"
        exit 1
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Navigate to Django directory
    cd ChatBot_DRF_Api
    
    print_header "📊 CURRENT PORT USAGE:"
    echo "   Redis: 6379"
    echo "   Django API: 8000"
    echo "   Daphne WebSocket: 8001"
    echo "   ChromaDB: 8002 (optional)"
    echo "   PostgreSQL: 5432"
    echo "   React Dev: 5173"
    echo "   HTML Demo: 8080"
    echo ""
    
    # 1. Check PostgreSQL
    print_status "Checking PostgreSQL connection..."
    if source chat/bin/activate && python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='chatbot_django',
        user='django_user',
        password='django_secure_2024'
    )
    conn.close()
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    exit(1)
"; then
        print_status "PostgreSQL is ready"
    else
        print_error "PostgreSQL connection failed"
        exit 1
    fi
    
    # 2. Check Redis
    print_status "Checking Redis connection..."
    if redis-cli ping >/dev/null 2>&1; then
        print_status "Redis is running"
    else
        print_warning "Redis not running, starting Redis..."
        if command -v redis-server >/dev/null 2>&1; then
            redis-server --daemonize yes
            sleep 2
            if redis-cli ping >/dev/null 2>&1; then
                print_status "Redis started successfully"
            else
                print_error "Failed to start Redis"
                exit 1
            fi
        else
            print_error "Redis not installed. Please install Redis first."
            exit 1
        fi
    fi
    
    # 3. Run Django migrations
    print_status "Running Django migrations..."
    source chat/bin/activate && python manage.py migrate --noinput
    
    # 4. Test ChromaDB
    print_status "Testing ChromaDB setup..."
    source chat/bin/activate && python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()
from chatbot.utils.rag_system import RAGSystem
rag = RAGSystem()
print(f'ChromaDB initialized: {rag.is_initialized}')
if rag.chroma_client:
    collections = rag.chroma_client.list_collections()
    print(f'Collections: {len(collections)}')
"
    
    # 5. Start Django API Server
    if ! start_service "Django-API" "bash -c 'source chat/bin/activate && python manage.py runserver 0.0.0.0:8000'" 8000 "../logs/django_api.log"; then
        print_error "Failed to start Django API server"
        exit 1
    fi
    
    # 6. Start Daphne WebSocket Server
    if ! start_service "Daphne-WebSocket" "bash -c 'source chat/bin/activate && daphne -b 0.0.0.0 -p 8001 auth_system.asgi:application'" 8001 "../logs/websocket.log"; then
        print_error "Failed to start Daphne WebSocket server"
        exit 1
    fi
    
    # 7. Start React Development Server (optional)
    cd ../Chat-bot-react-main
    if [ -f "package.json" ]; then
        print_status "Starting React development server..."
        if ! check_port 5173; then
            if command -v npm >/dev/null 2>&1; then
                start_service "React-Dev" "npm run dev" 5173 "../logs/react_dev.log"
            else
                print_warning "npm not found, skipping React dev server"
            fi
        else
            print_warning "React dev server already running on port 5173"
        fi
    fi
    
    # 8. Start HTML Demo Server (optional)
    cd ../
    if ! check_port 8080; then
        start_service "HTML-Demo" "python3 -m http.server 8080" 8080 "logs/html_server.log"
    else
        print_warning "HTML demo server already running on port 8080"
    fi
    
    print_header ""
    print_header "🎉 PRODUCTION SYSTEM STARTED SUCCESSFULLY!"
    print_header "========================================"
    print_status "Services running:"
    print_status "  ✅ PostgreSQL Database (port 5432)"
    print_status "  ✅ Redis Cache (port 6379)"
    print_status "  ✅ Django REST API (port 8000)"
    print_status "  ✅ WebSocket Server (port 8001)"
    print_status "  ✅ ChromaDB Vector Database (local file-based)"
    
    if check_port 5173; then
        print_status "  ✅ React Dev Server (port 5173)"
    fi
    
    if check_port 8080; then
        print_status "  ✅ HTML Demo Server (port 8080)"
    fi
    
    print_header ""
    print_status "🔗 Access URLs:"
    print_status "  📱 React Agent Dashboard: http://localhost:5173"
    print_status "  🌐 HTML Chatbot Demo: http://localhost:8080/New folder/index1.html"
    print_status "  🔧 Django Admin: http://localhost:8000/admin/"
    print_status "  📊 API Documentation: http://localhost:8000/api/"
    
    print_header ""
    print_status "📋 Management Commands:"
    print_status "  Stop all services: ./stop_production.sh"
    print_status "  View logs: tail -f logs/*.log"
    print_status "  Check status: ps aux | grep -E '(django|daphne|react|python)'"
    
    print_header ""
    print_warning "🔍 To test the system:"
    print_warning "  1. Open React dashboard: http://localhost:5173"
    print_warning "  2. Login with your admin credentials"
    print_warning "  3. Test the chatbot functionality"
    print_warning "  4. Try the Growth wings queries we fixed earlier"
    
    print_header ""
    print_status "✅ Production system is ready for use!"
}

# Run main function
main "$@"

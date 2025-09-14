#!/bin/bash

# 🛑 Production Stop Script for Django + ChromaDB + React Chatbot System
# ======================================================================

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

# Function to stop a service by port
stop_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_status "Stopping $service_name on port $port..."
        echo $pids | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            print_warning "Force killing $service_name..."
            echo $remaining_pids | xargs kill -KILL 2>/dev/null || true
        fi
        
        print_status "$service_name stopped"
    else
        print_warning "$service_name not running on port $port"
    fi
}

# Function to stop service by PID file
stop_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill -TERM $pid 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                print_warning "Force killing $service_name..."
                kill -KILL $pid 2>/dev/null || true
            fi
            
            print_status "$service_name stopped"
        else
            print_warning "$service_name not running (stale PID file)"
        fi
        
        rm -f "$pid_file"
    else
        print_warning "No PID file found for $service_name"
    fi
}

# Function to stop processes by name pattern
stop_by_pattern() {
    local pattern=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_status "Stopping $service_name processes..."
        echo $pids | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            print_warning "Force killing $service_name processes..."
            echo $remaining_pids | xargs kill -KILL 2>/dev/null || true
        fi
        
        print_status "$service_name processes stopped"
    else
        print_warning "No $service_name processes found"
    fi
}

# Main stop function
main() {
    print_header "🛑 STOPPING PRODUCTION CHATBOT SYSTEM"
    print_header "====================================="
    
    # Navigate to the correct directory
    if [ ! -f "ChatBot_DRF_Api/manage.py" ]; then
        print_error "Please run this script from the Full-Chatbot-Integration directory"
        exit 1
    fi
    
    cd ChatBot_DRF_Api
    
    print_status "Stopping all services..."
    
    # Stop services by PID files first
    stop_by_pid_file "django-api.pid" "Django API"
    stop_by_pid_file "daphne-websocket.pid" "Daphne WebSocket"
    stop_by_pid_file "react-dev.pid" "React Dev Server"
    stop_by_pid_file "html-demo.pid" "HTML Demo Server"
    
    # Stop services by port
    stop_by_port 8000 "Django API"
    stop_by_port 8001 "Daphne WebSocket"
    stop_by_port 8002 "ChromaDB Server"
    stop_by_port 5173 "React Dev Server"
    stop_by_port 8080 "HTML Demo Server"
    
    # Stop services by process pattern
    stop_by_pattern "manage.py runserver" "Django runserver"
    stop_by_pattern "daphne.*auth_system.asgi" "Daphne ASGI"
    stop_by_pattern "npm run dev" "React Dev"
    stop_by_pattern "python.*chromadb_server.py" "ChromaDB Server"
    stop_by_pattern "python.*-m http.server 8080" "HTTP Demo Server"
    
    # Clean up any remaining Python processes related to our project
    cd ..
    local project_path=$(pwd)
    stop_by_pattern "$project_path.*python" "Project Python processes"
    
    # Clean up PID files
    rm -f ChatBot_DRF_Api/*.pid
    
    print_header ""
    print_header "✅ ALL SERVICES STOPPED"
    print_header "======================="
    
    print_status "Stopped services:"
    print_status "  🛑 Django REST API (port 8000)"
    print_status "  🛑 WebSocket Server (port 8001)"
    print_status "  🛑 ChromaDB Server (port 8002)"
    print_status "  🛑 React Dev Server (port 5173)"
    print_status "  🛑 HTML Demo Server (port 8080)"
    
    print_header ""
    print_status "📋 Services still running:"
    print_status "  ✅ PostgreSQL Database (port 5432) - kept running"
    print_status "  ✅ Redis Cache (port 6379) - kept running"
    
    print_header ""
    print_warning "💡 Note: PostgreSQL and Redis are kept running as they may be used by other applications."
    print_warning "    To stop them manually:"
    print_warning "    - Redis: redis-cli shutdown"
    print_warning "    - PostgreSQL: brew services stop postgresql@14 (macOS)"
    
    print_header ""
    print_status "🔄 To restart the system: ./start_production.sh"
    print_status "📊 To check remaining processes: ps aux | grep -E '(django|daphne|react|python)'"
    
    print_header ""
    print_status "✅ Production system shutdown complete!"
}

# Run main function
main "$@"

#!/bin/bash

# Full Chatbot Integration - Start All Services with Redis
# This script starts all required services for the chatbot system

set -e  # Exit on any error

echo "🚀 Starting Full Chatbot Integration with Redis..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    print_status "Starting Redis server..."
    brew services start redis
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis started successfully"
    else
        print_error "Failed to start Redis"
        exit 1
    fi
else
    print_success "Redis is already running"
fi

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    # Kill background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    print_success "Cleanup completed"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Start Django API server
print_status "Starting Django API server on port 8001..."
cd ChatBot_DRF_Api
source chat/bin/activate
python manage.py runserver 8001 &
DJANGO_PID=$!
cd ..

# Wait a moment for Django to start
sleep 3

# Start Daphne WebSocket server
print_status "Starting Daphne WebSocket server on port 8000..."
cd ChatBot_DRF_Api
source chat/bin/activate
daphne -p 8000 auth_system.asgi:application &
DAPHNE_PID=$!
cd ..

# Wait a moment for Daphne to start
sleep 3

# Start React development server
print_status "Starting React development server on port 3000..."
cd Chat-bot-react-main
npm start &
REACT_PID=$!
cd ..

# Wait a moment for React to start
sleep 5

print_success "🎉 All services started successfully!"
echo ""
echo "📋 Services Running:"
echo "   ✅ Redis Server: localhost:6379"
echo "   ✅ Django API: http://localhost:8001"
echo "   ✅ WebSocket Server: ws://localhost:8000"
echo "   ✅ React Dashboard: http://localhost:3000"
echo ""
echo "🌐 Access Points:"
echo "   📱 Chatbot Widget: file://$(pwd)/New folder/chatbot-iframe.html"
echo "   👨‍💼 Agent Dashboard: http://localhost:3000"
echo "   🔧 Django Admin: http://localhost:8001/admin/"
echo ""
echo "🧪 Test Your File Sharing:"
echo "   1. Open the chatbot widget in your browser"
echo "   2. Upload a file from the chatbot"
echo "   3. Open the agent dashboard"
echo "   4. Upload a file from the agent side"
echo "   5. Both should now work perfectly with Redis!"
echo ""
echo "📊 Redis Status:"
redis-cli info server | grep redis_version || echo "   Redis info not available"
echo ""
echo "🔍 Debug Tips:"
echo "   - Check Redis: redis-cli ping"
echo "   - Monitor Redis: redis-cli monitor"
echo "   - View logs in each terminal window"
echo ""
print_warning "Press Ctrl+C to stop all services"

# Wait for user to stop the services
wait

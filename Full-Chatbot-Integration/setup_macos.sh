#!/bin/bash

# Full Chatbot Integration - macOS Setup Script
# This script sets up the complete development environment on macOS

set -e  # Exit on any error

echo "🚀 Setting up Full Chatbot Integration on macOS..."

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

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    print_success "Homebrew installed successfully"
else
    print_success "Homebrew already installed"
fi

# Update Homebrew
print_status "Updating Homebrew..."
brew update

# Install Python if not already installed
if ! command -v python3 &> /dev/null; then
    print_status "Installing Python..."
    brew install python
    print_success "Python installed successfully"
else
    print_success "Python already installed: $(python3 --version)"
fi

# Install Node.js if not already installed
if ! command -v node &> /dev/null; then
    print_status "Installing Node.js..."
    brew install node
    print_success "Node.js installed successfully"
else
    print_success "Node.js already installed: $(node --version)"
fi

# Install Redis if not already installed
if ! command -v redis-server &> /dev/null; then
    print_status "Installing Redis..."
    brew install redis
    print_success "Redis installed successfully"
else
    print_success "Redis already installed"
fi

# Setup Python virtual environment
print_status "Setting up Python virtual environment..."
cd ChatBot_DRF_Api
python3 -m venv chat
source chat/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Run Django migrations
print_status "Running Django migrations..."
python manage.py migrate
print_success "Database migrations completed"

# Go back to root directory
cd ..

# Setup Node.js dependencies
print_status "Setting up React frontend..."
cd Chat-bot-react-main
npm install
print_success "Node.js dependencies installed"

# Go back to root directory
cd ..

# Start Redis service
print_status "Starting Redis service..."
brew services start redis

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is running and accessible"
else
    print_warning "Redis might not be running properly"
fi

print_success "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start the development servers:"
echo "   Terminal 1: redis-server"
echo "   Terminal 2: cd ChatBot_DRF_Api && source chat/bin/activate && python manage.py runserver 8001"
echo "   Terminal 3: cd ChatBot_DRF_Api && source chat/bin/activate && python -m daphne auth_system.asgi:application --port 8000"
echo "   Terminal 4: cd Chat-bot-react-main && npm start"
echo ""
echo "2. Access the application:"
echo "   - Chatbot Widget: file://$(pwd)/New folder/chatbot-iframe.html"
echo "   - Agent Dashboard: http://localhost:3000"
echo "   - Django Admin: http://localhost:8001/admin/"
echo ""
echo "3. Create a Django superuser (optional):"
echo "   cd ChatBot_DRF_Api && source chat/bin/activate && python manage.py createsuperuser"
echo ""
print_success "Happy coding! 🚀"

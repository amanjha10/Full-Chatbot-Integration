#!/bin/bash

# 🗄️ ChromaDB Production Server Startup Script
# ============================================
# 
# This script starts ChromaDB as a standalone server for production use.
# It provides better stability and performance than embedded ChromaDB.

set -e  # Exit on any error

# Configuration
CHROMADB_HOST="localhost"
CHROMADB_PORT="8002"
CHROMADB_DATA_DIR="$(pwd)/ChatBot_DRF_Api/chroma_data"
CHROMADB_LOG_DIR="$(pwd)/logs"
CHROMADB_PID_FILE="$(pwd)/chromadb_server.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗄️ ChromaDB Production Server Startup${NC}"
echo "========================================"

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p "$CHROMADB_DATA_DIR"
mkdir -p "$CHROMADB_LOG_DIR"

# Check if ChromaDB is already running
if [ -f "$CHROMADB_PID_FILE" ]; then
    PID=$(cat "$CHROMADB_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ ChromaDB server is already running (PID: $PID)${NC}"
        echo "   Server should be available at: http://$CHROMADB_HOST:$CHROMADB_PORT"
        exit 0
    else
        echo -e "${YELLOW}🧹 Removing stale PID file...${NC}"
        rm -f "$CHROMADB_PID_FILE"
    fi
fi

# Check if port is already in use
if lsof -Pi :$CHROMADB_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $CHROMADB_PORT is already in use${NC}"
    echo "   Please stop the service using that port or change CHROMADB_PORT"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}🐍 Activating virtual environment...${NC}"
if [ -d "ChatBot_DRF_Api/chat/bin" ]; then
    source ChatBot_DRF_Api/chat/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ Virtual environment not found at ChatBot_DRF_Api/chat/bin${NC}"
    echo "   Please ensure the virtual environment exists"
    exit 1
fi

# Check if ChromaDB is installed
echo -e "${YELLOW}📦 Checking ChromaDB installation...${NC}"
if ! python -c "import chromadb" 2>/dev/null; then
    echo -e "${RED}❌ ChromaDB not installed${NC}"
    echo "   Installing ChromaDB..."
    pip install chromadb
fi

# Start ChromaDB server
echo -e "${YELLOW}🚀 Starting ChromaDB server...${NC}"
echo "   Host: $CHROMADB_HOST"
echo "   Port: $CHROMADB_PORT"
echo "   Data Directory: $CHROMADB_DATA_DIR"
echo "   Log Directory: $CHROMADB_LOG_DIR"

# Start ChromaDB server in background
nohup python -m chromadb.cli.cli run \
    --host "$CHROMADB_HOST" \
    --port "$CHROMADB_PORT" \
    --path "$CHROMADB_DATA_DIR" \
    --log-config-path /dev/null \
    > "$CHROMADB_LOG_DIR/chromadb_server.log" 2>&1 &

# Save PID
CHROMADB_PID=$!
echo $CHROMADB_PID > "$CHROMADB_PID_FILE"

# Wait a moment for server to start
echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"
sleep 3

# Check if server is running
if ps -p $CHROMADB_PID > /dev/null 2>&1; then
    # Test server connectivity
    echo -e "${YELLOW}🔍 Testing server connectivity...${NC}"
    
    # Try to connect to the server
    if python -c "
import chromadb
import sys
try:
    client = chromadb.HttpClient(host='$CHROMADB_HOST', port=$CHROMADB_PORT)
    client.heartbeat()
    print('✅ ChromaDB server is responding')
    sys.exit(0)
except Exception as e:
    print(f'❌ Server not responding: {e}')
    sys.exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}🎉 ChromaDB server started successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Server Information:${NC}"
        echo "   • URL: http://$CHROMADB_HOST:$CHROMADB_PORT"
        echo "   • PID: $CHROMADB_PID"
        echo "   • Data Directory: $CHROMADB_DATA_DIR"
        echo "   • Log File: $CHROMADB_LOG_DIR/chromadb_server.log"
        echo "   • PID File: $CHROMADB_PID_FILE"
        echo ""
        echo -e "${GREEN}✅ Your Django application will now use the ChromaDB server${NC}"
        echo -e "${YELLOW}💡 To stop the server, run: ./stop_chromadb_server.sh${NC}"
    else
        echo -e "${RED}❌ Server started but not responding${NC}"
        echo "   Check logs: $CHROMADB_LOG_DIR/chromadb_server.log"
        exit 1
    fi
else
    echo -e "${RED}❌ Failed to start ChromaDB server${NC}"
    echo "   Check logs: $CHROMADB_LOG_DIR/chromadb_server.log"
    rm -f "$CHROMADB_PID_FILE"
    exit 1
fi

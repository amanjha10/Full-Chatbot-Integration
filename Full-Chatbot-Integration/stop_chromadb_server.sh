#!/bin/bash

# 🛑 ChromaDB Production Server Shutdown Script
# =============================================

set -e  # Exit on any error

# Configuration
CHROMADB_PID_FILE="$(pwd)/chromadb_server.pid"
CHROMADB_LOG_DIR="$(pwd)/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 ChromaDB Production Server Shutdown${NC}"
echo "========================================"

# Check if PID file exists
if [ ! -f "$CHROMADB_PID_FILE" ]; then
    echo -e "${YELLOW}⚠️ ChromaDB PID file not found${NC}"
    echo "   Server may not be running or was started manually"
    
    # Try to find ChromaDB processes
    CHROMADB_PIDS=$(pgrep -f "chromadb.cli.cli run" 2>/dev/null || true)
    if [ -n "$CHROMADB_PIDS" ]; then
        echo -e "${YELLOW}🔍 Found ChromaDB processes: $CHROMADB_PIDS${NC}"
        echo -e "${YELLOW}💀 Killing ChromaDB processes...${NC}"
        echo $CHROMADB_PIDS | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo $CHROMADB_PIDS | xargs kill -KILL 2>/dev/null || true
        echo -e "${GREEN}✅ ChromaDB processes terminated${NC}"
    else
        echo -e "${GREEN}✅ No ChromaDB processes found${NC}"
    fi
    exit 0
fi

# Read PID from file
PID=$(cat "$CHROMADB_PID_FILE")
echo -e "${YELLOW}📋 Found ChromaDB PID: $PID${NC}"

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}💀 Stopping ChromaDB server (PID: $PID)...${NC}"
    
    # Try graceful shutdown first
    kill -TERM $PID 2>/dev/null || true
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ChromaDB server stopped gracefully${NC}"
            break
        fi
        echo -e "${YELLOW}⏳ Waiting for graceful shutdown... ($i/10)${NC}"
        sleep 1
    done
    
    # Force kill if still running
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🔨 Force killing ChromaDB server...${NC}"
        kill -KILL $PID 2>/dev/null || true
        sleep 1
        
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${RED}❌ Failed to stop ChromaDB server${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ ChromaDB server force stopped${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️ ChromaDB server (PID: $PID) is not running${NC}"
fi

# Clean up PID file
echo -e "${YELLOW}🧹 Cleaning up PID file...${NC}"
rm -f "$CHROMADB_PID_FILE"

# Show final status
echo -e "${GREEN}🎉 ChromaDB server shutdown complete!${NC}"
echo ""
echo -e "${BLUE}📋 Cleanup Summary:${NC}"
echo "   • Server process stopped"
echo "   • PID file removed"
echo "   • Data directory preserved: $(pwd)/ChatBot_DRF_Api/chroma_data"
if [ -f "$CHROMADB_LOG_DIR/chromadb_server.log" ]; then
    echo "   • Log file preserved: $CHROMADB_LOG_DIR/chromadb_server.log"
fi
echo ""
echo -e "${YELLOW}💡 To start the server again, run: ./start_chromadb_server.sh${NC}"

#!/bin/bash

# 🐘 PostgreSQL Setup Script for Production Migration
# ===================================================

echo "🚀 Setting up PostgreSQL for Django + ChromaDB..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    
    # macOS installation
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install postgresql
            brew services start postgresql
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    # Ubuntu/Debian installation
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    else
        echo "❌ Unsupported OS. Please install PostgreSQL manually."
        exit 1
    fi
else
    echo "✅ PostgreSQL already installed"
fi

# Create databases and users
echo "🔧 Creating databases and users..."

# Create Django database
sudo -u postgres psql -c "CREATE DATABASE chatbot_django;" 2>/dev/null || echo "⚠️ Django database already exists"
sudo -u postgres psql -c "CREATE USER django_user WITH PASSWORD 'django_secure_2024';" 2>/dev/null || echo "⚠️ Django user already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_django TO django_user;" 2>/dev/null
sudo -u postgres psql -c "ALTER USER django_user CREATEDB;" 2>/dev/null

# Create ChromaDB database
sudo -u postgres psql -c "CREATE DATABASE chatbot_chromadb;" 2>/dev/null || echo "⚠️ ChromaDB database already exists"
sudo -u postgres psql -c "CREATE USER chroma_user WITH PASSWORD 'chroma_secure_2024';" 2>/dev/null || echo "⚠️ ChromaDB user already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chatbot_chromadb TO chroma_user;" 2>/dev/null

echo "✅ PostgreSQL setup completed!"
echo ""
echo "📊 Database Configuration:"
echo "   Django DB: chatbot_django (user: django_user)"
echo "   ChromaDB: chatbot_chromadb (user: chroma_user)"
echo "   Port: 5432"
echo ""
echo "🔐 Credentials:"
echo "   Django: django_user / django_secure_2024"
echo "   ChromaDB: chroma_user / chroma_secure_2024"

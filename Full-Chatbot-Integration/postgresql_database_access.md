# 🐘 PostgreSQL Database Access Guide

## 📋 Database Connection Details

Your PostgreSQL databases are now set up with the following credentials:

### **Django Database**
- **Database Name**: `chatbot_django`
- **Username**: `django_user`
- **Password**: `django_secure_2024`
- **Host**: `localhost`
- **Port**: `5432`

### **ChromaDB Database** (Future Use)
- **Database Name**: `chatbot_chromadb`
- **Username**: `chroma_user`
- **Password**: `chroma_secure_2024`
- **Host**: `localhost`
- **Port**: `5432`

---

## 🖥️ Command Line Access

### **1. Using psql (PostgreSQL Command Line)**

```bash
# Connect to Django database
psql -h localhost -p 5432 -U django_user -d chatbot_django

# Connect to ChromaDB database
psql -h localhost -p 5432 -U chroma_user -d chatbot_chromadb

# Connect as postgres superuser (if needed)
psql postgres
```

### **2. Common psql Commands**

```sql
-- List all databases
\l

-- List all tables in current database
\dt

-- Describe a specific table
\d table_name

-- Show table data
SELECT * FROM table_name LIMIT 10;

-- Show Django migrations
SELECT * FROM django_migrations;

-- Show all users
SELECT * FROM auth_user;

-- Show companies
SELECT * FROM admin_dashboard_company;

-- Exit psql
\q
```

---

## 🖱️ GUI Database Viewers

### **1. pgAdmin (Recommended - Free)**

**Installation:**
```bash
# macOS (using Homebrew)
brew install --cask pgadmin4

# Or download from: https://www.pgadmin.org/download/
```

**Connection Setup:**
1. Open pgAdmin
2. Right-click "Servers" → "Create" → "Server"
3. **General Tab:**
   - Name: `Chatbot Django DB`
4. **Connection Tab:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `chatbot_django`
   - Username: `django_user`
   - Password: `django_secure_2024`

### **2. DBeaver (Free & Cross-Platform)**

**Installation:**
```bash
# macOS (using Homebrew)
brew install --cask dbeaver-community

# Or download from: https://dbeaver.io/download/
```

**Connection Setup:**
1. Open DBeaver
2. Click "New Database Connection"
3. Select "PostgreSQL"
4. **Main Tab:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `chatbot_django`
   - Username: `django_user`
   - Password: `django_secure_2024`

### **3. TablePlus (Paid - macOS/Windows)**

**Installation:**
- Download from: https://tableplus.com/

**Connection Setup:**
1. Click "Create a new connection"
2. Select "PostgreSQL"
3. Fill in the connection details above

### **4. Postico (macOS Only - Paid)**

**Installation:**
- Download from: https://eggerapps.at/postico/

---

## 🌐 Web-Based Database Viewers

### **1. Adminer (Lightweight)**

**Setup:**
```bash
# Download Adminer
curl -L https://www.adminer.org/latest.php -o adminer.php

# Start PHP server (if you have PHP installed)
php -S localhost:8080 adminer.php
```

**Access:**
- URL: `http://localhost:8080`
- System: `PostgreSQL`
- Server: `localhost:5432`
- Username: `django_user`
- Password: `django_secure_2024`
- Database: `chatbot_django`

### **2. phpPgAdmin (If you prefer web interface)**

**Installation (macOS):**
```bash
brew install phppgadmin
```

---

## 📊 Key Tables to Explore

### **Django Core Tables**
- `auth_user` - User accounts
- `django_migrations` - Migration history
- `django_session` - User sessions

### **Admin Dashboard Tables**
- `admin_dashboard_company` - Company information
- `admin_dashboard_agent` - Agent accounts
- `admin_dashboard_companyplan` - Company subscription plans

### **Chatbot Tables**
- `chatbot_conversation` - Chat conversations
- `chatbot_message` - Individual messages
- `chatbot_chatfile` - File attachments
- `chatbot_uploadedfile` - Uploaded files

### **FAQ Tables**
- `chatbot_faq` - General FAQs
- `chatbot_companyfaq` - Company-specific FAQs

---

## 🔍 Useful Queries

### **Check Database Status**
```sql
-- Show all tables and their row counts
SELECT 
    schemaname,
    tablename,
    n_tup_ins as "Total Inserts",
    n_tup_upd as "Total Updates",
    n_tup_del as "Total Deletes"
FROM pg_stat_user_tables
ORDER BY tablename;
```

### **Check Recent Activity**
```sql
-- Recent conversations
SELECT c.id, c.company_id, c.created_at, COUNT(m.id) as message_count
FROM chatbot_conversation c
LEFT JOIN chatbot_message m ON c.id = m.conversation_id
GROUP BY c.id, c.company_id, c.created_at
ORDER BY c.created_at DESC
LIMIT 10;
```

### **Check Companies and Users**
```sql
-- Companies with user counts
SELECT 
    c.name as company_name,
    c.company_id,
    COUNT(u.id) as user_count
FROM admin_dashboard_company c
LEFT JOIN auth_user u ON c.company_id = u.company_id
GROUP BY c.id, c.name, c.company_id
ORDER BY user_count DESC;
```

---

## 🚀 Quick Start

**For immediate access, use psql:**

```bash
# Navigate to your project directory
cd /Users/amanjha/Documents/Consultancy_ChatBot/Full-Chatbot-Integration

# Connect to your Django database
psql -h localhost -p 5432 -U django_user -d chatbot_django

# Once connected, explore your tables
\dt
```

**Password when prompted:** `django_secure_2024`

---

## 🔒 Security Notes

- These credentials are for development/local use
- For production, use environment variables
- Consider rotating passwords regularly
- Limit database access to necessary users only

---

## 📞 Troubleshooting

### **Connection Refused**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if not running
brew services start postgresql
```

### **Authentication Failed**
```bash
# Reset user password
psql postgres -c "ALTER USER django_user PASSWORD 'django_secure_2024';"
```

### **Database Not Found**
```bash
# List all databases
psql postgres -c "\l"

# Recreate database if needed
psql postgres -c "CREATE DATABASE chatbot_django OWNER django_user;"
```

#!/bin/bash

# File Sharing System Test Script
# ================================
# Tests the complete file sharing functionality between users and agents

echo "🚀 File Sharing System Test Suite"
echo "=================================="

BASE_URL="http://127.0.0.1:8001"
AGENT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2NzIzMzM2LCJpYXQiOjE3NTY2MzY5MzYsImp0aSI6IjE1MmY0YjJlMjg4MTQ5OTBiOWQxNTE0Nzk3OTJlMDY0IiwidXNlcl9pZCI6NDZ9.YOiPGkph4uQ_Mwm7l6WfamifzwwyJ18b6cRVokzN_W0"
COMPANY_ID="TEST001"
SESSION_ID="test-file-session-$(date +%s)"

# Create test files
echo "📁 Creating test files..."
echo "This is a test document for file sharing." > test_document.txt
echo "PDF content simulation" > test_document.pdf
echo "Test data file" > test_data.csv

echo "✅ Test files created"
echo ""

# Test 1: User file upload
echo "🧪 Test 1: User File Upload"
echo "------------------------"
USER_UPLOAD_RESULT=$(curl -s -X POST "$BASE_URL/api/chatbot/upload/" \
  -F "file=@test_document.txt" \
  -F "session_id=$SESSION_ID" \
  -F "company_id=$COMPANY_ID")

echo "User upload result: $USER_UPLOAD_RESULT"

if echo "$USER_UPLOAD_RESULT" | grep -q "file_id"; then
    echo "✅ User file upload: PASS"
    USER_FILE_ID=$(echo "$USER_UPLOAD_RESULT" | grep -o '"file_id":[0-9]*' | cut -d':' -f2)
    echo "   └─ File ID: $USER_FILE_ID"
else
    echo "❌ User file upload: FAIL"
fi
echo ""

# Test 2: Agent file upload
echo "🧪 Test 2: Agent File Upload"
echo "-------------------------"
AGENT_UPLOAD_RESULT=$(curl -s -X POST "$BASE_URL/api/human-handoff/agent/upload/" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -F "file=@test_document.pdf" \
  -F "session_id=$SESSION_ID")

echo "Agent upload result: $AGENT_UPLOAD_RESULT"

if echo "$AGENT_UPLOAD_RESULT" | grep -q "file_id"; then
    echo "✅ Agent file upload: PASS"
    AGENT_FILE_ID=$(echo "$AGENT_UPLOAD_RESULT" | grep -o '"file_id":[0-9]*' | cut -d':' -f2)
    echo "   └─ File ID: $AGENT_FILE_ID"
else
    echo "❌ Agent file upload: FAIL"
fi
echo ""

# Test 3: User message with attachment
echo "🧪 Test 3: User Message with File Attachment"
echo "----------------------------------------"
USER_MESSAGE_RESULT=$(curl -s -X POST "$BASE_URL/api/chatbot/chat/" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Here is my document\",
    \"session_id\": \"$SESSION_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"attachment_ids\": [$USER_FILE_ID]
  }")

echo "User message result: $USER_MESSAGE_RESULT"

if echo "$USER_MESSAGE_RESULT" | grep -q "session_id"; then
    echo "✅ User message with attachment: PASS"
else
    echo "❌ User message with attachment: FAIL"
fi
echo ""

# Test 4: Agent message with attachment
echo "🧪 Test 4: Agent Message with File Attachment"
echo "-----------------------------------------"
AGENT_MESSAGE_RESULT=$(curl -s -X POST "$BASE_URL/api/human-handoff/agent/send-message/" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Agent sending PDF file\",
    \"attachment_ids\": [$AGENT_FILE_ID]
  }")

echo "Agent message result: $AGENT_MESSAGE_RESULT"

if echo "$AGENT_MESSAGE_RESULT" | grep -q "Message sent successfully"; then
    echo "✅ Agent message with attachment: PASS"
else
    echo "❌ Agent message with attachment: FAIL"
fi
echo ""

# Test 5: File type validation (invalid file)
echo "🧪 Test 5: File Type Validation"
echo "-----------------------------"
echo "malicious content" > test_malicious.exe

INVALID_UPLOAD_RESULT=$(curl -s -X POST "$BASE_URL/api/chatbot/upload/" \
  -F "file=@test_malicious.exe" \
  -F "session_id=$SESSION_ID" \
  -F "company_id=$COMPANY_ID")

echo "Invalid file upload result: $INVALID_UPLOAD_RESULT"

if echo "$INVALID_UPLOAD_RESULT" | grep -q "error\|not allowed"; then
    echo "✅ File type validation: PASS (correctly rejected)"
else
    echo "❌ File type validation: FAIL (should reject .exe files)"
fi
echo ""

# Test 6: Chat history with files
echo "🧪 Test 6: Chat History with Files"
echo "--------------------------------"
HISTORY_RESULT=$(curl -s -X GET "$BASE_URL/api/human-handoff/agent/sessions/$SESSION_ID/messages/" \
  -H "Authorization: Bearer $AGENT_TOKEN")

echo "Chat history result: $HISTORY_RESULT"

if echo "$HISTORY_RESULT" | grep -q "attachments"; then
    echo "✅ Chat history with files: PASS"
else
    echo "❌ Chat history with files: FAIL"
fi
echo ""

# Cleanup
echo "🧹 Cleaning up test files..."
rm -f test_document.txt test_document.pdf test_data.csv test_malicious.exe

echo ""
echo "📊 TEST SUITE COMPLETED"
echo "======================"
echo "Check the results above for detailed information."
echo "All core file sharing features have been tested."

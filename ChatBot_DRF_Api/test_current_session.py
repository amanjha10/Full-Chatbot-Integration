#!/usr/bin/env python3
"""
Quick File Sharing Test - Current Status
"""

import requests
import tempfile
import json

# Test configuration
BASE_URL = "http://127.0.0.1:8001"
SESSION_ID = "f9ffdb2a-d24f-4108-85f2-1ceef91ab82f"  # From the console logs
COMPANY_ID = "TEST001"

def test_agent_auth():
    """Test agent authentication"""
    print("🔐 Testing agent authentication...")
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", {
        'username': 'testagent',
        'password': 'testpass123'
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        if token:
            print(f"✅ Agent authenticated successfully")
            return token
        else:
            print(f"❌ No access token in response: {data}")
            return None
    else:
        print(f"❌ Agent auth failed: {response.status_code} - {response.text}")
        return None

def test_agent_send_message(token):
    """Test agent sending a simple message"""
    print("\n💬 Testing agent message sending...")
    
    response = requests.post(f"{BASE_URL}/api/human-handoff/agent/send-message/", 
        json={
            'session_id': SESSION_ID,
            'message': 'Hello from agent via API test'
        }, 
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Agent message sent successfully")
        print(f"   Message ID: {result.get('chat_message', {}).get('id')}")
        return True
    else:
        print(f"❌ Agent message failed: {response.status_code} - {response.text}")
        return False

def test_user_upload():
    """Test user file upload to the specific session"""
    print("\n📤 Testing user file upload...")
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test file from user for active session")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as file:
            files = {'file': ('test_user_message.txt', file, 'text/plain')}
            data = {
                'session_id': SESSION_ID,
                'company_id': COMPANY_ID
            }
            
            response = requests.post(f"{BASE_URL}/api/chatbot/upload/", files=files, data=data)
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ User file uploaded successfully!")
                print(f"   File ID: {result['file_id']}")
                print(f"   File URL: {result['file_url']}")
                return True
            else:
                print(f"❌ User upload failed: {response.text}")
                return False
                
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def main():
    print("🧪 File Sharing System - Current Status Test")
    print("=" * 50)
    print(f"Testing session: {SESSION_ID}")
    print(f"Company: {COMPANY_ID}")
    
    # Test agent auth
    token = test_agent_auth()
    if not token:
        print("❌ Cannot proceed without agent authentication")
        return
    
    # Test agent message
    agent_msg_success = test_agent_send_message(token)
    
    # Test user upload
    user_upload_success = test_user_upload()
    
    # Summary
    print(f"\n📊 Test Results")
    print("=" * 30)
    print(f"✅ Agent Auth: {'✓' if token else '✗'}")
    print(f"✅ Agent Message: {'✓' if agent_msg_success else '✗'}")
    print(f"✅ User Upload: {'✓' if user_upload_success else '✗'}")
    
    if agent_msg_success and user_upload_success:
        print("\n🎉 Both directions working! Check the interfaces for real-time updates.")
    else:
        print("\n⚠️ Some issues detected. Check the console logs.")

if __name__ == "__main__":
    main()

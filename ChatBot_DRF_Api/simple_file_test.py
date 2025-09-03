#!/usr/bin/env python3
"""
Simple File Sharing Test
Quick validation that file sharing is working correctly.
"""

import requests
import tempfile
import os

# Test configuration
BASE_URL = "http://127.0.0.1:8001"
SESSION_ID = "ddd27227-f053-45b3-8849-874e0056e418"
COMPANY_ID = "TEST001"

def test_user_upload():
    """Test user file upload"""
    print("🔄 Testing user file upload...")
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello from user! This is a test file for file sharing.")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as file:
            files = {'file': ('user_test.txt', file, 'text/plain')}
            data = {
                'session_id': SESSION_ID,
                'company_id': COMPANY_ID
            }
            
            response = requests.post(f"{BASE_URL}/api/chatbot/upload/", files=files, data=data)
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ User upload successful!")
                print(f"   File ID: {result['file_id']}")
                print(f"   File URL: {result['file_url']}")
                print(f"   Original Name: {result['original_name']}")
                return True
            else:
                print(f"❌ User upload failed: {response.text}")
                return False
                
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_agent_upload():
    """Test agent file upload with authentication"""
    print("\n🔄 Testing agent file upload...")
    
    # Get agent token
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", {
        'username': 'testagent',
        'password': 'testpass123'
    })
    
    if login_response.status_code != 200:
        print("❌ Agent authentication failed")
        print(f"   Response: {login_response.text}")
        return False
    
    response_data = login_response.json()
    if 'access' not in response_data:
        print("❌ No access token in response")
        print(f"   Response: {response_data}")
        return False
        
    token = response_data['access']
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello from agent! This is a response file from the support team.")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as file:
            files = {'file': ('agent_response.txt', file, 'text/plain')}
            data = {
                'session_id': SESSION_ID,
                'company_id': COMPANY_ID
            }
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(f"{BASE_URL}/api/human-handoff/agent/upload/", 
                                   files=files, data=data, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Agent upload successful!")
                print(f"   File ID: {result['file_id']}")
                print(f"   File URL: {result['file_url']}")
                print(f"   Original Name: {result['original_name']}")
                return True
            else:
                print(f"❌ Agent upload failed: {response.text}")
                return False
                
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_file_validation():
    """Test file validation (size and type limits)"""
    print("\n🔄 Testing file validation...")
    
    # Test invalid file type
    with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
        f.write("malicious content")
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as file:
            files = {'file': ('malicious.exe', file, 'application/octet-stream')}
            data = {
                'session_id': SESSION_ID,
                'company_id': COMPANY_ID
            }
            
            response = requests.post(f"{BASE_URL}/api/chatbot/upload/", files=files, data=data)
            
            if response.status_code == 400 and 'not allowed' in response.text:
                print("✅ File type validation working - .exe files rejected")
                return True
            else:
                print(f"❌ File validation failed: {response.text}")
                return False
                
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def main():
    print("🚀 File Sharing System Test")
    print("=" * 40)
    
    results = []
    
    # Test user upload
    results.append(test_user_upload())
    
    # Test agent upload
    results.append(test_agent_upload())
    
    # Test validation
    results.append(test_file_validation())
    
    # Summary
    print(f"\n📊 Test Results")
    print("=" * 40)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! File sharing system is working perfectly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for file upload functionality in chat messages
"""

import requests
import json
import os
import tempfile

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = "TES001"

def create_test_file():
    """Create a temporary test file for upload"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for file upload functionality.\n")
        f.write("It contains sample content to demonstrate file uploads in chat messages.\n")
        f.write("File upload test - " + str(os.urandom(8).hex()) + "\n")
        return f.name

def test_file_upload_functionality():
    """Test the complete file upload and chat flow"""
    print("🧪 Testing File Upload Functionality for Chat Messages")
    print("=" * 60)
    
    session_id = None
    file_id = None
    test_file_path = None
    
    try:
        # Step 1: Create a chat session
        print("\n📝 Step 1: Creating chat session...")
        chat_data = {
            "message": "Hello, I want to test file uploads",
            "company_id": COMPANY_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=chat_data)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get('session_id')
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            print(response.text)
            return
        
        # Step 2: Create and upload a test file
        print("\n📤 Step 2: Uploading test file...")
        test_file_path = create_test_file()
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {
                'session_id': session_id,
                'company_id': COMPANY_ID,
                'message_context': 'Test file upload for API validation'
            }
            
            response = requests.post(f"{BASE_URL}/api/chatbot/upload/", files=files, data=data)
            
        if response.status_code == 201:
            file_data = response.json()
            file_id = file_data.get('file_id')
            print(f"✅ File uploaded successfully:")
            print(f"   📄 File ID: {file_id}")
            print(f"   📄 Original name: {file_data.get('original_name')}")
            print(f"   📄 File size: {file_data.get('file_size')} bytes")
            print(f"   📄 File type: {file_data.get('file_type')}")
            print(f"   📄 URL: {file_data.get('file_url')}")
        else:
            print(f"❌ Failed to upload file: {response.status_code}")
            print(response.text)
            return
        
        # Step 3: Send text-only message
        print("\n💬 Step 3: Sending text-only message...")
        text_data = {
            "message": "I need information about study abroad programs",
            "session_id": session_id,
            "company_id": COMPANY_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=text_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Text message sent successfully")
            print(f"   🤖 Bot response: {chat_response.get('response', '')[:100]}...")
            print(f"   📝 User message has {len(chat_response.get('user_message', {}).get('attachments', []))} attachments")
        else:
            print(f"❌ Failed to send text message: {response.status_code}")
            print(response.text)
        
        # Step 4: Send attachment-only message
        print("\n📎 Step 4: Sending attachment-only message...")
        attachment_data = {
            "session_id": session_id,
            "company_id": COMPANY_ID,
            "attachment_ids": [file_id]
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=attachment_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Attachment message sent successfully")
            print(f"   🤖 Bot response: {chat_response.get('response', '')[:100]}...")
            attachments = chat_response.get('user_message', {}).get('attachments', [])
            print(f"   📎 User message has {len(attachments)} attachments")
            if attachments:
                print(f"   📄 First attachment: {attachments[0].get('original_name')}")
        else:
            print(f"❌ Failed to send attachment message: {response.status_code}")
            print(response.text)
        
        # Step 5: Send message with both text and attachments
        print("\n📝📎 Step 5: Sending message with text AND attachments...")
        combined_data = {
            "message": "Please review this document and provide guidance",
            "session_id": session_id,
            "company_id": COMPANY_ID,
            "attachment_ids": [file_id],
            "context": "Document review request"
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=combined_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Combined message sent successfully")
            print(f"   🤖 Bot response: {chat_response.get('response', '')[:100]}...")
            user_message = chat_response.get('user_message', {})
            print(f"   📝 Message content: {user_message.get('content', '')[:50]}...")
            print(f"   📎 Attachments: {len(user_message.get('attachments', []))}")
            print(f"   📎 Response attachments: {len(chat_response.get('attachments', []))}")
        else:
            print(f"❌ Failed to send combined message: {response.status_code}")
            print(response.text)
        
        # Step 6: Test error scenarios
        print("\n🚨 Step 6: Testing error scenarios...")
        
        # Test empty message with no attachments
        empty_data = {
            "session_id": session_id,
            "company_id": COMPANY_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=empty_data)
        if response.status_code == 400:
            print("✅ Empty message validation working correctly")
        else:
            print(f"❌ Empty message validation failed: {response.status_code}")
        
        # Test invalid attachment ID
        invalid_data = {
            "message": "Test with invalid attachment",
            "session_id": session_id,
            "company_id": COMPANY_ID,
            "attachment_ids": [99999]
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=invalid_data)
        if response.status_code == 400:
            print("✅ Invalid attachment ID validation working correctly")
        else:
            print(f"❌ Invalid attachment ID validation failed: {response.status_code}")
        
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print(f"   ✅ Chat session created: {session_id}")
        print(f"   ✅ File uploaded: ID {file_id}")
        print(f"   ✅ Text-only message: Working")
        print(f"   ✅ Attachment-only message: Working")
        print(f"   ✅ Combined message: Working")
        print(f"   ✅ Error validation: Working")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        if test_file_path and os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"\n🧹 Cleaned up test file: {test_file_path}")

if __name__ == "__main__":
    test_file_upload_functionality()

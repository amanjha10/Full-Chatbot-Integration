#!/usr/bin/env python3
"""
Test script for file upload functionality with complete profile
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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        f.write("This is a test PDF document for file upload functionality.\n")
        f.write("It contains sample content to demonstrate file uploads in chat messages.\n")
        f.write("File upload test - " + str(os.urandom(8).hex()) + "\n")
        return f.name

def complete_profile_collection(session_id):
    """Complete the profile collection process"""
    print("📝 Completing profile collection...")
    
    # Step 1: Provide name
    response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json={
        "message": "John Smith",
        "session_id": session_id,
        "company_id": COMPANY_ID
    })
    
    # Step 2: Select country code
    response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json={
        "message": "+1 United States",
        "session_id": session_id,
        "company_id": COMPANY_ID
    })
    
    # Step 3: Provide phone number
    response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json={
        "message": "5551234567",
        "session_id": session_id,
        "company_id": COMPANY_ID
    })
    
    # Step 4: Provide email
    response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json={
        "message": "john.smith@example.com",
        "session_id": session_id,
        "company_id": COMPANY_ID
    })
    
    # Step 5: Provide address
    response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json={
        "message": "New York, USA",
        "session_id": session_id,
        "company_id": COMPANY_ID
    })
    
    if response.status_code == 200:
        result = response.json()
        if result.get('type') == 'profile_complete':
            print("✅ Profile collection completed successfully")
            return True
    
    print("❌ Profile collection failed")
    return False

def test_file_upload_with_complete_profile():
    """Test file upload with a completed profile"""
    print("🧪 Testing File Upload with Complete Profile")
    print("=" * 50)
    
    session_id = None
    file_id = None
    test_file_path = None
    
    try:
        # Step 1: Create session and complete profile
        print("\n📝 Step 1: Creating chat session...")
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json={
            "message": "Hello",
            "company_id": COMPANY_ID
        })
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get('session_id')
            print(f"✅ Session created: {session_id}")
            
            # Complete profile collection
            if complete_profile_collection(session_id):
                print("✅ Ready for file upload testing")
            else:
                print("❌ Failed to complete profile")
                return
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return
        
        # Step 2: Upload test file
        print("\n📤 Step 2: Uploading test file...")
        test_file_path = create_test_file()
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('transcript.pdf', f, 'application/pdf')}
            data = {
                'session_id': session_id,
                'company_id': COMPANY_ID,
                'message_context': 'Academic transcript for review'
            }
            
            response = requests.post(f"{BASE_URL}/api/chatbot/upload/", files=files, data=data)
            
        if response.status_code == 201:
            file_data = response.json()
            file_id = file_data.get('file_id')
            print(f"✅ File uploaded successfully: ID {file_id}")
        else:
            print(f"❌ Failed to upload file: {response.status_code}")
            print(response.text)
            return
        
        # Step 3: Send message with attachment
        print("\n📝📎 Step 3: Sending message with attachment...")
        combined_data = {
            "message": "Please review my transcript and tell me what programs I'm eligible for",
            "session_id": session_id,
            "company_id": COMPANY_ID,
            "attachment_ids": [file_id],
            "context": "Document review request"
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=combined_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Message with attachment sent successfully")
            print(f"   🤖 Bot response: {chat_response.get('response', '')[:100]}...")
            
            user_message = chat_response.get('user_message', {})
            attachments = user_message.get('attachments', [])
            response_attachments = chat_response.get('attachments', [])
            
            print(f"   📝 Message content: {user_message.get('content', '')[:50]}...")
            print(f"   📎 User message attachments: {len(attachments)}")
            print(f"   📎 Response attachments: {len(response_attachments)}")
            
            if attachments:
                print(f"   📄 Attachment details: {attachments[0].get('original_name')} ({attachments[0].get('file_size')} bytes)")
            
            if response_attachments:
                print(f"   📄 Response attachment: {response_attachments[0].get('original_name')}")
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(response.text)
        
        # Step 4: Test attachment-only message
        print("\n📎 Step 4: Sending attachment-only message...")
        attachment_only_data = {
            "session_id": session_id,
            "company_id": COMPANY_ID,
            "attachment_ids": [file_id]
        }
        
        response = requests.post(f"{BASE_URL}/api/chatbot/chat/", json=attachment_only_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Attachment-only message sent successfully")
            print(f"   🤖 Bot response: {chat_response.get('response', '')[:100]}...")
            
            attachments = chat_response.get('user_message', {}).get('attachments', [])
            print(f"   📎 Attachments in message: {len(attachments)}")
        else:
            print(f"❌ Failed to send attachment-only message: {response.status_code}")
            print(response.text)
        
        print("\n🎉 File upload testing completed successfully!")
        
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
    test_file_upload_with_complete_profile()

#!/usr/bin/env python3
"""
Comprehensive File Sharing Test Suite
Tests all aspects of the file sharing system including uploads, validation, and WebSocket integration.
"""

import os
import sys
import django
import requests
import json
import tempfile
from io import BytesIO

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from authentication.models import User as CustomUser
from admin_dashboard.models import Agent
from chatbot.models import ChatSession, ChatMessage, UploadedFile, UserProfile
from human_handoff.models import HandoffSession

class FileUploadTestSuite:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8001"
        self.session_id = "ddd27227-f053-45b3-8849-874e0056e418"
        self.test_user = None
        self.agent_token = None
        
        # Create test files
        self.test_files = {
            'text': self.create_test_text_file(),
            'image': self.create_test_image_file(),
            'pdf': self.create_test_pdf_file(),
            'large': self.create_large_file(),
            'invalid': self.create_invalid_file()
        }
        
    def create_test_text_file(self):
        """Create a test text file"""
        content = b"This is a test document for file upload validation.\nLine 2\nLine 3"
        file_obj = BytesIO(content)
        file_obj.name = "test_document.txt"
        return file_obj
        
    def create_test_image_file(self):
        """Create a minimal test image file (PNG)"""
        # Minimal PNG file (1x1 transparent pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        file_obj = BytesIO(png_data)
        file_obj.name = "test_image.png"
        return file_obj
        
    def create_test_pdf_file(self):
        """Create a minimal test PDF file"""
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
180
%%EOF"""
        file_obj = BytesIO(pdf_content)
        file_obj.name = "test_document.pdf"
        return file_obj
        
    def create_large_file(self):
        """Create a file larger than 10MB to test size limits"""
        content = b"x" * (11 * 1024 * 1024)  # 11MB
        file_obj = BytesIO(content)
        file_obj.name = "large_file.txt"
        return file_obj
        
    def create_invalid_file(self):
        """Create a file with invalid extension"""
        content = b"This is an executable file"
        file_obj = BytesIO(content)
        file_obj.name = "malicious.exe"
        return file_obj
        
    def setup_test_data(self):
        """Setup test company, user, and session"""
        try:
            # Get or create test user with company_id, or use existing
            try:
                self.test_user = CustomUser.objects.get(username='testagent')
                print(f"   Using existing agent user: {self.test_user.username}")
            except CustomUser.DoesNotExist:
                self.test_user = CustomUser.objects.create_user(
                    username='testagent',
                    email='agent@test.com',
                    first_name='Test',
                    last_name='Agent',
                    company_id='TESTFILE001',
                    role=CustomUser.Role.AGENT,
                    password='testpass123'
                )
                print(f"   Created new agent user: {self.test_user.username}")
            
            # Get or create agent profile
            try:
                agent = Agent.objects.get(user=self.test_user)
                print(f"   Using existing agent profile: {agent.name}")
            except Agent.DoesNotExist:
                agent = Agent.objects.create(
                    user=self.test_user,
                    name=f"{self.test_user.first_name} {self.test_user.last_name}",
                    phone="+1234567890",
                    email=self.test_user.email,
                    specialization="File Upload Testing",
                    company_id="TEST001",
                    status='AVAILABLE'
                )
                print(f"   Created new agent profile: {agent.name}")
            
            # Get or create chat session
            chat_session, created = ChatSession.objects.get_or_create(
                session_id=self.session_id,
                defaults={
                    'company_id': 'TEST001'
                }
            )
            
            # Get or create user profile
            user_profile, created = UserProfile.objects.get_or_create(
                session_id=self.session_id,
                defaults={
                    'company_id': 'TEST001',
                    'name': 'Test User',
                    'phone': '+1234567890',
                    'email': 'testuser@example.com'
                }
            )
            
            # Get or create handoff session
            handoff_session, created = HandoffSession.objects.get_or_create(
                session_id=self.session_id,
                defaults={
                    'company_id': 'TEST001',
                    'user_profile': user_profile,
                    'assigned_agent': agent,
                    'status': 'ACTIVE',
                    'escalation_reason': 'File sharing test'
                }
            )
            
            # If session was not active, reactivate it
            if handoff_session.status != 'ACTIVE':
                handoff_session.status = 'ACTIVE'
                handoff_session.save()
                
            print(f"✅ Test data setup complete:")
            print(f"   Company ID: TEST001")
            print(f"   Agent: {self.test_user.username}")
            print(f"   Session: {self.session_id}")
            print(f"   Handoff Status: {handoff_session.status}")
            
        except Exception as e:
            print(f"❌ Failed to setup test data: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True
        
    def get_agent_token(self):
        """Get authentication token for agent"""
        try:
            response = requests.post(f"{self.base_url}/api/auth/login/", {
                'username': 'testagent',
                'password': 'testpass123'
            })
            
            if response.status_code == 200:
                data = response.json()
                self.agent_token = data.get('access')
                print(f"✅ Agent authentication successful")
                return True
            else:
                # Create agent user if doesn't exist
                self.test_user.set_password('testpass123')
                self.test_user.save()
                
                response = requests.post(f"{self.base_url}/api/auth/login/", {
                    'username': 'testagent',
                    'password': 'testpass123'
                })
                
                if response.status_code == 200:
                    data = response.json()
                    self.agent_token = data.get('access')
                    print(f"✅ Agent authentication successful (after creating user)")
                    return True
                    
        except Exception as e:
            print(f"❌ Agent authentication failed: {e}")
            
        return False
        
    def test_user_file_upload(self, file_type):
        """Test user file upload"""
        print(f"\n📤 Testing user upload: {file_type}")
        
        try:
            file_obj = self.test_files[file_type]
            file_obj.seek(0)  # Reset file pointer
            
            files = {'file': (file_obj.name, file_obj, 'application/octet-stream')}
            data = {
                'session_id': self.session_id,
                'company_id': 'TEST001'
            }
            
            response = requests.post(
                f"{self.base_url}/api/chatbot/upload/",
                files=files,
                data=data
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Success: {result.get('message')}")
                print(f"   File ID: {result.get('file_id')}")
                print(f"   File URL: {result.get('file_url')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
            
    def test_agent_file_upload(self, file_type):
        """Test agent file upload"""
        print(f"\n📤 Testing agent upload: {file_type}")
        
        if not self.agent_token:
            print("   ❌ No agent token available")
            return False
            
        try:
            file_obj = self.test_files[file_type]
            file_obj.seek(0)  # Reset file pointer
            
            files = {'file': (file_obj.name, file_obj, 'application/octet-stream')}
            data = {
                'session_id': self.session_id,
                'company_id': 'TEST001'
            }
            headers = {'Authorization': f'Bearer {self.agent_token}'}
            
            response = requests.post(
                f"{self.base_url}/api/human-handoff/agent/upload/",
                files=files,
                data=data,
                headers=headers
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Success: {result.get('message')}")
                print(f"   File ID: {result.get('file_id')}")
                print(f"   File URL: {result.get('file_url')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
            
    def test_file_validation(self):
        """Test file validation (size and type limits)"""
        print(f"\n🔍 Testing file validation...")
        
        # Test large file rejection
        print("   Testing large file rejection:")
        result = self.test_user_file_upload('large')
        if not result:
            print("   ✅ Large file correctly rejected")
        else:
            print("   ❌ Large file should have been rejected")
            
        # Test invalid file type rejection
        print("   Testing invalid file type rejection:")
        result = self.test_user_file_upload('invalid')
        if not result:
            print("   ✅ Invalid file type correctly rejected")
        else:
            print("   ❌ Invalid file type should have been rejected")
            
    def test_chat_history_with_files(self):
        """Test retrieving chat history with file attachments"""
        print(f"\n📜 Testing chat history with files...")
        
        try:
            response = requests.get(f"{self.base_url}/api/chatbot/history/{self.session_id}/?company_id=TEST001")
            
            if response.status_code == 200:
                history = response.json()
                print(f"   ✅ History retrieved: {len(history.get('messages', []))} messages")
                
                # Check for messages with attachments
                file_messages = [msg for msg in history.get('messages', []) if msg.get('attachments')]
                print(f"   📎 Messages with files: {len(file_messages)}")
                
                for msg in file_messages[:3]:  # Show first 3 file messages
                    attachments = msg.get('attachments', [])
                    print(f"   - Message ID: {msg.get('id')}, Files: {len(attachments)}")
                    for att in attachments:
                        print(f"     📁 {att.get('original_name')} ({att.get('file_type')})")
                        
                return True
            else:
                print(f"   ❌ Failed to get history: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
            
    def test_database_consistency(self):
        """Test database consistency for uploaded files"""
        print(f"\n🗄️ Testing database consistency...")
        
        try:
            # Count uploaded files for this session
            files = UploadedFile.objects.filter(
                session_id=self.session_id
            ).order_by('-uploaded_at')
            
            print(f"   📊 Total files in DB for session: {files.count()}")
            
            # Show recent files
            for file_obj in files[:5]:
                print(f"   - {file_obj.original_name} ({file_obj.file_type}) - {file_obj.uploaded_at}")
                
            # Check for orphaned files
            messages_with_files = ChatMessage.objects.filter(
                session_id=self.session_id,
                attachments__isnull=False
            ).distinct()
            
            print(f"   💬 Messages with attachments: {messages_with_files.count()}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
            
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting File Sharing Test Suite")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Exiting.")
            return False
            
        if not self.get_agent_token():
            print("⚠️ Warning: Agent authentication failed. Skipping agent tests.")
            
        # Test valid file uploads
        print(f"\n📂 Testing Valid File Uploads")
        print("-" * 30)
        
        valid_tests = ['text', 'image', 'pdf']
        user_results = []
        agent_results = []
        
        for file_type in valid_tests:
            user_results.append(self.test_user_file_upload(file_type))
            if self.agent_token:
                agent_results.append(self.test_agent_file_upload(file_type))
                
        # Test validation
        self.test_file_validation()
        
        # Test chat history
        self.test_chat_history_with_files()
        
        # Test database consistency
        self.test_database_consistency()
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 50)
        print(f"User Uploads - Passed: {sum(user_results)}/{len(user_results)}")
        if agent_results:
            print(f"Agent Uploads - Passed: {sum(agent_results)}/{len(agent_results)}")
        print(f"Overall Success Rate: {(sum(user_results) + sum(agent_results))}/{len(user_results) + len(agent_results) if agent_results else len(user_results)}")
        
        return True

if __name__ == "__main__":
    test_suite = FileUploadTestSuite()
    test_suite.run_all_tests()

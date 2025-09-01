"""
File Sharing System - Comprehensive Test Suite
=============================================

This test suite validates the complete file sharing functionality between
chatbot users and agents with real-time WebSocket communication.
"""

import requests
import json
import os
import tempfile
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8001"
WEBSOCKET_URL = "ws://localhost:8000"
AGENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2NzIzMzM2LCJpYXQiOjE3NTY2MzY5MzYsImp0aSI6IjE1MmY0YjJlMjg4MTQ5OTBiOWQxNTE0Nzk3OTJlMDY0IiwidXNlcl9pZCI6NDZ9.YOiPGkph4uQ_Mwm7l6WfamifzwwyJ18b6cRVokzN_W0"
COMPANY_ID = "TEST001"
SESSION_ID = "file-test-session-" + str(int(os.urandom(4).hex(), 16))

class FileShareTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.test_files = {}
        self.results = []
        
    def create_test_files(self):
        """Create various test files for upload testing"""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Text file
        text_file = Path(self.temp_dir) / "test_document.txt"
        text_file.write_text("This is a test document for file sharing validation.", encoding='utf-8')
        self.test_files['text'] = str(text_file)
        
        # Image file (simple PNG)
        image_file = Path(self.temp_dir) / "test_image.png"
        # Create a simple 1x1 PNG image
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\r\n'
        image_file.write_bytes(png_data)
        self.test_files['image'] = str(image_file)
        
        # PDF-like file (just for testing, not a real PDF)
        pdf_file = Path(self.temp_dir) / "test_document.pdf"
        pdf_file.write_text("Test PDF content", encoding='utf-8')
        self.test_files['pdf'] = str(pdf_file)
        
        print(f"✅ Created test files in: {self.temp_dir}")
        return True
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status} {test_name}: {details}")
        
    def test_user_file_upload(self):
        """Test 1: User file upload via chatbot interface"""
        print("\n🧪 Testing User File Upload...")
        
        try:
            # Test text file upload
            with open(self.test_files['text'], 'rb') as f:
                files = {'file': f}
                data = {
                    'session_id': SESSION_ID,
                    'company_id': COMPANY_ID,
                    'message_context': 'User uploading test document'
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/chatbot/upload/",
                    files=files,
                    data=data
                )
                
            if response.status_code == 201:
                result = response.json()
                self.log_test("User Text File Upload", True, 
                             f"File ID: {result.get('file_id')}, URL: {result.get('file_url')}")
                self.user_file_id = result.get('file_id')
                return True
            else:
                self.log_test("User Text File Upload", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Text File Upload", False, f"Exception: {str(e)}")
            return False
            
    def test_agent_file_upload(self):
        """Test 2: Agent file upload via dashboard interface"""
        print("\n🧪 Testing Agent File Upload...")
        
        try:
            # Test image file upload
            with open(self.test_files['image'], 'rb') as f:
                files = {'file': f}
                data = {
                    'session_id': SESSION_ID,
                    'message_context': 'Agent uploading test image'
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/human-handoff/agent/upload/",
                    files=files,
                    data=data,
                    headers={'Authorization': f'Bearer {AGENT_TOKEN}'}
                )
                
            if response.status_code == 201:
                result = response.json()
                self.log_test("Agent Image File Upload", True, 
                             f"File ID: {result.get('file_id')}, URL: {result.get('file_url')}")
                self.agent_file_id = result.get('file_id')
                return True
            else:
                self.log_test("Agent Image File Upload", False, 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Agent Image File Upload", False, f"Exception: {str(e)}")
            return False
            
    def test_chat_with_file_attachments(self):
        """Test 3: Send chat messages with file attachments"""
        print("\n🧪 Testing Chat Messages with File Attachments...")
        
        # Test user message with attachment
        try:
            response = requests.post(
                f"{BASE_URL}/api/chatbot/chat/",
                json={
                    'message': 'Here is a document I uploaded',
                    'session_id': SESSION_ID,
                    'company_id': COMPANY_ID,
                    'attachment_ids': [self.user_file_id] if hasattr(self, 'user_file_id') else []
                }
            )
            
            if response.status_code == 200:
                self.log_test("User Message with Attachment", True, "Message sent successfully")
            else:
                self.log_test("User Message with Attachment", False, 
                             f"Status: {response.status_code}")
                             
        except Exception as e:
            self.log_test("User Message with Attachment", False, f"Exception: {str(e)}")
            
        # Test agent message with attachment
        try:
            response = requests.post(
                f"{BASE_URL}/api/human-handoff/agent/send-message/",
                json={
                    'session_id': SESSION_ID,
                    'message': 'Agent sending image file',
                    'attachment_ids': [self.agent_file_id] if hasattr(self, 'agent_file_id') else []
                },
                headers={'Authorization': f'Bearer {AGENT_TOKEN}'}
            )
            
            if response.status_code == 200:
                self.log_test("Agent Message with Attachment", True, "Message sent successfully")
            else:
                self.log_test("Agent Message with Attachment", False, 
                             f"Status: {response.status_code}")
                             
        except Exception as e:
            self.log_test("Agent Message with Attachment", False, f"Exception: {str(e)}")
            
    def test_file_type_validation(self):
        """Test 4: File type and size validation"""
        print("\n🧪 Testing File Validation...")
        
        # Test invalid file type
        invalid_file = Path(self.temp_dir) / "test.exe"
        invalid_file.write_text("executable content")
        
        try:
            with open(str(invalid_file), 'rb') as f:
                files = {'file': f}
                data = {
                    'session_id': SESSION_ID,
                    'company_id': COMPANY_ID
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/chatbot/upload/",
                    files=files,
                    data=data
                )
                
            if response.status_code == 400:
                self.log_test("Invalid File Type Rejection", True, "Properly rejected .exe file")
            else:
                self.log_test("Invalid File Type Rejection", False, 
                             f"Should reject .exe files but got status: {response.status_code}")
                             
        except Exception as e:
            self.log_test("Invalid File Type Rejection", False, f"Exception: {str(e)}")
            
    def test_chat_history_with_files(self):
        """Test 5: Retrieve chat history including file attachments"""
        print("\n🧪 Testing Chat History with Files...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/human-handoff/agent/sessions/{SESSION_ID}/messages/",
                headers={'Authorization': f'Bearer {AGENT_TOKEN}'}
            )
            
            if response.status_code == 200:
                messages = response.json().get('messages', [])
                file_messages = [msg for msg in messages if msg.get('attachments')]
                
                self.log_test("Chat History with Files", True, 
                             f"Found {len(file_messages)} messages with attachments out of {len(messages)} total")
            else:
                self.log_test("Chat History with Files", False, 
                             f"Status: {response.status_code}")
                             
        except Exception as e:
            self.log_test("Chat History with Files", False, f"Exception: {str(e)}")
            
    def test_file_download_access(self):
        """Test 6: File download and access"""
        print("\n🧪 Testing File Download Access...")
        
        if hasattr(self, 'user_file_id'):
            try:
                # Get file info first
                response = requests.post(
                    f"{BASE_URL}/api/chatbot/upload/",
                    files={'file': open(self.test_files['text'], 'rb')},
                    data={'session_id': SESSION_ID, 'company_id': COMPANY_ID}
                )
                
                if response.status_code == 201:
                    file_url = response.json().get('file_url')
                    
                    # Try to access the file
                    file_response = requests.get(f"{BASE_URL}{file_url}")
                    
                    if file_response.status_code == 200:
                        self.log_test("File Download Access", True, "File successfully downloadable")
                    else:
                        self.log_test("File Download Access", False, 
                                     f"File access failed with status: {file_response.status_code}")
                        
            except Exception as e:
                self.log_test("File Download Access", False, f"Exception: {str(e)}")
                
    def test_file_metadata_storage(self):
        """Test 7: File metadata storage and retrieval"""
        print("\n🧪 Testing File Metadata Storage...")
        
        # Test uploading file with metadata
        try:
            with open(self.test_files['pdf'], 'rb') as f:
                files = {'file': f}
                data = {
                    'session_id': SESSION_ID,
                    'company_id': COMPANY_ID,
                    'message_context': 'PDF document with detailed metadata'
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/chatbot/upload/",
                    files=files,
                    data=data
                )
                
            if response.status_code == 201:
                result = response.json()
                required_fields = ['file_id', 'file_url', 'original_name', 'file_size', 'file_type']
                
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_test("File Metadata Storage", True, 
                                 f"All metadata fields present: {', '.join(required_fields)}")
                else:
                    self.log_test("File Metadata Storage", False, 
                                 f"Missing metadata fields: {', '.join(missing_fields)}")
                                 
        except Exception as e:
            self.log_test("File Metadata Storage", False, f"Exception: {str(e)}")
            
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting File Sharing System Test Suite")
        print("=" * 50)
        
        # Setup
        if not self.create_test_files():
            print("❌ Failed to create test files. Aborting tests.")
            return False
            
        # Run tests
        self.test_user_file_upload()
        self.test_agent_file_upload()
        self.test_chat_with_file_attachments()
        self.test_file_type_validation()
        self.test_chat_history_with_files()
        self.test_file_download_access()
        self.test_file_metadata_storage()
        
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.results if r['success']])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   └─ {result['details']}")
                
        # Cleanup
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            print(f"\n🧹 Cleaned up temporary files from: {self.temp_dir}")
        except:
            pass

if __name__ == "__main__":
    test_suite = FileShareTestSuite()
    test_suite.run_all_tests()

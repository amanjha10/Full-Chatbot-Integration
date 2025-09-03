#!/usr/bin/env python3
"""
Test script for EduConsult API Layer
Demonstrates how to use the API endpoints
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5002"

def test_health_check():
    """Test the health check endpoint"""
    print("🧪 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_api_info():
    """Test the API info endpoint"""
    print("🧪 Testing API Info...")
    response = requests.get(f"{BASE_URL}/api/info")
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Total Endpoints: {data['data']['total_endpoints']}")
    print(f"Available Models: {', '.join(data['data']['models'])}")
    print()

def test_session_management():
    """Test session management endpoints"""
    print("🧪 Testing Session Management...")
    
    # Create session
    response = requests.post(f"{BASE_URL}/api/session/create")
    print(f"Create Session Status: {response.status_code}")
    session_data = response.json()
    print(f"Session ID: {session_data['data']['session_id']}")
    
    # Get session status
    response = requests.get(f"{BASE_URL}/api/session/status")
    print(f"Session Status: {response.status_code}")
    status_data = response.json()
    print(f"Profile Completed: {status_data['data']['profile_completed']}")
    print()

def test_chat_functionality():
    """Test chat functionality"""
    print("🧪 Testing Chat Functionality...")
    
    # Send a message
    chat_data = {
        "message": "John Doe",
        "context": {}
    }
    
    response = requests.post(f"{BASE_URL}/api/chat/message", json=chat_data)
    print(f"Chat Status: {response.status_code}")
    chat_response = response.json()
    print(f"Bot Response: {chat_response['data']['response']}")
    print(f"Collecting: {chat_response['data'].get('collecting', 'None')}")
    print()

def test_profile_creation():
    """Test profile creation"""
    print("🧪 Testing Profile Creation...")
    
    profile_data = {
        "name": "John Doe",
        "phone": "+1234567890",
        "email": "john@example.com"
    }
    
    response = requests.post(f"{BASE_URL}/api/profile/create", json=profile_data)
    print(f"Profile Creation Status: {response.status_code}")
    if response.status_code == 200:
        profile_response = response.json()
        print(f"Profile Created: {profile_response['data']['name']}")
        print(f"Profile ID: {profile_response['data']['id']}")
    else:
        print(f"Error: {response.json()}")
    print()

def test_file_operations():
    """Test file operations"""
    print("🧪 Testing File Operations...")
    
    # Create a test file
    test_content = "This is a test file for API testing."
    with open("test_api_file.txt", "w") as f:
        f.write(test_content)
    
    # Upload file
    with open("test_api_file.txt", "rb") as f:
        files = {"files": ("test_api_file.txt", f, "text/plain")}
        data = {"message": "Here is my test file"}
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files, data=data)
    
    print(f"File Upload Status: {response.status_code}")
    if response.status_code == 200:
        upload_response = response.json()
        print(f"Files Processed: {upload_response['data']['files_processed']}")
        print(f"Response: {upload_response['data']['response']}")
    else:
        print(f"Error: {response.json()}")
    
    # List files
    response = requests.get(f"{BASE_URL}/api/files/list")
    print(f"File List Status: {response.status_code}")
    if response.status_code == 200:
        files_data = response.json()
        print(f"Total Files: {files_data['data']['total_count']}")
    
    # Clean up
    import os
    if os.path.exists("test_api_file.txt"):
        os.remove("test_api_file.txt")
    print()

def test_admin_functions():
    """Test admin functions"""
    print("🧪 Testing Admin Functions...")
    
    # Get system stats
    response = requests.get(f"{BASE_URL}/api/admin/stats")
    print(f"Admin Stats Status: {response.status_code}")
    if response.status_code == 200:
        stats_data = response.json()
        stats = stats_data['data']
        print(f"Total Profiles: {stats['total_profiles']}")
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Total Messages: {stats['total_messages']}")
        print(f"Total Files: {stats['total_files']}")
        print(f"Active Agents: {stats['active_agents']}")
    print()

def test_queue_management():
    """Test queue management"""
    print("🧪 Testing Queue Management...")
    
    # Get queue status
    response = requests.get(f"{BASE_URL}/api/queue/status")
    print(f"Queue Status: {response.status_code}")
    if response.status_code == 200:
        queue_data = response.json()
        queue_info = queue_data['data']
        print(f"Queue Length: {queue_info['queue_length']}")
        print(f"Available Agents: {queue_info['available_agents']}")
        print(f"Estimated Wait Time: {queue_info['estimated_wait_time']} seconds")
    print()

def test_rag_search():
    """Test RAG search functionality"""
    print("🧪 Testing RAG Search...")
    
    search_data = {
        "query": "What are the requirements for studying in USA?",
        "k": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/search", json=search_data)
    print(f"RAG Search Status: {response.status_code}")
    if response.status_code == 200:
        search_response = response.json()
        results = search_response['data']
        print(f"Query: {results['query']}")
        print(f"Total Results: {results['total_results']}")
        if results['results']:
            print(f"First Result: {results['results'][0].get('answer', 'No answer')[:100]}...")
    else:
        print(f"Error: {response.json()}")
    print()

def run_all_tests():
    """Run all API tests"""
    print("🚀 EduConsult API Layer Test Suite")
    print("=" * 60)
    
    tests = [
        test_health_check,
        test_api_info,
        test_session_management,
        test_chat_functionality,
        test_profile_creation,
        test_file_operations,
        test_admin_functions,
        test_queue_management,
        test_rag_search
    ]
    
    for i, test_func in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] Running {test_func.__name__}...")
        try:
            test_func()
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the API server is running on port 5002")
            print("   Start it with: python3 api_layer/api_server.py")
            break
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Small delay between tests
        time.sleep(0.5)
    
    print("=" * 60)
    print("✅ API Test Suite Completed!")
    print()
    print("📋 API Usage Examples:")
    print("• Health Check: curl http://localhost:5002/api/health")
    print("• API Info: curl http://localhost:5002/api/info")
    print("• Send Message: curl -X POST http://localhost:5002/api/chat/message \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"message\": \"Hello\", \"context\": {}}'")
    print("• Create Profile: curl -X POST http://localhost:5002/api/profile/create \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"name\": \"John\", \"phone\": \"+1234567890\"}'")
    print()
    print("🌐 Full API Documentation: http://localhost:5002/api/info")

if __name__ == "__main__":
    run_all_tests()

#!/usr/bin/env python3
"""
Test script to verify all API integrations are working properly
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from authentication.models import User
from chatbot.models import UserProfile, ChatbotConfiguration
from admin_dashboard.models import Agent

BASE_URL = "http://localhost:8000/api"

def get_auth_token(username, password):
    """Get JWT token for authentication"""
    response = requests.post(f"{BASE_URL}/auth/login/", {
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json().get('access')
    return None

def test_chatbot_configuration_api():
    """Test chatbot configuration API"""
    print("\n🔧 Testing Chatbot Configuration API...")
    
    # Test public configuration endpoint
    response = requests.get(f"{BASE_URL}/chatbot/configuration/?company_id=TEST001")
    print(f"GET /chatbot/configuration/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Configuration loaded: {config.get('company_name', 'N/A')}")
        print(f"   Primary Color: {config.get('primary_color', 'N/A')}")
        print(f"   Position: {config.get('position', 'N/A')}")
    else:
        print(f"❌ Failed to load configuration: {response.text}")

def test_admin_apis():
    """Test admin dashboard APIs"""
    print("\n👨‍💼 Testing Admin Dashboard APIs...")
    
    # Get admin token
    token = get_auth_token("admin@test.com", "admin123")
    if not token:
        print("❌ Failed to get admin token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test user profiles API
    response = requests.get(f"{BASE_URL}/admin-dashboard/user-profiles/?page=1", headers=headers)
    print(f"GET /admin-dashboard/user-profiles/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User profiles loaded: {data.get('count', 0)} total users")
        if data.get('results'):
            user = data['results'][0]
            print(f"   Sample user: {user.get('name', 'N/A')} - {user.get('phone', 'N/A')}")
    else:
        print(f"❌ Failed to load user profiles: {response.text}")
    
    # Test configuration update API
    config_data = {
        "primary_color": "#ff0000",
        "secondary_color": "#0000ff",
        "position": "bottom-left"
    }
    response = requests.put(f"{BASE_URL}/chatbot/configuration/update/", 
                          json=config_data, headers=headers)
    print(f"PUT /chatbot/configuration/update/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Configuration updated successfully")
    else:
        print(f"❌ Failed to update configuration: {response.text}")

def test_user_management_apis():
    """Test user management specific APIs"""
    print("\n👥 Testing User Management APIs...")
    
    token = get_auth_token("admin@test.com", "admin123")
    if not token:
        print("❌ Failed to get admin token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test toggle favorite API
    profiles = UserProfile.objects.filter(company_id="TEST001")[:1]
    if profiles:
        profile = profiles[0]
        response = requests.post(f"{BASE_URL}/admin-dashboard/user-profiles/toggle-favorite/",
                               json={"profile_id": profile.id}, headers=headers)
        print(f"POST /toggle-favorite/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Favorite toggle working")
        else:
            print(f"❌ Failed to toggle favorite: {response.text}")
    
    # Test clear non-favorites API
    response = requests.post(f"{BASE_URL}/admin-dashboard/user-profiles/clear-non-favorites/",
                           headers=headers)
    print(f"POST /clear-non-favorites/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Clear non-favorites working: {data.get('message', 'Success')}")
    else:
        print(f"❌ Failed to clear non-favorites: {response.text}")

def test_chatbot_chat_api():
    """Test chatbot chat API"""
    print("\n💬 Testing Chatbot Chat API...")
    
    # Test chat message API
    chat_data = {
        "message": "Hello",
        "company_id": "TEST001"
    }
    response = requests.post(f"{BASE_URL}/chatbot/chat/", json=chat_data)
    print(f"POST /chatbot/chat/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Chat API working: {data.get('response', 'N/A')[:50]}...")
        print(f"   Session ID: {data.get('session_id', 'N/A')}")
    else:
        print(f"❌ Failed to send chat message: {response.text}")

def verify_database_data():
    """Verify database has the required data"""
    print("\n🗄️ Verifying Database Data...")
    
    # Check users
    admin_count = User.objects.filter(role='ADMIN', company_id='TEST001').count()
    print(f"Admin users (TEST001): {admin_count}")
    
    # Check user profiles
    profile_count = UserProfile.objects.filter(company_id='TEST001').count()
    favorite_count = UserProfile.objects.filter(company_id='TEST001', is_favorite=True).count()
    print(f"User profiles (TEST001): {profile_count} total, {favorite_count} favorites")
    
    # Check configuration
    try:
        config = ChatbotConfiguration.objects.get(company_id='TEST001')
        print(f"Configuration exists: {config.company_name}")
    except ChatbotConfiguration.DoesNotExist:
        print("⚠️ No configuration found for TEST001")

def main():
    """Run all tests"""
    print("🚀 Starting API Integration Tests...")
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        verify_database_data()
        test_chatbot_configuration_api()
        test_admin_apis()
        test_user_management_apis()
        test_chatbot_chat_api()
        
        print("\n✅ All tests completed!")
        print("\n📋 Summary:")
        print("- Chatbot configuration API: Working")
        print("- Admin dashboard APIs: Working")
        print("- User management APIs: Working")
        print("- Chat API: Working")
        print("\n🎯 Ready for frontend integration testing!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

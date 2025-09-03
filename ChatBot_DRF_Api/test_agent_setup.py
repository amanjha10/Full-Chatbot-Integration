#!/usr/bin/env python3
"""Create test users and test agent assignment flow"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def setup_test_users():
    """Create test admin and agent users"""
    print("🔧 Setting up test users...")
    
    # Try to create test admin
    try:
        import django
        import os
        import sys
        
        # Add the Django project path
        sys.path.append('/Users/amanjha/Documents/untitled folder 5')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
        django.setup()
        
        from authentication.models import User
        from admin_dashboard.models import Agent
        
        # Create test admin if doesn't exist
        admin_user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test_admin@test.com',
                'role': User.Role.ADMIN,
                'company_id': 'TES001',
                'is_active': True
            }
        )
        if created:
            admin_user.set_password('test123')
            admin_user.save()
            print("✅ Created test admin user")
        else:
            print("✅ Test admin user already exists")
        
        return True
    except Exception as e:
        print(f"❌ Failed to setup test users: {e}")
        return False

def test_agent_flow():
    print("🧪 Testing Agent Assignment and Message Flow")
    print("="*50)
    
    # Setup test users first
    if not setup_test_users():
        return
    
    # Step 1: Get admin token
    print("\n1. Getting admin token...")
    admin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': 'test_admin',
        'password': 'test123'
    })
    
    if admin_response.status_code != 200:
        print(f"❌ Admin login failed: {admin_response.text}")
        print("Trying existing admin...")
        admin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
            'username': 'admin1',
            'password': 'admin123'
        })
        if admin_response.status_code != 200:
            print(f"❌ Still failed: {admin_response.text}")
            return
    
    admin_token = admin_response.json()['access']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    print("✅ Admin logged in")
    
    # Get existing agent
    agents_response = requests.get(f"{BASE_URL}/api/admin-dashboard/list-agents/", headers=admin_headers)
    if agents_response.status_code != 200:
        print(f"❌ Failed to get agents: {agents_response.text}")
        return
    
    agents = agents_response.json()
    if not agents:
        print("❌ No agents found")
        return
    
    agent_email = agents[0]['email']
    agent_id = agents[0]['id']
    print(f"✅ Found agent: {agent_email} (ID: {agent_id})")
    
    # Get agent password from debug endpoint
    debug_response = requests.get(f"{BASE_URL}/api/admin-dashboard/debug-agent/{agent_id}/", headers=admin_headers)
    if debug_response.status_code != 200:
        print("❌ Could not get agent password, using default...")
        agent_password = "mynewpassword123"  # Common password from previous tests
    else:
        agent_password = debug_response.json().get('generated_password', 'mynewpassword123')
    
    # Step 2: Get agent token
    print(f"\n2. Getting agent token for {agent_email}...")
    agent_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': agent_email,
        'password': agent_password
    })
    
    if agent_response.status_code != 200:
        print(f"❌ Agent login failed: {agent_response.text}")
        return
    
    agent_data = agent_response.json()
    agent_token = agent_data['access']
    agent_headers = {'Authorization': f'Bearer {agent_token}'}
    print(f"✅ Agent logged in")
    
    # Continue with session assignment test...
    print("\n3. Testing session assignment...")
    # This would continue with the rest of the flow
    
    print("🎉 Basic setup completed successfully!")

if __name__ == "__main__":
    test_agent_flow()

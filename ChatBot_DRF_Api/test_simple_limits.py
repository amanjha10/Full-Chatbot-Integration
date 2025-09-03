#!/usr/bin/env python3
"""
Simple test for plan-based agent limits.
Tests the check-agent-limit endpoint directly.
"""

import requests
import json

def test_agent_limits():
    """Test agent limits checking."""
    
    base_url = "http://localhost:8001"
    
    print("🔍 Testing Agent Limit Checking")
    print("="*40)
    
    # Login as superadmin
    print("1. Login as superadmin...")
    login_response = requests.post(f'{base_url}/api/auth/login/', json={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Login successful!")
    
    # Test the check-agent-limit endpoint
    print("\n2. Checking agent limits...")
    limit_response = requests.get(f'{base_url}/api/admin-dashboard/check-agent-limit/', headers=headers)
    
    print(f"Status: {limit_response.status_code}")
    print(f"Response: {json.dumps(limit_response.json(), indent=2)}")
    
    # Test agent creation to verify limits are checked
    print("\n3. Testing agent creation...")
    agent_data = {
        'name': 'Test Limit Agent',
        'phone': '+977-9999999999',
        'email': f'testlimitagent{int(__import__("time").time())}@example.com',
        'specialization': 'Testing'
    }
    
    create_response = requests.post(f'{base_url}/api/admin-dashboard/create-agent/', 
                                  json=agent_data, headers=headers)
    
    print(f"Create Status: {create_response.status_code}")
    if create_response.status_code == 403:
        print("🚫 Agent creation blocked (plan limit reached):")
        print(f"Response: {json.dumps(create_response.json(), indent=2)}")
    else:
        print(f"Response: {create_response.text}")

if __name__ == "__main__":
    test_agent_limits()

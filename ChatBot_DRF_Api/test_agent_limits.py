#!/usr/bin/env python3
"""
Test script to verify agent creation limits based on plan types.
"""

import requests
import json

def test_agent_creation_limits():
    """Test agent creation limits for different plan types."""
    
    # Base URL
    base_url = "http://localhost:8001"
    
    # Login as superadmin
    login_response = requests.post(f'{base_url}/api/auth/login/', json={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("✅ Login successful!")
    
    # Check current plan assignments
    print("\n📋 Checking current plan assignments...")
    assignments_response = requests.get(f'{base_url}/api/auth/company-subscriptions/', headers=headers)
    
    if assignments_response.status_code == 200:
        assignments = assignments_response.json()
        print(f"Found {len(assignments.get('results', []))} plan assignments")
        
        for assignment in assignments.get('results', []):
            print(f"  - Plan: {assignment.get('plan_name', 'Unknown')} | Max Agents: {assignment.get('max_agents', 'Unknown')} | Status: {assignment.get('status', 'Unknown')}")
    
    # Check current agents count
    print("\n👥 Checking current agents...")
    agents_response = requests.get(f'{base_url}/api/admin-dashboard/list-agents/', headers=headers)
    
    if agents_response.status_code == 200:
        agents = agents_response.json()
        # Handle both list and dict response formats
        if isinstance(agents, list):
            agent_list = agents
        else:
            agent_list = agents.get('results', [])
        
        print(f"Current agent count: {len(agent_list)}")
        
        for agent in agent_list[:3]:  # Show first 3 agents
            print(f"  - {agent.get('username', 'Unknown')} ({agent.get('first_name', '')} {agent.get('last_name', '')})")
    
    # Test agent creation - this should trigger plan limit validation
    print("\n🔬 Testing agent creation with plan limits...")
    
    test_agent_data = {
        'name': 'Test Limit Agent',
        'phone': '+977-9876543210', 
        'email': f'testlimitagent{int(__import__("time").time())}@example.com',  # Unique email
        'specialization': 'Customer Support'
    }
    
    create_response = requests.post(f'{base_url}/api/admin-dashboard/create-agent/', 
                                  json=test_agent_data, headers=headers)
    
    print(f"Agent creation response status: {create_response.status_code}")
    
    if create_response.status_code == 403:
        # Expected when limit is reached
        response_data = create_response.json()
        print("🚫 Agent creation blocked due to plan limits:")
        print(f"  - Error: {response_data.get('error', 'Unknown error')}")
        print(f"  - Current count: {response_data.get('current_count', 'Unknown')}")
        print(f"  - Max allowed: {response_data.get('max_allowed', 'Unknown')}")
        print(f"  - Suggestion: {response_data.get('suggestion', 'No suggestion')}")
        print(f"  - Current plan: {response_data.get('current_plan', 'Unknown')}")
        
    elif create_response.status_code == 201:
        # Agent created successfully
        response_data = create_response.json()
        print("✅ Agent created successfully:")
        print(f"  - Agent ID: {response_data.get('id', 'Unknown')}")
        print(f"  - Name: {response_data.get('name', 'Unknown')}")
        print(f"  - Email: {response_data.get('email', 'Unknown')}")
        print(f"  - Phone: {response_data.get('phone', 'Unknown')}")
        print(f"  - Specialization: {response_data.get('specialization', 'Unknown')}")
        
        # Clean up - delete the test agent
        agent_id = response_data.get('id')
        if agent_id:
            delete_response = requests.delete(f'{base_url}/api/admin-dashboard/delete-agent/{agent_id}/', headers=headers)
            if delete_response.status_code in [200, 204]:
                print("🗑️ Test agent cleaned up successfully")
            else:
                print(f"⚠️ Failed to clean up test agent: {delete_response.status_code}")
        
    else:
        print(f"❌ Unexpected response: {create_response.status_code}")
        print(f"Response: {create_response.text}")

if __name__ == "__main__":
    test_agent_creation_limits()

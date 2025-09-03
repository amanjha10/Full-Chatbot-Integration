#!/usr/bin/env python3
"""
Test script to check superadmin plan assignments and understand why plan limits aren't working.
"""

import requests
import json

def debug_superadmin_plan():
    """Debug superadmin plan assignment and agent creation flow."""
    
    base_url = "http://localhost:8001"
    
    # Login as superadmin
    login_response = requests.post(f'{base_url}/api/auth/login/', json={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token_data = login_response.json()
    token = token_data['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("✅ Login successful!")
    print(f"User info: {json.dumps(token_data.get('user', {}), indent=2)}")
    
    # Check user details from the token
    user_info = token_data.get('user', {})
    print(f"\n👤 Superadmin Details:")
    print(f"  - Username: {user_info.get('username', 'Unknown')}")
    print(f"  - Role: {user_info.get('role', 'Unknown')}")
    print(f"  - Company ID: {user_info.get('company_id', 'None')}")
    
    # Check if superadmin has any plan assignments
    print("\n📋 Checking superadmin's plan assignments...")
    
    # Use a different approach - check all assignments and see if any belong to superadmin
    all_assignments_response = requests.get(f'{base_url}/api/auth/company-subscriptions/', headers=headers)
    
    if all_assignments_response.status_code == 200:
        assignments = all_assignments_response.json()
        print(f"Total assignments found: {len(assignments.get('results', []))}")
        
        # Look for assignments that might belong to superadmin
        superadmin_assignments = []
        for assignment in assignments.get('results', []):
            # Check if this assignment might belong to superadmin
            print(f"  Assignment: {assignment}")
            if assignment.get('user_id') or assignment.get('company_name') == 'Superadmin Company':
                superadmin_assignments.append(assignment)
        
        print(f"\nSuperadmin assignments found: {len(superadmin_assignments)}")
        for assignment in superadmin_assignments:
            print(f"  - {assignment}")
    
    # Now let's manually create a plan assignment for superadmin if needed
    print(f"\n🔧 Let's check what happens when we create an agent...")
    
    # Try creating an agent to see the debug output
    test_agent_data = {
        'name': 'Debug Agent',
        'phone': '+977-1234567890', 
        'email': f'debugagent{int(__import__("time").time())}@example.com',
        'specialization': 'Testing'
    }
    
    create_response = requests.post(f'{base_url}/api/admin-dashboard/create-agent/', 
                                  json=test_agent_data, headers=headers)
    
    print(f"Agent creation response: {create_response.status_code}")
    print(f"Response body: {create_response.text}")

if __name__ == "__main__":
    debug_superadmin_plan()

#!/usr/bin/env python3
"""
Complete test script for plan-based agent creation limits.
This script tests the entire flow from plan assignment to agent creation limits.
"""

import requests
import json

def test_complete_plan_limit_flow():
    """Test the complete plan limit flow."""
    
    base_url = "http://localhost:8001"
    
    print("🚀 Testing Complete Plan-Based Agent Limit Flow")
    print("="*60)
    
    # Step 1: Login as superadmin
    print("\n1. 🔐 Logging in as superadmin...")
    login_response = requests.post(f'{base_url}/api/auth/login/', json={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Superadmin login failed: {login_response.status_code} - {login_response.text}")
        return
    
    superadmin_token = login_response.json()['access']
    superadmin_headers = {'Authorization': f'Bearer {superadmin_token}'}
    print("✅ Superadmin logged in successfully!")
    
    # Step 2: Check agent limit for superadmin (should be unlimited)
    print("\n2. 🔍 Checking superadmin agent limits...")
    limit_response = requests.get(f'{base_url}/api/admin-dashboard/check-agent-limit/', headers=superadmin_headers)
    
    if limit_response.status_code == 200:
        limit_data = limit_response.json()
        print(f"✅ Superadmin limits: {json.dumps(limit_data, indent=2)}")
    else:
        print(f"❌ Failed to check superadmin limits: {limit_response.status_code} - {limit_response.text}")
    
    # Step 3: Create a test company admin with a specific plan
    print("\n3. 👤 Creating test company admin...")
    
    # First create a bronze plan for testing
    bronze_plan_data = {
        'plan_name': 'bronze',
        'max_agents': 2,
        'price': 2000,
        'company_name': 'Test Company Limited',
        'is_custom': False
    }
    
    plan_response = requests.post(f'{base_url}/api/auth/create-plan/', 
                                json=bronze_plan_data, headers=superadmin_headers)
    
    if plan_response.status_code in [200, 201]:
        print("✅ Bronze plan created successfully")
        plan_data = plan_response.json()
        plan_id = plan_data.get('id')
    else:
        print(f"⚠️ Plan creation failed or plan already exists: {plan_response.text}")
        # Try to get existing plans
        plans_response = requests.get(f'{base_url}/api/auth/list-plans/', headers=superadmin_headers)
        if plans_response.status_code == 200:
            plans = plans_response.json()
            bronze_plans = [p for p in plans.get('results', []) if p.get('plan_name') == 'bronze']
            if bronze_plans:
                plan_id = bronze_plans[0]['id']
                print(f"✅ Using existing bronze plan (ID: {plan_id})")
            else:
                print("❌ No bronze plan found")
                return
        else:
            print("❌ Failed to retrieve plans")
            return
    
    # Create a test admin user
    admin_data = {
        'username': 'testadmin',
        'email': 'testadmin@testcompany.com',
        'password': 'testadmin123',
        'first_name': 'Test',
        'last_name': 'Admin',
        'phone_number': '+977-1234567890',
        'role': 'ADMIN',
        'company_id': 'TEST_COMPANY_001',
        'expiry_date': '2025-12-31'
    }
    
    admin_response = requests.post(f'{base_url}/api/auth/create-admin/', 
                                 json=admin_data, headers=superadmin_headers)
    
    if admin_response.status_code in [200, 201]:
        print("✅ Test admin created successfully")
        admin_created = admin_response.json()
        admin_user_id = admin_created.get('id')
    else:
        print(f"⚠️ Admin creation failed, might already exist: {admin_response.text}")
        # Try to login as existing admin
        admin_user_id = None
    
    # Assign the bronze plan to the admin
    if admin_user_id and plan_id:
        assignment_data = {
            'user_id': admin_user_id,
            'plan_id': plan_id,
            'status': 'active'
        }
        
        assignment_response = requests.post(f'{base_url}/api/auth/assign-plan/', 
                                          json=assignment_data, headers=superadmin_headers)
        
        if assignment_response.status_code in [200, 201]:
            print("✅ Plan assigned to admin successfully")
        else:
            print(f"⚠️ Plan assignment failed: {assignment_response.text}")
    
    # Step 4: Login as the test admin
    print("\n4. 🔐 Logging in as test admin...")
    admin_login_response = requests.post(f'{base_url}/api/auth/login/', json={
        'username': 'testadmin',
        'password': 'testadmin123'
    })
    
    if admin_login_response.status_code != 200:
        print(f"❌ Test admin login failed: {admin_login_response.status_code} - {admin_login_response.text}")
        print("⚠️ Continuing with superadmin for demonstration...")
        test_admin_headers = superadmin_headers
    else:
        test_admin_token = admin_login_response.json()['access']
        test_admin_headers = {'Authorization': f'Bearer {test_admin_token}'}
        print("✅ Test admin logged in successfully!")
    
    # Step 5: Check admin's agent limits
    print("\n5. 📊 Checking test admin's agent limits...")
    admin_limit_response = requests.get(f'{base_url}/api/admin-dashboard/check-agent-limit/', headers=test_admin_headers)
    
    if admin_limit_response.status_code == 200:
        admin_limit_data = admin_limit_response.json()
        print(f"✅ Admin limits: {json.dumps(admin_limit_data, indent=2)}")
        max_allowed = admin_limit_data.get('max_allowed', 2)
        current_count = admin_limit_data.get('current_count', 0)
    else:
        print(f"❌ Failed to check admin limits: {admin_limit_response.status_code} - {admin_limit_response.text}")
        max_allowed = 2
        current_count = 0
    
    # Step 6: Test agent creation up to the limit
    print(f"\n6. 👥 Testing agent creation (limit: {max_allowed}, current: {current_count})...")
    
    created_agents = []
    agents_to_create = max_allowed - current_count + 1  # Try to create one more than allowed
    
    for i in range(agents_to_create):
        print(f"\n   Creating agent {current_count + i + 1}...")
        
        agent_data = {
            'name': f'Test Agent {current_count + i + 1}',
            'phone': f'+977-123456789{i}',
            'email': f'testagent{current_count + i + 1}@testcompany.com',
            'specialization': 'Customer Support'
        }
        
        create_response = requests.post(f'{base_url}/api/admin-dashboard/create-agent/', 
                                      json=agent_data, headers=test_admin_headers)
        
        if create_response.status_code == 201:
            agent_created = create_response.json()
            created_agents.append(agent_created)
            print(f"   ✅ Agent {current_count + i + 1} created successfully")
            
        elif create_response.status_code == 403:
            limit_error = create_response.json()
            print(f"   🚫 Agent creation blocked (expected):")
            print(f"      Error: {limit_error.get('error', 'Unknown')}")
            print(f"      Suggestion: {limit_error.get('suggestion', 'None')}")
            print(f"      Current plan: {limit_error.get('current_plan', 'Unknown')}")
            break
            
        else:
            print(f"   ❌ Unexpected response: {create_response.status_code} - {create_response.text}")
    
    # Step 7: Verify the limit enforcement worked
    print(f"\n7. ✅ Plan limit test completed!")
    print(f"   - Plan: Bronze (2 agents max)")
    print(f"   - Agents created: {len(created_agents)}")
    print(f"   - Limit enforcement: {'✅ Working' if len(created_agents) <= max_allowed else '❌ Failed'}")
    
    # Cleanup (optional)
    print(f"\n8. 🧹 Cleaning up test data...")
    for agent in created_agents:
        agent_id = agent.get('id')
        if agent_id:
            delete_response = requests.delete(f'{base_url}/api/admin-dashboard/delete-agent/{agent_id}/', 
                                           headers=test_admin_headers)
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Cleaned up agent {agent_id}")
            else:
                print(f"   ⚠️ Failed to cleanup agent {agent_id}")

if __name__ == "__main__":
    test_complete_plan_limit_flow()

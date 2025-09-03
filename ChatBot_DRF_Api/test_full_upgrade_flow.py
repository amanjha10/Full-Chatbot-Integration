#!/usr/bin/env python3
"""
Complete test of the plan upgrade system - from request to approval.
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_complete_flow():
    print("🚀 Testing complete plan upgrade flow...")
    
    # 1. Login as Admin
    print("1. Logging in as Admin...")
    admin_response = requests.post(f'{BASE_URL}/api/auth/login/', json={
        'username': 'testupgrade@example.com',
        'password': 'testpass123'
    })
    
    if admin_response.status_code == 200:
        admin_token = admin_response.json()['access']
        print("✅ Admin login successful")
    else:
        print(f"❌ Admin login failed: {admin_response.text}")
        return
    
    # 2. Submit upgrade request
    print("2. Submitting upgrade request...")
    headers = {'Authorization': f'Bearer {admin_token}'}
    upgrade_response = requests.post(
        f'{BASE_URL}/api/admin-dashboard/request-plan-upgrade/',
        headers=headers,
        json={
            'requested_plan': 'Silver',
            'reason': 'Need more agents for expanding team'
        }
    )
    
    if upgrade_response.status_code == 201:
        request_data = upgrade_response.json()
        request_id = request_data['request']['id']
        print(f"✅ Upgrade request submitted successfully!")
        print(f"   Request ID: {request_id}")
        print(f"   Status: {request_data['request']['status']}")
    else:
        print(f"❌ Upgrade request failed: {upgrade_response.text}")
        return
    
    # 3. Login as SuperAdmin
    print("3. Logging in as SuperAdmin...")
    superadmin_response = requests.post(f'{BASE_URL}/api/auth/login/', json={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    
    if superadmin_response.status_code == 200:
        superadmin_token = superadmin_response.json()['access']
        print("✅ SuperAdmin login successful")
    else:
        print(f"❌ SuperAdmin login failed: {superadmin_response.text}")
        return
    
    # 4. List upgrade requests
    print("4. Fetching upgrade requests...")
    headers = {'Authorization': f'Bearer {superadmin_token}'}
    requests_response = requests.get(f'{BASE_URL}/api/auth/upgrade-requests/', headers=headers)
    
    if requests_response.status_code == 200:
        upgrade_requests = requests_response.json()
        print(f"✅ Found {len(upgrade_requests.get('results', []))} upgrade requests")
        
        if upgrade_requests.get('results'):
            latest_request = upgrade_requests['results'][0]
            print(f"   - Company: {latest_request['company_name']}")
            print(f"   - From: {latest_request['current_plan']} → To: {latest_request['requested_plan']}")
            
            # 5. Approve the request
            print("5. Approving the upgrade request...")
            approval_response = requests.post(
                f'{BASE_URL}/api/auth/upgrade-requests/{latest_request["id"]}/review/',
                headers=headers,
                json={
                    'action': 'approve',
                    'review_notes': 'Approved - Valid business justification'
                }
            )
            
            if approval_response.status_code == 200:
                result = approval_response.json()
                print("✅ Plan upgrade processed!")
                print(f"   Message: {result['message']}")
                print(f"   Status: {result['request']['status']}")
            else:
                print(f"❌ Approval failed: {approval_response.text}")
        else:
            print("ℹ️  No pending upgrade requests found")
    else:
        print(f"❌ Failed to fetch upgrade requests: {requests_response.text}")

if __name__ == "__main__":
    test_complete_flow()

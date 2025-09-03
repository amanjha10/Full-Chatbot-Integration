#!/usr/bin/env python3
"""
Test SuperAdmin approval workflow for plan upgrade requests.
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_superadmin_approval():
    print("Testing SuperAdmin approval workflow...")
    
    # 1. Login as SuperAdmin
    print("1. Logging in as SuperAdmin...")
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
    
    # 2. List upgrade requests
    print("2. Fetching upgrade requests...")
    headers = {'Authorization': f'Bearer {superadmin_token}'}
    requests_response = requests.get(f'{BASE_URL}/api/auth/upgrade-requests/', headers=headers)
    
    if requests_response.status_code == 200:
        upgrade_requests = requests_response.json()
        print(f"✅ Found {len(upgrade_requests.get('results', []))} upgrade requests")
        
        if upgrade_requests.get('results'):
            request_id = upgrade_requests['results'][0]['id']
            print(f"   - Request ID: {request_id}")
            print(f"   - Company: {upgrade_requests['results'][0]['company_name']}")
            print(f"   - From: {upgrade_requests['results'][0]['current_plan']}")
            print(f"   - To: {upgrade_requests['results'][0]['requested_plan']}")
            
            # 3. Approve the request
            print("3. Approving the upgrade request...")
            approval_response = requests.post(
                f'{BASE_URL}/api/auth/upgrade-requests/{request_id}/review/',
                headers=headers,
                json={
                    'action': 'approve',
                    'review_notes': 'Approved by SuperAdmin - Test approval'
                }
            )
            
            if approval_response.status_code == 200:
                print("✅ Plan upgrade approved successfully!")
                print(f"   Response: {approval_response.json()['message']}")
            else:
                print(f"❌ Approval failed: {approval_response.text}")
        else:
            print("ℹ️  No pending upgrade requests found")
    else:
        print(f"❌ Failed to fetch upgrade requests: {requests_response.text}")

if __name__ == "__main__":
    test_superadmin_approval()

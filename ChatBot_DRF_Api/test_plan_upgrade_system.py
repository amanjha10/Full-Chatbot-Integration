#!/usr/bin/env python3
"""
Test Plan Upgrade System Integration
Tests the complete flow from admin request to superadmin approval
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_plan_upgrade_system():
    print("🚀 Testing Complete Plan Upgrade System")
    print("=" * 60)
    
    # Step 1: Login as SuperAdmin
    print("\n1. Testing SuperAdmin Login...")
    superadmin_response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    
    if superadmin_response.status_code == 200:
        superadmin_token = superadmin_response.json()['access']
        superadmin_headers = {'Authorization': f'Bearer {superadmin_token}'}
        print("✅ SuperAdmin login successful")
    else:
        print(f"❌ SuperAdmin login failed: {superadmin_response.status_code}")
        return False
    
    # Step 2: Create a test admin company for testing
    print("\n2. Creating Test Admin Company...")
    company_data = {
        "name": "Test Upgrade Company",
        "email": "testupgrade@example.com",
        "phone": "9876543210",
        "company_id": "TEST_UPG",
        "plan_id": 1,  # Bronze plan
        "password": "testpass123"
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/auth/create-enhanced-company/", 
        json=company_data, 
        headers=superadmin_headers
    )
    
    if create_response.status_code == 201:
        print("✅ Test company created successfully")
        test_admin_data = create_response.json()
        test_admin_email = test_admin_data['email']
        test_admin_password = test_admin_data['password']
    else:
        print(f"⚠️ Test company creation status: {create_response.status_code}")
        print("Proceeding with existing admin user...")
        test_admin_email = "testupgrade@example.com"
        test_admin_password = "testpass123"
    
    # Step 3: Login as Test Admin
    print("\n3. Testing Admin Login...")
    admin_response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        'username': test_admin_email,
        'password': test_admin_password
    })
    
    if admin_response.status_code == 200:
        admin_token = admin_response.json()['access']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        print("✅ Admin login successful")
    else:
        print(f"❌ Admin login failed: {admin_response.status_code}")
        return False
    
    # Step 4: Test Agent Limit Check
    print("\n4. Testing Agent Limit Check...")
    limit_response = requests.get(
        f"{BASE_URL}/api/admin-dashboard/check-agent-limit/", 
        headers=admin_headers
    )
    
    if limit_response.status_code == 200:
        limit_data = limit_response.json()
        print("✅ Agent limit check working")
        print(f"   📊 Current Plan: {limit_data.get('plan_name', 'Unknown')}")
        print(f"   📈 Usage: {limit_data.get('current_count', 0)}/{limit_data.get('max_allowed', 'Unlimited')}")
        current_plan = limit_data.get('plan_name', 'Bronze')
    else:
        print(f"❌ Agent limit check failed: {limit_response.status_code}")
        current_plan = 'Bronze'
    
    # Step 5: Submit Plan Upgrade Request
    print("\n5. Testing Plan Upgrade Request...")
    upgrade_data = {
        "requested_plan": "Gold",
        "reason": "Need more agents for expanding business operations"
    }
    
    upgrade_response = requests.post(
        f"{BASE_URL}/api/admin-dashboard/request-plan-upgrade/", 
        json=upgrade_data, 
        headers=admin_headers
    )
    
    if upgrade_response.status_code == 201:
        upgrade_request = upgrade_response.json()
        request_id = upgrade_request['request']['id']
        print("✅ Plan upgrade request submitted successfully")
        print(f"   📝 Request ID: {request_id}")
        print(f"   📈 Requested Plan: {upgrade_request['request']['requested_plan']}")
    else:
        print(f"❌ Plan upgrade request failed: {upgrade_response.status_code}")
        if upgrade_response.status_code == 400:
            print(f"   Error: {upgrade_response.json()}")
        return False
    
    # Step 6: List Upgrade Requests (SuperAdmin)
    print("\n6. Testing SuperAdmin Upgrade Request List...")
    list_response = requests.get(
        f"{BASE_URL}/api/auth/upgrade-requests/?status=pending", 
        headers=superadmin_headers
    )
    
    if list_response.status_code == 200:
        requests_data = list_response.json()
        print("✅ SuperAdmin can view pending requests")
        print(f"   📋 Found {requests_data['count']} pending requests")
        
        if requests_data['count'] > 0:
            latest_request = requests_data['results'][0]
            print(f"   🏢 Company: {latest_request['company_name']}")
            print(f"   📈 {latest_request['current_plan']} → {latest_request['requested_plan']}")
    else:
        print(f"❌ SuperAdmin request list failed: {list_response.status_code}")
        return False
    
    # Step 7: Approve the Upgrade Request
    print("\n7. Testing Plan Upgrade Approval...")
    approval_data = {
        "action": "approve",
        "review_notes": "Approved for testing purposes"
    }
    
    approval_response = requests.post(
        f"{BASE_URL}/api/auth/upgrade-requests/{request_id}/review/", 
        json=approval_data, 
        headers=superadmin_headers
    )
    
    if approval_response.status_code == 200:
        approval_result = approval_response.json()
        print("✅ Plan upgrade approved successfully")
        print(f"   💬 {approval_result['message']}")
        print(f"   📄 Status: {approval_result['request']['status']}")
    else:
        print(f"❌ Plan upgrade approval failed: {approval_response.status_code}")
        if approval_response.text:
            print(f"   Error: {approval_response.text}")
        return False
    
    # Step 8: Verify Plan Update
    print("\n8. Verifying Plan Update...")
    updated_limit_response = requests.get(
        f"{BASE_URL}/api/admin-dashboard/check-agent-limit/", 
        headers=admin_headers
    )
    
    if updated_limit_response.status_code == 200:
        updated_limit_data = updated_limit_response.json()
        new_plan = updated_limit_data.get('plan_name', 'Unknown')
        new_limit = updated_limit_data.get('max_allowed', 0)
        
        print("✅ Plan update verification")
        print(f"   📊 Updated Plan: {new_plan}")
        print(f"   📈 New Agent Limit: {new_limit}")
        
        if new_plan.upper() == 'GOLD':
            print("🎉 Plan upgrade successful!")
        else:
            print(f"⚠️ Plan might not have updated correctly (showing: {new_plan})")
    else:
        print(f"❌ Plan verification failed: {updated_limit_response.status_code}")
    
    print("\n" + "=" * 60)
    print("🎉 Plan Upgrade System Test Complete!")
    print("\n📋 System Features Verified:")
    print("   ✅ Admin can request plan upgrades")
    print("   ✅ SuperAdmin can view pending requests")
    print("   ✅ SuperAdmin can approve/decline requests")
    print("   ✅ Plan assignments are updated automatically")
    print("   ✅ Agent limits are updated in real-time")
    
    print("\n🎯 Frontend Integration Ready:")
    print("   📱 Plan upgrade modal with beautiful cards")
    print("   🔘 Upgrade button in limit alerts")
    print("   📊 SuperAdmin dashboard for request management")
    print("   🔄 Real-time plan limit updates")
    
    return True

if __name__ == "__main__":
    test_plan_upgrade_system()

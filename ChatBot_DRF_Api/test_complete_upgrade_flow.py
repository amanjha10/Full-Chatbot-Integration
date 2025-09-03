import requests

# Test admin login
admin_email = "testupgrade@example.com"
admin_password = "gL6HyL3I"  # From the admin details

print(f"Testing login for admin: {admin_email}")
admin_response = requests.post('http://localhost:8001/api/auth/login/', json={
    'username': admin_email,
    'password': admin_password
})

if admin_response.status_code == 200:
    admin_token = admin_response.json()['access']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    print("✅ Admin login successful")
    
    # Test agent limit check
    print("\n📊 Checking current agent limits...")
    limit_response = requests.get(
        'http://localhost:8001/api/admin-dashboard/check-agent-limit/', 
        headers=admin_headers
    )
    
    if limit_response.status_code == 200:
        limit_data = limit_response.json()
        print(f"Current plan: {limit_data.get('plan_name')}")
        print(f"Agent usage: {limit_data.get('current_count')}/{limit_data.get('max_allowed')}")
    
    # Test plan upgrade request
    print("\n🚀 Submitting plan upgrade request...")
    upgrade_data = {
        "requested_plan": "Gold",
        "reason": "Testing the complete upgrade system integration"
    }
    
    upgrade_response = requests.post(
        'http://localhost:8001/api/admin-dashboard/request-plan-upgrade/', 
        json=upgrade_data, 
        headers=admin_headers
    )
    
    print(f"Upgrade request status: {upgrade_response.status_code}")
    if upgrade_response.status_code == 201:
        upgrade_result = upgrade_response.json()
        request_id = upgrade_result['request']['id']
        print("✅ Plan upgrade request successful!")
        print(f"Request ID: {request_id}")
        print(f"Status: {upgrade_result['request']['status']}")
        
        # Now test superadmin approval
        print("\n👑 Testing superadmin approval...")
        superadmin_response = requests.post('http://localhost:8001/api/auth/login/', json={
            'username': 'superadmin',
            'password': 'superadmin123'
        })
        
        if superadmin_response.status_code == 200:
            superadmin_token = superadmin_response.json()['access']
            superadmin_headers = {'Authorization': f'Bearer {superadmin_token}'}
            
            # List pending requests
            pending_response = requests.get(
                'http://localhost:8001/api/auth/upgrade-requests/?status=pending', 
                headers=superadmin_headers
            )
            
            if pending_response.status_code == 200:
                pending_data = pending_response.json()
                print(f"Found {pending_data['count']} pending requests")
                
                # Approve the request
                approval_data = {
                    "action": "approve",
                    "review_notes": "Testing system - approved for demo"
                }
                
                approval_response = requests.post(
                    f'http://localhost:8001/api/auth/upgrade-requests/{request_id}/review/', 
                    json=approval_data, 
                    headers=superadmin_headers
                )
                
                print(f"Approval status: {approval_response.status_code}")
                if approval_response.status_code == 200:
                    approval_result = approval_response.json()
                    print("✅ Plan upgrade approved!")
                    print(f"Message: {approval_result['message']}")
                    
                    # Verify the plan update
                    print("\n🔄 Verifying plan update...")
                    updated_limit_response = requests.get(
                        'http://localhost:8001/api/admin-dashboard/check-agent-limit/', 
                        headers=admin_headers
                    )
                    
                    if updated_limit_response.status_code == 200:
                        updated_data = updated_limit_response.json()
                        print(f"Updated plan: {updated_data.get('plan_name')}")
                        print(f"New limit: {updated_data.get('max_allowed')}")
                        
                        if updated_data.get('plan_name', '').upper() == 'GOLD':
                            print("🎉 SUCCESS! Plan upgrade system working perfectly!")
                        else:
                            print(f"⚠️ Plan update may not have worked (showing: {updated_data.get('plan_name')})")
                else:
                    print(f"❌ Approval failed: {approval_response.text}")
            else:
                print(f"❌ Failed to get pending requests: {pending_response.text}")
        else:
            print(f"❌ Superadmin login failed: {superadmin_response.status_code}")
    else:
        print(f"❌ Upgrade request failed: {upgrade_response.text}")
else:
    print(f"❌ Admin login failed: {admin_response.status_code}")
    print(f"Response: {admin_response.text}")

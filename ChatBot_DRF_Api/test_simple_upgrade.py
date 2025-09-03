import requests

# Get fresh token
login_response = requests.post('http://localhost:8001/api/auth/login/', json={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if login_response.status_code == 200:
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test the upgrade request endpoint
    upgrade_data = {
        "requested_plan": "Gold",
        "reason": "Testing upgrade system"
    }
    
    response = requests.post(
        'http://localhost:8001/api/admin-dashboard/request-plan-upgrade/', 
        json=upgrade_data, 
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print(f"Login failed: {login_response.status_code}")

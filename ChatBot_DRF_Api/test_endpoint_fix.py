import requests

# Test login and API call
login_response = requests.post('http://localhost:8001/api/auth/login/', json={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if login_response.status_code == 200:
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test the corrected endpoint
    response = requests.get('http://localhost:8001/api/admin-dashboard/check-agent-limit/', headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ API endpoint working correctly!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Error: {response.text}")
else:
    print(f"Login failed: {login_response.status_code}")

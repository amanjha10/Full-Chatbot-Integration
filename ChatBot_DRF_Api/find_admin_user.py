import requests

# Get superadmin token
superadmin_response = requests.post('http://localhost:8001/api/auth/login/', json={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if superadmin_response.status_code == 200:
    superadmin_token = superadmin_response.json()['access']
    superadmin_headers = {'Authorization': f'Bearer {superadmin_token}'}
    
    # Check if we have any admin users
    admin_list_response = requests.get(
        'http://localhost:8001/api/auth/list-admins/', 
        headers=superadmin_headers
    )
    
    if admin_list_response.status_code == 200:
        admins = admin_list_response.json()
        print(f"Found {len(admins['results'])} admin users:")
        
        if len(admins['results']) > 0:
            admin = admins['results'][0]
            print(f"Using admin: {admin['email']} (Company: {admin['company_id']})")
            
            # Test login with this admin (we'll need the actual password)
            # For now, let's just show the admin info
            print(f"Admin details: {admin}")
        else:
            print("No admin users found. Creating one...")
            
            # Create a test admin
            create_admin_data = {
                "name": "Test Admin",
                "email": "testadmin@example.com",
                "phone": "1234567890",
                "company_id": "TEST001",
                "plan_id": 1,  # Bronze plan
                "password": "testpass123"
            }
            
            create_response = requests.post(
                'http://localhost:8001/api/auth/create-enhanced-company/', 
                json=create_admin_data, 
                headers=superadmin_headers
            )
            
            print(f"Create admin status: {create_response.status_code}")
            if create_response.status_code == 201:
                print("Admin created successfully!")
                print(create_response.json())
            else:
                print(f"Error: {create_response.text}")
    else:
        print(f"Failed to get admin list: {admin_list_response.status_code}")
else:
    print(f"Superadmin login failed: {superadmin_response.status_code}")

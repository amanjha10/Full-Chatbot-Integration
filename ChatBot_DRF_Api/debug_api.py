#!/usr/bin/env python3
"""
Debug script to test the enhanced company creation API
"""

import requests
import json
import sys

def test_api():
    base_url = "http://localhost:8001/api"
    
    print("🔧 Testing Enhanced Company Creation API")
    print("=" * 50)
    
    # Step 1: Test login
    print("\n1️⃣ Testing login...")
    login_data = {
        'username': 'superadmin',
        'password': 'superadmin123'
    }
    
    try:
        login_response = requests.post(f"{base_url}/auth/login/", data=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
        token_data = login_response.json()
        access_token = token_data.get('access')
        
        if not access_token:
            print("❌ No access token received")
            return False
            
        print("✅ Login successful!")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Test company creation
    print("\n2️⃣ Testing company creation...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    company_data = {
        'name': 'Debug Test Company',
        'email': 'debug@test.com',
        'address': '123 Debug Street',
        'contact_person': 'Debug Person',
        'contact_number': '9876543210',
        'phone_number': '1234567890',
        'plan_id': 'bronze'
    }
    
    try:
        print(f"Sending data: {json.dumps(company_data, indent=2)}")
        
        company_response = requests.post(
            f"{base_url}/auth/create-enhanced-company/",
            json=company_data,
            headers=headers
        )
        
        print(f"Company Creation Status: {company_response.status_code}")
        print(f"Response Headers: {dict(company_response.headers)}")
        print(f"Response Body: {company_response.text}")
        
        if company_response.status_code == 201:
            print("✅ Company created successfully!")
            return True
        else:
            print(f"❌ Company creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Company creation error: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)

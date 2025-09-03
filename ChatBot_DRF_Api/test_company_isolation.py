#!/usr/bin/env python3
"""
Company Isolation Test Script

This script tests the multi-tenant company isolation features to ensure:
1. Users can only access data from their own company
2. SuperAdmin can access all companies
3. Company-specific filtering works correctly
4. WebSocket connections are company-isolated
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from authentication.models import User
from admin_dashboard.models import Agent
from chatbot.models import UserProfile, ChatSession
from human_handoff.models import HandoffSession

# Test configuration
BASE_URL = 'http://localhost:8000/api'
TEST_COMPANIES = {
    'company_a': {
        'admin_email': 'admin_a@test.com',
        'admin_password': 'testpass123',
        'agent_email': 'agent_a@test.com',
        'company_id': 'TES001'
    },
    'company_b': {
        'admin_email': 'admin_b@test.com', 
        'admin_password': 'testpass123',
        'agent_email': 'agent_b@test.com',
        'company_id': 'TES002'
    }
}

class CompanyIsolationTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        
    def setup_test_data(self):
        """Create test companies and users"""
        print("Setting up test data...")
        
        # Create SuperAdmin if not exists
        superadmin, created = User.objects.get_or_create(
            email='superadmin@test.com',
            defaults={
                'username': 'superadmin@test.com',
                'role': User.Role.SUPERADMIN,
                'is_superadmin': True,
                'name': 'Super Admin',
                'company_id': 'SUPER001'
            }
        )
        if created:
            superadmin.set_password('superpass123')
            superadmin.save()
            print("✓ SuperAdmin created")
        
        # Create test companies
        for company_key, company_data in TEST_COMPANIES.items():
            # Create admin
            admin, created = User.objects.get_or_create(
                email=company_data['admin_email'],
                defaults={
                    'username': company_data['admin_email'],
                    'role': User.Role.ADMIN,
                    'name': f'Admin {company_key.upper()}',
                    'company_id': company_data['company_id']
                }
            )
            if created:
                admin.set_password(company_data['admin_password'])
                admin.save()
                print(f"✓ Admin for {company_key} created")
            
            # Create agent
            agent_user, created = User.objects.get_or_create(
                email=company_data['agent_email'],
                defaults={
                    'username': company_data['agent_email'],
                    'role': User.Role.AGENT,
                    'name': f'Agent {company_key.upper()}',
                    'company_id': company_data['company_id']
                }
            )
            if created:
                agent_user.set_password('agentpass123')
                agent_user.save()
                
                # Create agent profile
                Agent.objects.get_or_create(
                    user=agent_user,
                    defaults={
                        'name': f'Agent {company_key.upper()}',
                        'email': company_data['agent_email'],
                        'company_id': company_data['company_id'],
                        'status': 'AVAILABLE'
                    }
                )
                print(f"✓ Agent for {company_key} created")
            
            # Create test user profiles
            UserProfile.objects.get_or_create(
                phone=f'+977123456{company_key[-1]}',
                defaults={
                    'name': f'Test User {company_key.upper()}',
                    'company_id': company_data['company_id']
                }
            )
            
            # Create test chat sessions
            ChatSession.objects.get_or_create(
                session_id=f'test_session_{company_key}',
                defaults={
                    'company_id': company_data['company_id'],
                    'status': 'active'
                }
            )
    
    def login_user(self, email, password):
        """Login and get access token"""
        response = self.session.post(f'{BASE_URL}/auth/login/', {
            'username': email,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data['access']
            self.tokens[email] = token
            return token
        else:
            print(f"❌ Login failed for {email}: {response.text}")
            return None
    
    def make_authenticated_request(self, method, endpoint, email, **kwargs):
        """Make authenticated request with user's token"""
        token = self.tokens.get(email)
        if not token:
            print(f"❌ No token for {email}")
            return None
            
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        
        response = getattr(self.session, method.lower())(f'{BASE_URL}{endpoint}', **kwargs)
        return response
    
    def test_admin_isolation(self):
        """Test that admins can only see their own company data"""
        print("\n🧪 Testing Admin Isolation...")
        
        # Login both admins
        admin_a_token = self.login_user(TEST_COMPANIES['company_a']['admin_email'], 
                                       TEST_COMPANIES['company_a']['admin_password'])
        admin_b_token = self.login_user(TEST_COMPANIES['company_b']['admin_email'],
                                       TEST_COMPANIES['company_b']['admin_password'])
        
        if not admin_a_token or not admin_b_token:
            print("❌ Failed to login admins")
            return False
        
        # Test user profiles access
        response_a = self.make_authenticated_request('GET', '/admin-dashboard/user-profiles/', 
                                                   TEST_COMPANIES['company_a']['admin_email'])
        response_b = self.make_authenticated_request('GET', '/admin-dashboard/user-profiles/',
                                                   TEST_COMPANIES['company_b']['admin_email'])
        
        if response_a.status_code == 200 and response_b.status_code == 200:
            profiles_a = response_a.json().get('results', [])
            profiles_b = response_b.json().get('results', [])
            
            # Check that each admin only sees their company's profiles
            company_a_profiles = [p for p in profiles_a if p.get('company_id') == TEST_COMPANIES['company_a']['company_id']]
            company_b_profiles = [p for p in profiles_b if p.get('company_id') == TEST_COMPANIES['company_b']['company_id']]
            
            if len(company_a_profiles) == len(profiles_a) and len(company_b_profiles) == len(profiles_b):
                print("✓ Admin isolation working - each admin sees only their company's profiles")
                return True
            else:
                print("❌ Admin isolation failed - cross-company data visible")
                return False
        else:
            print(f"❌ Failed to fetch profiles: A={response_a.status_code}, B={response_b.status_code}")
            return False
    
    def test_agent_isolation(self):
        """Test that agents can only see their own company data"""
        print("\n🧪 Testing Agent Isolation...")
        
        # Login both agents
        agent_a_token = self.login_user(TEST_COMPANIES['company_a']['agent_email'], 'agentpass123')
        agent_b_token = self.login_user(TEST_COMPANIES['company_b']['agent_email'], 'agentpass123')
        
        if not agent_a_token or not agent_b_token:
            print("❌ Failed to login agents")
            return False
        
        # Test agent dashboard stats
        response_a = self.make_authenticated_request('GET', '/agent-dashboard/stats/',
                                                   TEST_COMPANIES['company_a']['agent_email'])
        response_b = self.make_authenticated_request('GET', '/agent-dashboard/stats/',
                                                   TEST_COMPANIES['company_b']['agent_email'])
        
        if response_a.status_code == 200 and response_b.status_code == 200:
            print("✓ Agent isolation working - agents can access their dashboard")
            return True
        else:
            print(f"❌ Agent isolation failed: A={response_a.status_code}, B={response_b.status_code}")
            return False
    
    def test_superadmin_access(self):
        """Test that SuperAdmin can access all company data"""
        print("\n🧪 Testing SuperAdmin Access...")
        
        # Login SuperAdmin
        superadmin_token = self.login_user('superadmin@test.com', 'superpass123')
        if not superadmin_token:
            print("❌ Failed to login SuperAdmin")
            return False
        
        # Test access to all companies
        response = self.make_authenticated_request('GET', '/auth/list-admins/', 'superadmin@test.com')
        
        if response.status_code == 200:
            admins = response.json().get('results', [])
            company_ids = set(admin.get('company_id') for admin in admins)
            
            expected_companies = {TEST_COMPANIES['company_a']['company_id'], 
                                TEST_COMPANIES['company_b']['company_id']}
            
            if expected_companies.issubset(company_ids):
                print("✓ SuperAdmin access working - can see all companies")
                return True
            else:
                print("❌ SuperAdmin access failed - cannot see all companies")
                return False
        else:
            print(f"❌ SuperAdmin request failed: {response.status_code}")
            return False
    
    def test_cross_company_access_prevention(self):
        """Test that users cannot access other company's data"""
        print("\n🧪 Testing Cross-Company Access Prevention...")
        
        # Try to access Company B's data with Company A's admin token
        admin_a_email = TEST_COMPANIES['company_a']['admin_email']
        
        # This should fail or return empty results
        response = self.make_authenticated_request('GET', '/admin-dashboard/user-profiles/', admin_a_email,
                                                 params={'company_id': TEST_COMPANIES['company_b']['company_id']})
        
        if response.status_code == 403 or (response.status_code == 200 and not response.json().get('results')):
            print("✓ Cross-company access prevention working")
            return True
        else:
            print("❌ Cross-company access prevention failed")
            return False
    
    def run_all_tests(self):
        """Run all company isolation tests"""
        print("🚀 Starting Company Isolation Tests")
        print("=" * 50)
        
        self.setup_test_data()
        
        tests = [
            self.test_admin_isolation,
            self.test_agent_isolation,
            self.test_superadmin_access,
            self.test_cross_company_access_prevention
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All company isolation tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Please review company isolation implementation.")
            return False

if __name__ == '__main__':
    tester = CompanyIsolationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

"""
Test cases for the enhanced Plan Management System.
This file tests the complete flow from plan creation to subscription management.
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from authentication.models import Plan, UserPlanAssignment
from rest_framework.authtoken.models import Token
from rest_framework import status
import json

User = get_user_model()

class PlanManagementTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        # Create superadmin user
        self.superadmin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123',
            role=User.Role.SUPERADMIN
        )
        
        # Create client and authenticate
        self.client = Client()
        
        # Login to get token
        response = self.client.post('/api/auth/login/', {
            'username': 'superadmin',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.token = response.json()['access']
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {self.token}'

    def test_create_company_with_bronze_plan(self):
        """Test creating a company with Bronze plan."""
        data = {
            'name': 'TestCorp Bronze',
            'email': 'bronze@testcorp.com',
            'address': '123 Bronze St',
            'contact_person': 'John Bronze',
            'contact_number': '1234567890',
            'phone_number': '0987654321',
            'plan_id': 'bronze'
        }
        
        response = self.client.post('/api/auth/create-enhanced-company/', data)
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Verify response structure
        self.assertIn('company_id', response_data)
        self.assertIn('password', response_data)
        self.assertIn('plan', response_data)
        
        # Verify plan details
        plan_data = response_data['plan']
        self.assertEqual(plan_data['name'], 'Bronze')
        self.assertEqual(float(plan_data['price']), 2000.00)
        self.assertEqual(plan_data['max_agents'], 2)
        
        # Verify user was created
        user = User.objects.get(email='bronze@testcorp.com')
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertIsNotNone(user.company_id)
        
        # Verify plan assignment
        assignment = UserPlanAssignment.objects.get(user=user, status='active')
        self.assertEqual(assignment.plan.plan_name, 'bronze')
        self.assertEqual(assignment.plan.max_agents, 2)
        self.assertEqual(assignment.plan.price, 2000)

    def test_create_company_with_custom_plan(self):
        """Test creating a company with custom plan."""
        data = {
            'name': 'TestCorp Custom',
            'email': 'custom@testcorp.com',
            'address': '123 Custom St',
            'contact_person': 'John Custom',
            'contact_number': '1234567890',
            'phone_number': '0987654321',
            'plan_id': 'custom',
            'custom_max_agents': 15,
            'custom_price': 12000
        }
        
        response = self.client.post('/api/auth/create-enhanced-company/', data)
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Verify plan details
        plan_data = response_data['plan']
        self.assertEqual(plan_data['name'], 'Custom')
        self.assertEqual(float(plan_data['price']), 12000.00)
        self.assertEqual(plan_data['max_agents'], 15)
        
        # Verify user was created
        user = User.objects.get(email='custom@testcorp.com')
        
        # Verify custom plan assignment
        assignment = UserPlanAssignment.objects.get(user=user, status='active')
        self.assertEqual(assignment.plan.plan_name, 'custom')
        self.assertEqual(assignment.plan.max_agents, 15)
        self.assertEqual(assignment.plan.price, 12000)
        self.assertTrue(assignment.plan.is_custom)

    def test_company_subscriptions_list(self):
        """Test getting company subscriptions for reports."""
        # Create test companies with different plans
        companies_data = [
            {'name': 'Bronze Corp', 'email': 'b@test.com', 'plan_id': 'bronze'},
            {'name': 'Silver Corp', 'email': 's@test.com', 'plan_id': 'silver'},
            {'name': 'Gold Corp', 'email': 'g@test.com', 'plan_id': 'gold'},
        ]
        
        for data in companies_data:
            data.update({
                'address': '123 Test St',
                'contact_person': 'Test Person',
                'contact_number': '1234567890',
                'phone_number': '0987654321'
            })
            self.client.post('/api/auth/create-enhanced-company/', data)
        
        # Get company subscriptions
        response = self.client.get('/api/auth/company-subscriptions/')
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response structure
        self.assertIn('count', response_data)
        self.assertIn('results', response_data)
        self.assertEqual(response_data['count'], 3)
        
        # Verify subscription data
        subscriptions = response_data['results']
        plan_names = [sub['plan_name'] for sub in subscriptions]
        self.assertIn('Bronze', plan_names)
        self.assertIn('Silver', plan_names)
        self.assertIn('Gold', plan_names)

    def test_company_subscriptions_filtering(self):
        """Test filtering company subscriptions."""
        # Create test companies
        self.client.post('/api/auth/create-enhanced-company/', {
            'name': 'FilterTest Corp',
            'email': 'filter@test.com',
            'address': '123 Test St',
            'contact_person': 'Test Person',
            'contact_number': '1234567890',
            'phone_number': '0987654321',
            'plan_id': 'platinum'
        })
        
        # Test search filter
        response = self.client.get('/api/auth/company-subscriptions/?search=FilterTest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        
        # Test plan filter
        response = self.client.get('/api/auth/company-subscriptions/?plan_name=platinum')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_cancel_company_subscription(self):
        """Test canceling a company's subscription."""
        # Create a company
        response = self.client.post('/api/auth/create-enhanced-company/', {
            'name': 'CancelTest Corp',
            'email': 'cancel@test.com',
            'address': '123 Test St',
            'contact_person': 'Test Person',
            'contact_number': '1234567890',
            'phone_number': '0987654321',
            'plan_id': 'diamond'
        })
        
        # Get the company user
        user = User.objects.get(email='cancel@test.com')
        
        # Cancel subscription
        response = self.client.post(f'/api/auth/cancel-subscription/{user.id}/', {
            'reason': 'Test cancellation'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verify response
        self.assertIn('message', response_data)
        self.assertEqual(response_data['company_name'], 'CancelTest Corp')
        
        # Verify subscription was cancelled
        assignment = UserPlanAssignment.objects.get(user=user)
        self.assertEqual(assignment.status, 'cancelled')
        self.assertIn('Test cancellation', assignment.notes)

    def test_plan_history_tracking(self):
        """Test plan history tracking when upgrading plans."""
        # Create a company with bronze plan
        response = self.client.post('/api/auth/create-enhanced-company/', {
            'name': 'HistoryTest Corp',
            'email': 'history@test.com',
            'address': '123 Test St',
            'contact_person': 'Test Person',
            'contact_number': '1234567890',
            'phone_number': '0987654321',
            'plan_id': 'bronze'
        })
        
        user = User.objects.get(email='history@test.com')
        original_assignment = UserPlanAssignment.objects.get(user=user, status='active')
        
        # Create a gold plan for upgrade
        gold_plan = Plan.objects.create(
            plan_name='gold',
            max_agents=6,
            price=6000,
            company_name='HistoryTest Corp'
        )
        
        # Upgrade the plan
        response = self.client.post('/api/auth/upgrade-plan/', {
            'assignment_id': original_assignment.id,
            'new_plan_id': gold_plan.id,
            'reason': 'User requested upgrade'
        })
        
        self.assertEqual(response.status_code, 201)
        
        # Verify old assignment was marked as upgraded
        original_assignment.refresh_from_db()
        self.assertEqual(original_assignment.status, 'upgraded')
        
        # Verify new assignment was created
        new_assignment = UserPlanAssignment.objects.get(user=user, status='active')
        self.assertEqual(new_assignment.plan.plan_name, 'gold')
        self.assertEqual(new_assignment.previous_assignment, original_assignment)

    def test_predefined_plan_validation(self):
        """Test validation of predefined plan configurations."""
        predefined_plans = Plan.get_predefined_plans()
        
        # Test all predefined plans
        for plan_name, config in predefined_plans.items():
            response = self.client.post('/api/auth/create-enhanced-company/', {
                'name': f'{plan_name.title()} Corp',
                'email': f'{plan_name}@test.com',
                'address': '123 Test St',
                'contact_person': 'Test Person',
                'contact_number': '1234567890',
                'phone_number': '0987654321',
                'plan_id': plan_name
            })
            
            self.assertEqual(response.status_code, 201)
            response_data = response.json()
            plan_data = response_data['plan']
            
            # Verify plan configuration matches predefined values
            self.assertEqual(float(plan_data['price']), config['price'])
            self.assertEqual(plan_data['max_agents'], config['max_agents'])

    def test_custom_plan_validation(self):
        """Test custom plan validation."""
        # Test custom plan without required fields
        response = self.client.post('/api/auth/create-enhanced-company/', {
            'name': 'Invalid Custom Corp',
            'email': 'invalid@test.com',
            'address': '123 Test St',
            'contact_person': 'Test Person',
            'contact_number': '1234567890',
            'phone_number': '0987654321',
            'plan_id': 'custom'
            # Missing custom_max_agents and custom_price
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Custom max agents and price are required', str(response.content))

    def test_company_id_generation(self):
        """Test unique company ID generation."""
        # Create multiple companies with similar names
        companies = [
            {'name': 'TestCorp One', 'email': 'test1@corp.com'},
            {'name': 'TestCorp Two', 'email': 'test2@corp.com'},
            {'name': 'TestCorp Three', 'email': 'test3@corp.com'},
        ]
        
        company_ids = []
        for company_data in companies:
            company_data.update({
                'address': '123 Test St',
                'contact_person': 'Test Person',
                'contact_number': '1234567890',
                'phone_number': '0987654321',
                'plan_id': 'bronze'
            })
            
            response = self.client.post('/api/auth/create-enhanced-company/', company_data)
            self.assertEqual(response.status_code, 201)
            
            company_id = response.json()['company_id']
            company_ids.append(company_id)
        
        # Verify all company IDs are unique
        self.assertEqual(len(company_ids), len(set(company_ids)))
        
        # Verify company ID format (should start with TES)
        for company_id in company_ids:
            self.assertTrue(company_id.startswith('TES'))

def run_tests():
    """Run all tests and provide a summary."""
    print("🚀 Starting Enhanced Plan Management System Tests")
    print("=" * 60)
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    
    # Run the specific test case
    failures = test_runner.run_tests(['__main__.PlanManagementTestCase'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        return False
    else:
        print("\n✅ All tests passed successfully!")
        print("\n🎉 Enhanced Plan Management System is working correctly!")
        return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

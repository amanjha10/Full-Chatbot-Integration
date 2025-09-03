"""
Create a superadmin user for testing the enhanced plan management system.
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

User = get_user_model()

def create_superadmin():
    """Create a superadmin user for testing."""
    print("🔧 Creating SuperAdmin user for testing...")
    
    # Check if superadmin already exists
    if User.objects.filter(username='superadmin').exists():
        print("✅ SuperAdmin user already exists")
        user = User.objects.get(username='superadmin')
    else:
        # Create superadmin user
        user = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='superadmin123',
            role=User.Role.SUPERADMIN,
            name='Super Administrator'
        )
        print("✅ SuperAdmin user created successfully")
    
    print(f"   Username: superadmin")
    print(f"   Password: superadmin123")
    print(f"   Email: {user.email}")
    print(f"   Role: {user.role}")
    
    return user

def create_sample_data():
    """Create some sample plans and data for testing."""
    from authentication.models import Plan, UserPlanAssignment
    from datetime import datetime, timedelta
    
    print("\n🏗️  Creating sample data...")
    
    # Create some test companies with new predefined plans for testing
    test_companies = [
        {'plan_name': 'bronze', 'max_agents': 5, 'price': 2000, 'company_name': 'Bronze Test Corp'},
        {'plan_name': 'silver', 'max_agents': 10, 'price': 4000, 'company_name': 'Silver Test Corp'},
        {'plan_name': 'gold', 'max_agents': 20, 'price': 6000, 'company_name': 'Gold Test Corp'},
    ]
    
    created_plans = []
    for plan_data in test_companies:
        plan, created = Plan.objects.get_or_create(
            plan_name=plan_data['plan_name'],
            company_name=plan_data['company_name'],
            defaults={
                'max_agents': plan_data['max_agents'],
                'price': plan_data['price'],
                'expiry_date': datetime.now().date() + timedelta(days=365)
            }
        )
        if created:
            print(f"   ✅ Created test plan: {plan.plan_name}")
            created_plans.append(plan)
        else:
            print(f"   ℹ️  Test plan already exists: {plan.plan_name}")
    
    print(f"✅ Sample data setup complete ({len(created_plans)} new plans created)")

if __name__ == "__main__":
    print("🚀 Setting up test environment for Enhanced Plan Management System")
    print("=" * 70)
    
    try:
        # Create superadmin user
        superadmin = create_superadmin()
        
        # Create sample data
        create_sample_data()
        
        print("\n" + "=" * 70)
        print("✅ Test environment setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Make sure Django server is running: python manage.py runserver 8001")
        print("   2. Run API tests: python test_api_endpoints.py")
        print("   3. Test the React frontend")
        
    except Exception as e:
        print(f"\n💥 Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

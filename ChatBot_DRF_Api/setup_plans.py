#!/usr/bin/env python3
"""
Create required plans and test the upgrade system.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from authentication.models import Plan, User, UserPlanAssignment
from admin_dashboard.models import PlanUpgradeRequest

def create_plans():
    """Create the required plans if they don't exist."""
    plans_to_create = [
        {'plan_name': 'bronze', 'max_agents': 2, 'price': 2000.00},
        {'plan_name': 'silver', 'max_agents': 4, 'price': 4000.00},
        {'plan_name': 'gold', 'max_agents': 6, 'price': 6000.00},
        {'plan_name': 'platinum', 'max_agents': 10, 'price': 8000.00},
        {'plan_name': 'diamond', 'max_agents': 20, 'price': 10000.00},
    ]
    
    created_plans = []
    for plan_data in plans_to_create:
        # Check if plan exists, if multiple exist, use the first one
        existing_plans = Plan.objects.filter(plan_name=plan_data['plan_name'])
        
        if existing_plans.exists():
            print(f"ℹ️  {plan_data['plan_name']} plan already exists ({existing_plans.count()} found)")
        else:
            # Create new plan
            plan = Plan.objects.create(
                plan_name=plan_data['plan_name'],
                max_agents=plan_data['max_agents'],
                price=plan_data['price'],
                company_name=f"Standard {plan_data['plan_name'].title()} Plan",
                is_active=True
            )
            created_plans.append(plan.plan_name)
            print(f"✅ Created {plan.plan_name} plan")
    
    return created_plans

def check_system():
    """Check the current state of the system."""
    print("\n📊 System Status:")
    print(f"   Plans in database: {Plan.objects.count()}")
    print(f"   Upgrade requests: {PlanUpgradeRequest.objects.count()}")
    print(f"   Pending requests: {PlanUpgradeRequest.objects.filter(status='PENDING').count()}")
    
    print("\n📋 Available Plans:")
    for plan in Plan.objects.all():
        print(f"   - {plan.plan_name}: {plan.max_agents} agents, ₨{plan.price}")

if __name__ == "__main__":
    print("🚀 Setting up plan upgrade system...")
    
    create_plans()
    check_system()
    
    print("\n✅ Setup complete! You can now test the upgrade system.")

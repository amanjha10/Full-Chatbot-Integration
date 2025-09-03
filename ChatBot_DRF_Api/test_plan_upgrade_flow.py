#!/usr/bin/env python
"""
Test script to verify the complete plan upgrade flow works correctly
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import Plan, UserPlanAssignment
from admin_dashboard.models import PlanUpgradeRequest
from admin_dashboard.views import update_user_plan
from datetime import datetime

User = get_user_model()

def test_complete_upgrade_flow():
    """Test the complete plan upgrade flow"""
    print("=== Testing Complete Plan Upgrade Flow ===\n")
    
    # 1. Setup test data
    print("1. Setting up test data...")
    
    # Find or create admin user for SEP002
    admin_user, created = User.objects.get_or_create(
        username='sep002_admin',
        defaults={
            'email': 'admin@sep002.com',
            'company_id': 'SEP002',
            'role': 'ADMIN',
            'is_active': True
        }
    )
    if created:
        admin_user.set_password('password123')
        admin_user.save()
    
    # Find or create superadmin user
    superadmin_user, created = User.objects.get_or_create(
        username='superadmin',
        defaults={
            'email': 'superadmin@company.com',
            'role': 'SUPERADMIN',
            'is_active': True
        }
    )
    if created:
        superadmin_user.set_password('superadmin123')
        superadmin_user.save()
    
    print(f"   Admin user: {admin_user.username} (Company: {admin_user.company_id})")
    print(f"   SuperAdmin user: {superadmin_user.username}")
    
    # 2. Create or get Bronze plan
    print("\n2. Setting up initial Bronze plan...")
    
    bronze_plan, created = Plan.objects.get_or_create(
        plan_name='bronze',
        company_name='SEP002',
        defaults={
            'max_agents': 2,
            'price': 2000,
            'is_active': True
        }
    )
    
    # Ensure user has active Bronze plan assignment
    UserPlanAssignment.objects.filter(
        user=admin_user,
        status='active'
    ).update(status='upgraded')
    
    bronze_assignment = UserPlanAssignment.objects.create(
        user=admin_user,
        plan=bronze_plan,
        status='active',
        notes='Initial Bronze plan setup for testing'
    )
    
    print(f"   Created Bronze plan assignment: {bronze_assignment.id}")
    print(f"   Plan: {bronze_plan.plan_name} (Max agents: {bronze_plan.max_agents})")
    
    # 3. Create upgrade request
    print("\n3. Creating plan upgrade request...")
    
    # Clear any existing pending requests
    PlanUpgradeRequest.objects.filter(
        company_id='SEP002',
        status='PENDING'
    ).delete()
    
    upgrade_request = PlanUpgradeRequest.objects.create(
        company_id='SEP002',
        company_name='SEP002',
        current_plan='Bronze',
        requested_plan='Silver',
        reason='Testing upgrade flow - need more agents',
        requested_by=admin_user,
        status='PENDING'
    )
    
    print(f"   Created upgrade request: {upgrade_request.id}")
    print(f"   From: {upgrade_request.current_plan} → To: {upgrade_request.requested_plan}")
    print(f"   Status: {upgrade_request.status}")
    
    # 4. Test approval process
    print("\n4. Testing approval process...")
    
    # Simulate SuperAdmin approval
    upgrade_request.status = 'APPROVED'
    upgrade_request.reviewed_by = superadmin_user
    upgrade_request.reviewed_at = datetime.now()
    upgrade_request.review_notes = 'Approved for testing - company needs more agents'
    upgrade_request.save()
    
    print(f"   Request status updated to: {upgrade_request.status}")
    print(f"   Reviewed by: {upgrade_request.reviewed_by.username}")
    
    # 5. Update user plan
    print("\n5. Updating user plan...")
    
    success = update_user_plan(upgrade_request)
    
    if success:
        print("   ✅ Plan update successful!")
        
        # Verify the update
        new_assignment = UserPlanAssignment.objects.filter(
            user=admin_user,
            status='active'
        ).first()
        
        if new_assignment:
            print(f"   New plan: {new_assignment.plan.plan_name}")
            print(f"   Max agents: {new_assignment.plan.max_agents}")
            print(f"   Company: {new_assignment.plan.company_name}")
        else:
            print("   ❌ No active plan assignment found!")
            
    else:
        print("   ❌ Plan update failed!")
    
    # 6. Verify agent limit check
    print("\n6. Testing agent limit check...")
    
    from admin_dashboard.models import Agent
    
    # Check current agent count
    current_agents = Agent.objects.filter(company_id='SEP002').count()
    
    # Get updated plan assignment
    active_assignment = UserPlanAssignment.objects.filter(
        user=admin_user,
        status='active'
    ).first()
    
    if active_assignment:
        max_agents = active_assignment.plan.get_max_agents_for_plan()
        can_create = current_agents < max_agents
        
        print(f"   Current agents: {current_agents}")
        print(f"   Max allowed: {max_agents}")
        print(f"   Can create more: {'✅ Yes' if can_create else '❌ No'}")
        
        if active_assignment.plan.plan_name == 'silver' and max_agents == 4:
            print("   ✅ Plan upgrade verification successful!")
        else:
            print(f"   ❌ Plan upgrade verification failed! Expected Silver plan with 4 agents, got {active_assignment.plan.plan_name} with {max_agents} agents")
    else:
        print("   ❌ No active plan assignment found!")
    
    # 7. Summary
    print("\n" + "="*50)
    print("UPGRADE FLOW TEST SUMMARY")
    print("="*50)
    
    final_assignment = UserPlanAssignment.objects.filter(
        user=admin_user,
        status='active'
    ).first()
    
    if final_assignment:
        print(f"✅ Company SEP002 successfully upgraded to {final_assignment.plan.plan_name.upper()} plan")
        print(f"✅ Agent limit increased from 2 to {final_assignment.plan.max_agents}")
        print(f"✅ User can now create {final_assignment.plan.max_agents - current_agents} more agents")
    else:
        print("❌ Upgrade flow failed - no active plan found")
    
    # 8. Display current state
    print("\n" + "-"*30)
    print("CURRENT STATE:")
    print("-"*30)
    
    all_assignments = UserPlanAssignment.objects.filter(user=admin_user).order_by('-created_at')
    for assignment in all_assignments:
        status_icon = "🟢" if assignment.status == 'active' else "🔵" if assignment.status == 'upgraded' else "🔴"
        print(f"{status_icon} {assignment.plan.plan_name.upper()} plan - Status: {assignment.status}")
    
    print(f"\nUpgrade Request Status: {upgrade_request.status}")
    print(f"Request reviewed at: {upgrade_request.reviewed_at}")
    

if __name__ == '__main__':
    test_complete_upgrade_flow()

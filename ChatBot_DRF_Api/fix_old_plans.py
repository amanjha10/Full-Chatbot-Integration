#!/usr/bin/env python
"""Script to fix old plan entries and update legacy plans."""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from authentication.models import Plan, User, UserPlanAssignment

def fix_old_plans():
    """Fix old plan entries and update legacy plans."""
    
    print("=== Plan Cleanup and Update ===")
    
    # 1. List all plans and their types
    print("\n1. Current Plans in Database:")
    all_plans = Plan.objects.all()
    for plan in all_plans:
        print(f"   ID: {plan.id}, Name: {plan.plan_name}, Display: {plan.plan_name_display}, Company: {plan.company_name}, Price: {plan.price}")
    
    # 2. Find and update legacy plans (basic, pro, premium)
    print("\n2. Updating Legacy Plans:")
    legacy_plans = Plan.objects.filter(plan_name__in=['basic', 'pro', 'premium'])
    
    plan_mapping = {
        'basic': 'bronze',
        'pro': 'silver', 
        'premium': 'gold'
    }
    
    updated_count = 0
    for plan in legacy_plans:
        old_name = plan.plan_name
        new_name = plan_mapping.get(old_name)
        if new_name:
            plan.plan_name = new_name
            plan.save()
            print(f"   Updated plan {plan.id}: {old_name} -> {new_name}")
            updated_count += 1
    
    print(f"   Total legacy plans updated: {updated_count}")
    
    # 3. Check for users with problematic data
    print("\n3. Checking Users with Plan Issues:")
    problematic_users = []
    all_users = User.objects.filter(role='ADMIN')
    
    for user in all_users:
        assignments = user.plan_assignments.all()
        if assignments.exists():
            for assignment in assignments:
                plan_display = assignment.plan.plan_name_display
                if plan_display.isdigit() or len(plan_display) < 3:
                    problematic_users.append({
                        'user': user,
                        'assignment': assignment,
                        'issue': f'Bad plan display: {plan_display}'
                    })
    
    if problematic_users:
        print(f"   Found {len(problematic_users)} users with plan display issues:")
        for item in problematic_users:
            user = item['user']
            assignment = item['assignment']
            print(f"     User: {user.name} ({user.company_id})")
            print(f"     Plan ID: {assignment.plan.id}, Name: {assignment.plan.plan_name}, Display: '{assignment.plan.plan_name_display}'")
            print(f"     Issue: {item['issue']}")
    else:
        print("   No users with plan display issues found.")
    
    # 4. Check assignments that might need status updates
    print("\n4. Checking Assignment Statuses:")
    assignments = UserPlanAssignment.objects.all()
    status_counts = {}
    for assignment in assignments:
        status = assignment.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("   Status distribution:")
    for status, count in status_counts.items():
        print(f"     {status}: {count}")
    
    print("\n=== Cleanup Complete ===")

if __name__ == '__main__':
    fix_old_plans()

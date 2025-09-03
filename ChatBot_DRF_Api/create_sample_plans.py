#!/usr/bin/env python
"""
Script to create sample plans with different dates for testing filters
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django
sys.path.append('/mnt/c/Users/Spell Developer/Desktop/New folder (2)/ChatBot_DRF_Api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from authentication.models import Plan

def create_sample_plans():
    """Create sample plans with different creation dates for testing"""
    
    # Sample data with different dates
    sample_plans = [
        {
            "plan_name": "basic",
            "company_name": "TestCorp Alpha",
            "max_agents": 3,
            "price": 49.99,
            "days_ago": 30,  # 30 days ago
            "expiry_days": 365
        },
        {
            "plan_name": "pro", 
            "company_name": "TestCorp Beta",
            "max_agents": 8,
            "price": 149.99,
            "days_ago": 15,  # 15 days ago
            "expiry_days": 730
        },
        {
            "plan_name": "premium",
            "company_name": "TestCorp Gamma", 
            "max_agents": 20,
            "price": 299.99,
            "days_ago": 7,   # 7 days ago
            "expiry_days": 365
        },
        {
            "plan_name": "basic",
            "company_name": "TestCorp Delta",
            "max_agents": 5,
            "price": 79.99,
            "days_ago": 60,  # 60 days ago
            "expiry_days": 180
        },
        {
            "plan_name": "pro",
            "company_name": "TestCorp Echo",
            "max_agents": 12,
            "price": 199.99,
            "days_ago": 90,  # 90 days ago
            "expiry_days": 540
        }
    ]
    
    for plan_data in sample_plans:
        # Calculate creation date
        created_date = datetime.now() - timedelta(days=plan_data["days_ago"])
        
        # Calculate expiry date
        expiry_date = created_date.date() + timedelta(days=plan_data["expiry_days"])
        
        plan = Plan.objects.create(
            plan_name=plan_data["plan_name"],
            company_name=plan_data["company_name"],
            max_agents=plan_data["max_agents"],
            price=plan_data["price"],
            expiry_date=expiry_date
        )
        
        # Update created_at to the calculated date
        plan.created_at = created_date
        plan.save()
        
        print(f"Created Plan {plan.id}: {plan_data['company_name']} - Created: {created_date.date()} - Expiry: {expiry_date}")
    
    print("Sample plans created successfully!")

if __name__ == "__main__":
    create_sample_plans()

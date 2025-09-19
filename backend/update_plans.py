#!/usr/bin/env python
"""
Script to update existing plans with random company names and expiry dates
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

# Random company names
company_names = [
    "Spell Technologies",
    "InnovateCorp",
    "TechVision Ltd",
    "Digital Solutions Inc",
    "CloudWorks",
    "DataFlow Systems",
    "NextGen Software",
    "SmartBiz Solutions",
    "CyberTech Industries",
    "FutureLogic Corp",
    "TechPro Solutions",
    "Quantum Systems",
    "ElevateIT",
    "TechSphere Inc",
    "InnovateHub"
]

def update_plans():
    """Update existing plans with random company names and expiry dates"""
    plans = Plan.objects.filter(company_name="Default Company")
    
    print(f"Found {plans.count()} plans with 'Default Company'")
    
    for i, plan in enumerate(plans):
        # Assign random company name
        company_name = random.choice(company_names)
        
        # Generate random expiry date (between 6 months to 2 years from creation)
        days_from_creation = random.randint(180, 730)  # 6 months to 2 years
        expiry_date = plan.created_at.date() + timedelta(days=days_from_creation)
        
        plan.company_name = company_name
        plan.expiry_date = expiry_date
        plan.save()
        
        print(f"Updated Plan {plan.id}: {company_name} - Expiry: {expiry_date}")
    
    print("Update completed!")

if __name__ == "__main__":
    update_plans()

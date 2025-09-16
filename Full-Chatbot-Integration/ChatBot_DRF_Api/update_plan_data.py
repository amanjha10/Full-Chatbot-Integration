#!/usr/bin/env python3
"""
Update plan data with correct values according to requirements
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from chatbot.models import Plan, PlanFeature

def update_plan_data():
    """Update existing plans with correct data"""
    
    # Plan data according to requirements
    plans_data = [
        {
            'name': 'Bronze',
            'icon': '🥉',
            'price': 2000.00,
            'subtitle': 'Small Companies',
            'max_agents': '2',
            'features_line': 'AI-powered Chatbot',
            'gradient': 'from-amber-800 via-yellow-600 to-amber-900',
            'text_color': 'text-black',
            'border_color': 'border-amber-400',
            'button_color': 'bg-amber-600 hover:bg-amber-700',
            'shine_color': 'rgba(255, 215, 0, 0.8)',
            'sort_order': 1
        },
        {
            'name': 'Silver',
            'icon': '🥈',
            'price': 4000.00,
            'subtitle': 'Growing Businesses',
            'max_agents': '4',
            'features_line': 'Advanced AI Chatbot with Full RAG',
            'gradient': 'from-gray-600 via-gray-400 to-gray-700',
            'text_color': 'text-black',
            'border_color': 'border-gray-300',
            'button_color': 'bg-gray-500 hover:bg-gray-600',
            'shine_color': 'rgba(192, 192, 192, 0.8)',
            'sort_order': 2
        },
        {
            'name': 'Gold',
            'icon': '🥇',
            'price': 6000.00,
            'subtitle': 'Medium Enterprises',
            'max_agents': '6',
            'features_line': 'Premium AI Chatbot + Analytics + Customization',
            'gradient': 'from-yellow-600 via-yellow-400 to-yellow-700',
            'text_color': 'text-black',
            'border_color': 'border-yellow-300',
            'button_color': 'bg-yellow-500 hover:bg-yellow-600',
            'shine_color': 'rgba(255, 215, 0, 0.9)',
            'sort_order': 3
        },
        {
            'name': 'Platinum',
            'icon': '💎',
            'price': 8000.00,
            'subtitle': 'Large Enterprises',
            'max_agents': '8',
            'features_line': 'Enterprise Chatbot + Dedicated Support',
            'gradient': 'from-purple-800 via-purple-600 to-purple-900',
            'text_color': 'text-white',
            'border_color': 'border-purple-400',
            'button_color': 'bg-purple-600 hover:bg-purple-700',
            'shine_color': 'rgba(147, 51, 234, 0.8)',
            'sort_order': 4
        },
        {
            'name': 'Diamond',
            'icon': '💠',
            'price': 10000.00,
            'subtitle': 'Corporates & Enterprises',
            'max_agents': '10',
            'features_line': 'Custom AI Solution + White-label + SLA',
            'gradient': 'from-cyan-600 via-blue-500 to-cyan-700',
            'text_color': 'text-white',
            'border_color': 'border-cyan-300',
            'button_color': 'bg-cyan-500 hover:bg-cyan-600',
            'shine_color': 'rgba(6, 182, 212, 0.8)',
            'sort_order': 5
        },
        {
            'name': 'Custom',
            'icon': '⚙️',
            'price': None,  # Custom pricing
            'subtitle': 'Enterprises',
            'max_agents': 'According to your needs',
            'features_line': 'AI-powered Chatbot',
            'gradient': 'from-indigo-800 via-indigo-600 to-indigo-900',
            'text_color': 'text-white',
            'border_color': 'border-indigo-400',
            'button_color': 'bg-indigo-600 hover:bg-indigo-700',
            'shine_color': 'rgba(99, 102, 241, 0.8)',
            'sort_order': 6
        }
    ]
    
    print("🔄 Updating plan data...")
    
    for plan_data in plans_data:
        plan, created = Plan.objects.update_or_create(
            name=plan_data['name'],
            defaults=plan_data
        )
        
        if created:
            print(f"✅ Created plan: {plan.name}")
        else:
            print(f"🔄 Updated plan: {plan.name}")
    
    print(f"\n📊 Total plans: {Plan.objects.count()}")
    
    # Create company plan for SPE001 user
    from chatbot.models import CompanyPlan
    
    try:
        silver_plan = Plan.objects.get(name='Silver')
        company_plan, created = CompanyPlan.objects.update_or_create(
            company_id='SPE001',
            defaults={
                'current_plan': silver_plan,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created company plan for SPE001: {silver_plan.name}")
        else:
            print(f"🔄 Updated company plan for SPE001: {silver_plan.name}")
            
    except Plan.DoesNotExist:
        print("❌ Silver plan not found")

if __name__ == "__main__":
    update_plan_data()
    print("✅ Plan data update completed!")

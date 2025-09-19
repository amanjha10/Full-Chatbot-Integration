from django.core.management.base import BaseCommand
from chatbot.models import Plan, PlanFeature


class Command(BaseCommand):
    help = 'Populate initial plan data'

    def handle(self, *args, **options):
        self.stdout.write('Creating plans...')
        
        # Bronze Plan
        bronze_plan, created = Plan.objects.get_or_create(
            name='Bronze',
            defaults={
                'icon': '',
                'price': 2000.00,
                'subtitle': 'Basic Plan',
                'max_agents': '2',
                'gradient': 'from-amber-800 via-yellow-600 to-amber-900',
                'text_color': 'text-black',
                'border_color': 'border-amber-400',
                'button_color': 'bg-amber-600 hover:bg-amber-700',
                'shine_color': 'rgba(255, 215, 0, 0.8)',
                'sort_order': 1
            }
        )
        
        if created:
            # Bronze features
            bronze_features = [
                'Basic chatbot (FAQ + RAG-lite)',
                'Up to 2 agents',
                'Email support',
                'Basic analytics',
                'Standard response time'
            ]
            
            for i, feature_text in enumerate(bronze_features):
                PlanFeature.objects.create(
                    plan=bronze_plan,
                    text=feature_text,
                    included=True,
                    sort_order=i
                )
        
        # Silver Plan
        silver_plan, created = Plan.objects.get_or_create(
            name='Silver',
            defaults={
                'icon': '',
                'price': 4000.00,
                'subtitle': 'Professional Plan',
                'max_agents': '4',
                'gradient': 'from-gray-600 via-gray-400 to-gray-700',
                'text_color': 'text-black',
                'border_color': 'border-gray-300',
                'button_color': 'bg-gray-500 hover:bg-gray-600',
                'shine_color': 'rgba(192, 192, 192, 0.8)',
                'sort_order': 2
            }
        )
        
        if created:
            # Silver features
            silver_features = [
                'Advanced chatbot (FAQ + Full RAG)',
                'Up to 4 agents',
                'Priority email support',
                'Advanced analytics',
                'Custom branding',
                'API access'
            ]
            
            for i, feature_text in enumerate(silver_features):
                PlanFeature.objects.create(
                    plan=silver_plan,
                    text=feature_text,
                    included=True,
                    sort_order=i
                )
        
        # Gold Plan
        gold_plan, created = Plan.objects.get_or_create(
            name='Gold',
            defaults={
                'icon': '',
                'price': 6000.00,
                'subtitle': 'Premium Plan',
                'max_agents': '6',
                'gradient': 'from-yellow-600 via-yellow-400 to-yellow-700',
                'text_color': 'text-black',
                'border_color': 'border-yellow-300',
                'button_color': 'bg-yellow-500 hover:bg-yellow-600',
                'shine_color': 'rgba(255, 215, 0, 0.9)',
                'sort_order': 3
            }
        )
        
        if created:
            # Gold features
            gold_features = [
                'Premium chatbot (FAQ + RAG + AI)',
                'Up to 6 agents',
                'Phone & email support',
                'Premium analytics',
                'Full customization',
                'API access',
                'Priority support'
            ]
            
            for i, feature_text in enumerate(gold_features):
                PlanFeature.objects.create(
                    plan=gold_plan,
                    text=feature_text,
                    included=True,
                    sort_order=i
                )
        
        # Platinum Plan
        platinum_plan, created = Plan.objects.get_or_create(
            name='Platinum',
            defaults={
                'icon': '',
                'price': 8000.00,
                'subtitle': 'Enterprise Plan',
                'max_agents': '8',
                'gradient': 'from-purple-800 via-purple-600 to-purple-900',
                'text_color': 'text-white',
                'border_color': 'border-purple-400',
                'button_color': 'bg-purple-600 hover:bg-purple-700',
                'shine_color': 'rgba(147, 51, 234, 0.8)',
                'sort_order': 4
            }
        )
        
        if created:
            # Platinum features
            platinum_features = [
                'Enterprise chatbot (Full AI Suite)',
                'Up to 8 agents',
                '24/7 dedicated support',
                'Enterprise analytics',
                'White-label solution',
                'Full API access',
                'Custom integrations',
                'SLA guarantee'
            ]
            
            for i, feature_text in enumerate(platinum_features):
                PlanFeature.objects.create(
                    plan=platinum_plan,
                    text=feature_text,
                    included=True,
                    sort_order=i
                )
        
        # Diamond Plan
        diamond_plan, created = Plan.objects.get_or_create(
            name='Diamond',
            defaults={
                'icon': '',
                'price': 10000.00,
                'subtitle': 'Custom Enterprise',
                'max_agents': '10',
                'gradient': 'from-cyan-600 via-blue-500 to-cyan-700',
                'text_color': 'text-white',
                'border_color': 'border-cyan-300',
                'button_color': 'bg-cyan-500 hover:bg-cyan-600',
                'shine_color': 'rgba(6, 182, 212, 0.8)',
                'sort_order': 5
            }
        )
        
        if created:
            # Diamond features
            diamond_features = [
                'Custom AI solution',
                'Up to 10 agents',
                'Dedicated account manager',
                'Custom analytics dashboard',
                'Complete white-label',
                'Custom development',
                'On-premise deployment',
                'Enterprise SLA'
            ]
            
            for i, feature_text in enumerate(diamond_features):
                PlanFeature.objects.create(
                    plan=diamond_plan,
                    text=feature_text,
                    included=True,
                    sort_order=i
                )
        
        # Enterprise Plan (Custom)
        enterprise_plan, created = Plan.objects.get_or_create(
            name='Custom',
            defaults={
                'icon': '',
                'price': None,  # Custom pricing
                'subtitle': 'Large Scale Solution',
                'max_agents': 'Unlimited',
                'gradient': 'from-indigo-800 via-indigo-600 to-indigo-900',
                'text_color': 'text-white',
                'border_color': 'border-indigo-400',
                'button_color': 'bg-indigo-600 hover:bg-indigo-700',
                'shine_color': 'rgba(99, 102, 241, 0.8)',
                'sort_order': 6
            }
        )
        
        if created:
            # Enterprise features
            enterprise_features = [
                'Multi-tenant architecture',
                'Unlimited agents & companies',
                'Enterprise support',
                'Advanced security',
                'Custom deployment',
                'Integration suite',
                'Training & onboarding',
                'Success manager'
            ]
            
            for i, feature_text in enumerate(enterprise_features):
                PlanFeature.objects.create(
                    plan=enterprise_plan,
                    text=feature_text,
                    included=True,
                    sort_order=i
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created all plans with features!')
        )

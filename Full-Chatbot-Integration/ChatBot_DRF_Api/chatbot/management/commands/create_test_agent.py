from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin_dashboard.models import Agent

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a test agent for chatbot handoff testing'

    def handle(self, *args, **options):
        # Create a test agent if one doesn't exist
        user, user_created = User.objects.get_or_create(
            username='test_agent',
            defaults={
                'email': 'agent@test.com',
                'first_name': 'Test',
                'last_name': 'Agent',
                'role': 'AGENT'
            }
        )
        
        if user_created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f"✅ Created test user: {user.username}")
        else:
            self.stdout.write(f"ℹ️  Test user already exists: {user.username}")

        agent, agent_created = Agent.objects.get_or_create(
            user=user,
            defaults={
                'is_active': True,
                'company_id': 'TEST001'
            }
        )

        if agent_created:
            self.stdout.write(f"✅ Created test agent: ID={agent.id}")
        else:
            self.stdout.write(f"ℹ️  Test agent already exists: ID={agent.id}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Test agent ready - Username: {user.username}, Password: testpass123, Agent ID: {agent.id}"
            )
        )

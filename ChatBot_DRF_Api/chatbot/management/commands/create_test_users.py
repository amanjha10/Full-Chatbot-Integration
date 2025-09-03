from django.core.management.base import BaseCommand
from chatbot.models import UserProfile
from datetime import datetime, timedelta
import uuid

class Command(BaseCommand):
    help = 'Create test user profiles for TEST001 company'

    def handle(self, *args, **options):
        # Clear existing data
        UserProfile.objects.filter(company_id="TEST001").delete()
        
        # Create test users
        users = [
            {"name": "John Doe", "phone": "1234567890", "email": "john@example.com", "address": "123 Main St", "is_favorite": True},
            {"name": "Jane Smith", "phone": "9876543210", "email": "jane@example.com", "address": "456 Oak Ave", "is_favorite": False},
            {"name": "Mike Johnson", "phone": "5555555555", "email": None, "address": "789 Pine Rd", "is_favorite": True},
            {"name": "Sarah Wilson", "phone": "7777777777", "email": "sarah@example.com", "address": None, "is_favorite": False},
            {"name": "David Brown", "phone": "3333333333", "email": None, "address": "321 Elm St", "is_favorite": False},
        ]

        for i, user_data in enumerate(users):
            UserProfile.objects.create(
                session_id=str(uuid.uuid4()),
                persistent_user_id=str(uuid.uuid4()),
                name=user_data["name"],
                phone=user_data["phone"],
                email=user_data["email"],
                address=user_data["address"],
                country_code="+1",
                company_id="TEST001",
                is_favorite=user_data["is_favorite"],
                last_used=datetime.now() - timedelta(days=i+1)
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(users)} test users for TEST001')
        )

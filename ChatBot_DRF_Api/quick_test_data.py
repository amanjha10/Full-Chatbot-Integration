import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from chatbot.models import UserProfile
from datetime import datetime, timedelta
import uuid

# Clear existing data
UserProfile.objects.filter(company_id="TEST001").delete()

# Create test users
users = [
    {"name": "John Doe", "phone": "1234567890", "email": "john@example.com", "address": "123 Main St", "is_favorite": True},
    {"name": "Jane Smith", "phone": "9876543210", "email": "jane@example.com", "address": "456 Oak Ave", "is_favorite": False},
    {"name": "Mike Johnson", "phone": "5555555555", "email": None, "address": "789 Pine Rd", "is_favorite": True},
    {"name": "Sarah Wilson", "phone": "7777777777", "email": "sarah@example.com", "address": None, "is_favorite": False},
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

print(f"Created {len(users)} test users for TEST001")
print(f"Total users: {UserProfile.objects.filter(company_id='TEST001').count()}")

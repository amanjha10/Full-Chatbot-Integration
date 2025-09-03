#!/usr/bin/env python3
"""
Create test data for the chatbot system
"""
import os
import sys
import django
from datetime import datetime, timedelta
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from authentication.models import User
from chatbot.models import UserProfile, ChatbotConfiguration
from admin_dashboard.models import Agent

def create_test_users():
    """Create test user profiles"""
    print("Creating test user profiles...")
    
    # Clear existing test data
    UserProfile.objects.filter(company_id="TEST001").delete()
    
    users_data = [
        {"name": "John Doe", "phone": "1234567890", "email": "john@example.com", "address": "123 Main St, New York", "is_favorite": True},
        {"name": "Jane Smith", "phone": "9876543210", "email": "jane@example.com", "address": "456 Oak Ave, Los Angeles", "is_favorite": False},
        {"name": "Mike Johnson", "phone": "5555555555", "email": None, "address": "789 Pine Rd, Chicago", "is_favorite": True},
        {"name": "Sarah Wilson", "phone": "7777777777", "email": "sarah@example.com", "address": None, "is_favorite": False},
        {"name": "David Brown", "phone": "3333333333", "email": None, "address": "321 Elm St, Houston", "is_favorite": False},
        {"name": "Lisa Davis", "phone": "8888888888", "email": "lisa@example.com", "address": "654 Maple Dr, Phoenix", "is_favorite": True},
        {"name": "Tom Anderson", "phone": "2222222222", "email": None, "address": None, "is_favorite": False},
        {"name": "Emma Taylor", "phone": "6666666666", "email": "emma@example.com", "address": "987 Cedar Ln, Philadelphia", "is_favorite": True}
    ]
    
    created_count = 0
    for i, user_data in enumerate(users_data):
        last_used = datetime.now() - timedelta(days=i+1, hours=i*2)
        
        profile = UserProfile.objects.create(
            session_id=str(uuid.uuid4()),
            persistent_user_id=str(uuid.uuid4()),
            name=user_data["name"],
            phone=user_data["phone"],
            email=user_data["email"],
            address=user_data["address"],
            country_code="+1",
            company_id="TEST001",
            is_favorite=user_data["is_favorite"],
            last_used=last_used
        )
        created_count += 1
        print(f"Created: {profile.name} - {profile.email or 'No email'}")
    
    print(f"✅ Created {created_count} test user profiles")
    return created_count

def create_admin_user():
    """Create or update admin user"""
    print("Creating/updating admin user...")
    
    try:
        admin = User.objects.get(username='admin@test.com')
        print(f"✅ Admin user exists: {admin.username} - Role: {admin.role} - Company: {admin.company_id}")
    except User.DoesNotExist:
        admin = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='admin123',
            role='ADMIN',
            name='Test Admin',
            company_id='TEST001'
        )
        print(f"✅ Created admin user: {admin.username}")
    
    return admin

def create_chatbot_config():
    """Create or update chatbot configuration"""
    print("Creating/updating chatbot configuration...")
    
    config, created = ChatbotConfiguration.objects.get_or_create(
        company_id="TEST001",
        defaults={
            'primary_color': '#f7941d',
            'secondary_color': '#652d90',
            'position': 'bottom-right',
            'iframe_width': 400,
            'iframe_height': 600,
            'welcome_message': 'Hello! How can I help you today?',
            'company_name': 'Test Company',
            'enable_file_upload': True,
            'enable_voice_messages': False,
            'enable_typing_indicator': True
        }
    )
    
    if created:
        print("✅ Created new chatbot configuration")
    else:
        print("✅ Chatbot configuration already exists")
    
    return config

def verify_data():
    """Verify the created data"""
    print("\n🔍 Verifying created data...")
    
    # Check user profiles
    profile_count = UserProfile.objects.filter(company_id="TEST001").count()
    favorite_count = UserProfile.objects.filter(company_id="TEST001", is_favorite=True).count()
    print(f"User Profiles (TEST001): {profile_count} total, {favorite_count} favorites")
    
    # Check admin user
    try:
        admin = User.objects.get(username='admin@test.com')
        print(f"Admin User: {admin.username} - Role: {admin.role} - Company: {admin.company_id}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
    
    # Check configuration
    try:
        config = ChatbotConfiguration.objects.get(company_id='TEST001')
        print(f"Configuration: {config.primary_color} - {config.position}")
    except ChatbotConfiguration.DoesNotExist:
        print("❌ Configuration not found")
    
    print("\n✅ Data verification complete!")

def main():
    """Main function"""
    print("🚀 Creating test data for chatbot system...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Create test data
        admin = create_admin_user()
        config = create_chatbot_config()
        user_count = create_test_users()
        
        # Verify data
        verify_data()
        
        print(f"\n🎉 Test data creation completed successfully!")
        print(f"- Admin user: admin@test.com / admin123")
        print(f"- User profiles: {user_count} created")
        print(f"- Company ID: TEST001")
        print(f"- Configuration: Ready")
        
        print(f"\n🎯 Next steps:")
        print(f"1. Login to admin dashboard: http://localhost:5173/login")
        print(f"2. Check user management: http://localhost:5173/app/user-management")
        print(f"3. Test chatbot settings: http://localhost:5173/app/settings")
        print(f"4. Test chatbot widget: http://localhost:8080/hello.html")
        
    except Exception as e:
        print(f"\n❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

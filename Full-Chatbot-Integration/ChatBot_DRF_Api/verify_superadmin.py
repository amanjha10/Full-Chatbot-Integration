#!/usr/bin/env python3
"""
🔍 SUPERADMIN VERIFICATION SCRIPT
================================

This script verifies that the SuperAdmin exists before running cleanup.
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from authentication.models import User

def verify_superadmin():
    """Verify SuperAdmin exists and show details"""
    print("🔍 Checking SuperAdmin status...")
    
    try:
        superadmin = User.objects.get(username='superadmin', role=User.Role.SUPERADMIN)
        print("✅ SuperAdmin found!")
        print(f"   Username: {superadmin.username}")
        print(f"   Role: {superadmin.role}")
        print(f"   Email: {superadmin.email}")
        print(f"   Active: {superadmin.is_active}")
        print(f"   Staff: {superadmin.is_staff}")
        print(f"   Superuser: {superadmin.is_superuser}")
        return True
    except User.DoesNotExist:
        print("❌ SuperAdmin not found!")
        print("   Expected: username='superadmin', role='SUPERADMIN'")
        return False

def show_all_users():
    """Show all users in the system"""
    print("\n📊 All users in system:")
    users = User.objects.all()
    if users.exists():
        for user in users:
            print(f"   - {user.username} ({user.role}) - Active: {user.is_active}")
    else:
        print("   No users found")

def main():
    """Main function"""
    print("=" * 50)
    print("🔍 SUPERADMIN VERIFICATION")
    print("=" * 50)
    
    if verify_superadmin():
        print("\n✅ SuperAdmin verification successful!")
        print("✅ Safe to proceed with database cleanup")
    else:
        print("\n❌ SuperAdmin verification failed!")
        print("❌ DO NOT proceed with database cleanup")
        show_all_users()
        
        print("\n💡 To create SuperAdmin:")
        print("   python manage.py createsuperuser")
        print("   Username: superadmin")
        print("   Password: superadmin123")

if __name__ == "__main__":
    main()

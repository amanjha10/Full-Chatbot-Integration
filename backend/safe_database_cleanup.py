#!/usr/bin/env python3
"""
🧹 SAFE DATABASE CLEANUP SCRIPT
===============================

This script safely cleans the database while preserving essential data:

KEEPS:
✅ SuperAdmin user (username: superadmin)
✅ Plan models (subscription plans)
✅ RAG Documents (knowledge base)
✅ Django system tables

DELETES:
🗑️ All Admin users and companies
🗑️ All Agents and sessions
🗑️ All chat sessions and user profiles
🗑️ All handoff sessions
🗑️ All uploaded files and media
🗑️ All plan assignments

⚠️  IMPORTANT: This action is IRREVERSIBLE!
"""

import os
import sys
import django
import shutil
from pathlib import Path

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from authentication.models import User

# Import models with error handling
try:
    from admin_dashboard.models import Agent, AgentSession, PlanUpgradeRequest
except ImportError as e:
    print(f"⚠️ Warning: Could not import admin_dashboard models: {e}")
    Agent = AgentSession = PlanUpgradeRequest = None

try:
    from chatbot.models import ChatSession, UserProfile, ChatMessage, UploadedFile, ChatFile
except ImportError as e:
    print(f"⚠️ Warning: Could not import chatbot models: {e}")
    ChatSession = UserProfile = ChatMessage = UploadedFile = ChatFile = None

try:
    from human_handoff.models import HandoffSession, HumanHandoffSession, AgentActivity
except ImportError as e:
    print(f"⚠️ Warning: Could not import human_handoff models: {e}")
    HandoffSession = HumanHandoffSession = AgentActivity = None

def print_banner():
    """Print warning banner"""
    print("=" * 80)
    print("🧹 SAFE DATABASE CLEANUP SCRIPT")
    print("=" * 80)
    print("⚠️  WARNING: This will DELETE most data from the database!")
    print("⚠️  This action is IRREVERSIBLE!")
    print()
    print("WILL KEEP:")
    print("✅ SuperAdmin user (username: superadmin)")
    print("✅ Plan models (subscription plans)")
    print("✅ RAG Documents (knowledge base)")
    print("✅ Django system tables")
    print()
    print("WILL DELETE:")
    print("🗑️ All Admin users and companies")
    print("🗑️ All Agents and sessions")
    print("🗑️ All chat sessions and user profiles")
    print("🗑️ All handoff sessions")
    print("🗑️ All uploaded files and media")
    print("🗑️ All plan assignments")
    print("=" * 80)

def get_confirmation():
    """Get user confirmation"""
    print("\n🔍 Current database status:")

    # Count current data
    admin_count = User.objects.filter(role=User.Role.ADMIN).count()
    agent_count = safe_count_model(Agent, "agents")
    chat_sessions = safe_count_model(ChatSession, "chat sessions")
    user_profiles = safe_count_model(UserProfile, "user profiles")
    handoff_sessions = safe_count_model(HandoffSession, "handoff sessions")

    print(f"📊 Admin users: {admin_count}")
    print(f"📊 Agents: {agent_count}")
    print(f"📊 Chat sessions: {chat_sessions}")
    print(f"📊 User profiles: {user_profiles}")
    print(f"📊 Handoff sessions: {handoff_sessions}")
    
    print("\n" + "=" * 50)
    print("⚠️  ARE YOU ABSOLUTELY SURE?")
    print("⚠️  This will DELETE all the data shown above!")
    print("⚠️  Only the SuperAdmin will remain!")
    print("=" * 50)
    
    response = input("\nType 'DELETE ALL DATA' to confirm (case sensitive): ")
    return response == "DELETE ALL DATA"

def verify_superadmin():
    """Verify SuperAdmin exists"""
    try:
        superadmin = User.objects.get(username='superadmin', role=User.Role.SUPERADMIN)
        print(f"✅ SuperAdmin found: {superadmin.username}")
        return True
    except User.DoesNotExist:
        print("❌ SuperAdmin not found! Cannot proceed safely.")
        print("   Please ensure SuperAdmin exists with username 'superadmin'")
        return False

def cleanup_media_files():
    """Clean up media files"""
    print("\n🧹 Cleaning media files...")
    
    media_root = Path('media')
    if media_root.exists():
        try:
            # Remove all subdirectories in media
            for item in media_root.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"🗑️ Removed media directory: {item}")
                elif item.is_file() and item.name != '.gitkeep':
                    item.unlink()
                    print(f"🗑️ Removed media file: {item}")
            print("✅ Media files cleaned")
        except Exception as e:
            print(f"⚠️ Error cleaning media files: {e}")
    else:
        print("ℹ️ No media directory found")

def safe_delete_model(model, model_name):
    """Safely delete all objects from a model"""
    if model is None:
        print(f"⚠️ Skipping {model_name} (model not available)")
        return 0

    try:
        count = model.objects.count()
        if count > 0:
            model.objects.all().delete()
            print(f"🗑️ Deleted {count} {model_name}")
            return count
        else:
            print(f"ℹ️ No {model_name} to delete")
            return 0
    except Exception as e:
        print(f"⚠️ Error deleting {model_name}: {e}")
        return 0

def cleanup_database():
    """Perform database cleanup"""
    print("\n🧹 Starting database cleanup...")

    try:
        with transaction.atomic():
            # 1. Delete Agent Activities
            safe_delete_model(AgentActivity, "agent activities")

            # 2. Delete Handoff Sessions
            safe_delete_model(HandoffSession, "handoff sessions")
            safe_delete_model(HumanHandoffSession, "human handoff sessions")

            # 3. Delete Chat Files and Uploaded Files
            safe_delete_model(ChatFile, "chat files")
            safe_delete_model(UploadedFile, "uploaded files")

            # 4. Delete Chat Messages
            safe_delete_model(ChatMessage, "chat messages")

            # 5. Delete Chat Sessions
            safe_delete_model(ChatSession, "chat sessions")

            # 6. Delete User Profiles
            safe_delete_model(UserProfile, "user profiles")

            # 7. Delete Plan Upgrade Requests
            safe_delete_model(PlanUpgradeRequest, "plan upgrade requests")

            # 8. Delete Agent Sessions
            safe_delete_model(AgentSession, "agent sessions")

            # 9. Delete Agents
            safe_delete_model(Agent, "agents")
            
            # 10. Delete Admin Users (keep SuperAdmin)
            admin_users = User.objects.filter(role=User.Role.ADMIN)
            count = admin_users.count()
            if count > 0:
                admin_users.delete()
                print(f"🗑️ Deleted {count} admin users")
            
            # 11. Delete Agent Users (keep SuperAdmin)
            agent_users = User.objects.filter(role=User.Role.AGENT)
            count = agent_users.count()
            if count > 0:
                agent_users.delete()
                print(f"🗑️ Deleted {count} agent users")
            
            print("✅ Database cleanup completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during database cleanup: {e}")
        raise

def safe_count_model(model, model_name):
    """Safely count objects in a model"""
    if model is None:
        return 0
    try:
        return model.objects.count()
    except Exception as e:
        print(f"⚠️ Error counting {model_name}: {e}")
        return 0

def verify_cleanup():
    """Verify cleanup was successful"""
    print("\n🔍 Verifying cleanup...")

    # Check what remains
    superadmin_count = User.objects.filter(role=User.Role.SUPERADMIN).count()
    admin_count = User.objects.filter(role=User.Role.ADMIN).count()
    agent_count = safe_count_model(Agent, "agents")
    chat_sessions = safe_count_model(ChatSession, "chat sessions")
    user_profiles = safe_count_model(UserProfile, "user profiles")

    print(f"📊 SuperAdmin users remaining: {superadmin_count}")
    print(f"📊 Admin users remaining: {admin_count}")
    print(f"📊 Agents remaining: {agent_count}")
    print(f"📊 Chat sessions remaining: {chat_sessions}")
    print(f"📊 User profiles remaining: {user_profiles}")

    if superadmin_count == 1 and admin_count == 0 and agent_count == 0:
        print("✅ Cleanup verification successful!")
        return True
    else:
        print("⚠️ Cleanup verification failed!")
        return False

def main():
    """Main function"""
    print_banner()
    
    # Verify SuperAdmin exists
    if not verify_superadmin():
        return
    
    # Get confirmation
    if not get_confirmation():
        print("\n❌ Operation cancelled by user")
        return
    
    print("\n🚀 Starting cleanup process...")
    
    try:
        # Clean media files
        cleanup_media_files()
        
        # Clean database
        cleanup_database()
        
        # Verify cleanup
        if verify_cleanup():
            print("\n🎉 DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
            print("✅ SuperAdmin preserved")
            print("✅ All other data removed")
            print("✅ System ready for fresh start")
        else:
            print("\n⚠️ Cleanup completed but verification failed")
            
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        print("⚠️ Database may be in inconsistent state")
        return

if __name__ == "__main__":
    main()

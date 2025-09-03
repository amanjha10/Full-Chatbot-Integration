#!/usr/bin/env python
"""
Test script to create an escalated session for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from chatbot.models import ChatSession, UserProfile
from human_handoff.models import HumanHandoffSession
from admin_dashboard.models import Agent
import uuid

def create_test_escalation():
    """Create a test escalated session"""
    print("Creating test escalated session...")
    
    # Create a chat session
    session_id = str(uuid.uuid4())
    chat_session = ChatSession.objects.create(
        session_id=session_id,
        company_id="TEST001",
        status="escalated"
    )
    
    # Create a user profile
    user_profile = UserProfile.objects.create(
        session_id=session_id,
        company_id="TEST001",
        persistent_user_id=f"user_{uuid.uuid4().hex[:12]}",
        name="Test User",
        phone="+977-9841234567",
        email="test@example.com",
        address="Test Address",
        country_code="+977"
    )
    
    # Link profile to session
    chat_session.user_profile = user_profile
    chat_session.save()
    
    # Create handoff session (unassigned)
    handoff_session = HumanHandoffSession.objects.create(
        chat_session=chat_session,
        escalation_reason="User requested human assistance",
        priority="medium"
    )
    
    print(f"✅ Created escalated session:")
    print(f"   - Session ID: {session_id}")
    print(f"   - Handoff ID: {handoff_session.id}")
    print(f"   - User: {user_profile.name}")
    print(f"   - Company: {chat_session.company_id}")
    print(f"   - Status: Unassigned (ready for agent to accept)")
    
    return handoff_session

def check_agents():
    """Check available agents"""
    agents = Agent.objects.filter(company_id="TEST001")
    print(f"\n📋 Available agents for TEST001:")
    for agent in agents:
        print(f"   - {agent.name} ({agent.email}) - Status: {agent.status}")
    
    return agents

if __name__ == "__main__":
    try:
        # Check existing escalated sessions
        existing_sessions = HumanHandoffSession.objects.filter(
            agent__isnull=True,
            resolved_at__isnull=True,
            chat_session__company_id="TEST001"
        )
        
        print(f"🔍 Found {existing_sessions.count()} existing unassigned sessions")
        
        if existing_sessions.count() == 0:
            create_test_escalation()
        else:
            print("✅ Unassigned sessions already exist:")
            for session in existing_sessions:
                print(f"   - ID: {session.id}, User: {session.chat_session.user_profile.name if session.chat_session.user_profile else 'Unknown'}")
        
        check_agents()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

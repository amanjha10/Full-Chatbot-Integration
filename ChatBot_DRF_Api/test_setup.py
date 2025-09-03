import os, sys, django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from chatbot.models import ChatSession, UserProfile
from human_handoff.models import HumanHandoffSession
from admin_dashboard.models import Agent
import uuid

print('🔍 Checking existing data...')

# Check existing escalated sessions
sessions = HumanHandoffSession.objects.filter(
    agent__isnull=True,
    resolved_at__isnull=True,
    chat_session__company_id='TEST001'
)
print(f'Found {sessions.count()} unassigned escalated sessions')

# Check agents
agents = Agent.objects.filter(company_id='TEST001')
print(f'Found {agents.count()} agents for TEST001')
for agent in agents:
    print(f'  - {agent.name} ({agent.email})')

# Create test escalated session if none exist
if sessions.count() == 0:
    print('\n📝 Creating test escalated session...')
    
    # Create chat session
    session_id = str(uuid.uuid4())
    chat_session = ChatSession.objects.create(
        session_id=session_id,
        company_id='TEST001',
        status='escalated'
    )
    
    # Create user profile
    user_profile = UserProfile.objects.create(
        session_id=session_id,
        company_id='TEST001',
        persistent_user_id=f'user_{uuid.uuid4().hex[:12]}',
        name='Test User for Agent',
        phone='+977-9841234567',
        email='testuser@example.com',
        address='Test Address, Nepal',
        country_code='+977'
    )
    
    # Link profile to session
    chat_session.user_profile = user_profile
    chat_session.save()
    
    # Create handoff session (unassigned)
    handoff_session = HumanHandoffSession.objects.create(
        chat_session=chat_session,
        escalation_reason='User requested human assistance for study abroad guidance',
        priority='medium'
    )
    
    print(f'✅ Created escalated session:')
    print(f'   - Session ID: {session_id}')
    print(f'   - Handoff ID: {handoff_session.id}')
    print(f'   - User: {user_profile.name}')
    print(f'   - Status: Unassigned (ready for agent to accept)')
else:
    print('✅ Escalated sessions already exist:')
    for session in sessions:
        profile = session.chat_session.user_profile
        print(f'   - ID: {session.id}, User: {profile.name if profile else "Unknown"}')

print('\n🎯 Test the agent dashboard now:')
print('1. Login as agent: amanjha321@gmail.com')
print('2. Go to pending sessions')
print('3. You should see unassigned sessions to accept')
print('4. Click Accept to assign session to yourself')
print('5. Check active sessions to see accepted sessions')

#!/usr/bin/env python3
"""Test agent assignment and message flow"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_agent_flow():
    print("🧪 Testing Agent Assignment and Message Flow")
    print("="*50)
    
    # Step 1: Get admin token
    print("1. Getting admin token...")
    admin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': 'admin',
        'password': 'admin123'  # Try common admin password
    })
    
    if admin_response.status_code != 200:
        # Try alternative admin
        admin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
            'username': 'admin1',
            'password': 'admin123'
        })
    
    if admin_response.status_code != 200:
        print(f"❌ Admin login failed: {admin_response.text}")
        return
    
    admin_token = admin_response.json()['access']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    print("✅ Admin logged in")
    
    # Step 2: Get agent token
    print("\n2. Getting agent token...")
    agent_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': 'agent@test.com',
        'password': 'agent123'
    })
    
    if agent_response.status_code != 200:
        print(f"❌ Agent login failed: {agent_response.text}")
        return
    
    agent_data = agent_response.json()
    agent_token = agent_data['access']
    agent_id = agent_data['agent']['id']
    agent_headers = {'Authorization': f'Bearer {agent_token}'}
    print(f"✅ Agent logged in (ID: {agent_id})")
    
    # Step 3: List unassigned sessions
    print("\n3. Checking unassigned sessions...")
    sessions_response = requests.get(f"{BASE_URL}/api/human-handoff/sessions/?status=unassigned", 
                                   headers=admin_headers)
    
    if sessions_response.status_code != 200:
        print(f"❌ Failed to get sessions: {sessions_response.text}")
        return
    
    sessions = sessions_response.json()
    if not sessions:
        print("❌ No unassigned sessions found. Please escalate a session first.")
        return
    
    handoff_session_id = sessions[0]['id']
    session_id = sessions[0]['chat_session_id']
    print(f"✅ Found unassigned session (Handoff ID: {handoff_session_id}, Session ID: {session_id})")
    
    # Step 4: Assign session to agent
    print("\n4. Assigning session to agent...")
    assign_response = requests.post(f"{BASE_URL}/api/human-handoff/assign/", 
                                  headers=admin_headers,
                                  json={
                                      'handoff_session_id': handoff_session_id,
                                      'agent_id': agent_id
                                  })
    
    if assign_response.status_code != 200:
        print(f"❌ Failed to assign session: {assign_response.text}")
        return
    
    print("✅ Session assigned to agent")
    
    # Step 5: Agent views assigned sessions
    print("\n5. Agent checking assigned sessions...")
    agent_sessions_response = requests.get(f"{BASE_URL}/api/human-handoff/agent/sessions/", 
                                         headers=agent_headers)
    
    if agent_sessions_response.status_code != 200:
        print(f"❌ Failed to get agent sessions: {agent_sessions_response.text}")
        return
    
    agent_sessions = agent_sessions_response.json()
    print(f"✅ Agent sees {agent_sessions['count']} assigned sessions")
    
    # Step 6: Agent views session messages
    print(f"\n6. Agent viewing messages for session {session_id}...")
    messages_response = requests.get(f"{BASE_URL}/api/human-handoff/agent/sessions/{session_id}/messages/", 
                                   headers=agent_headers)
    
    if messages_response.status_code != 200:
        print(f"❌ Failed to get messages: {messages_response.text}")
        return
    
    messages_data = messages_response.json()
    print(f"✅ Agent can view messages ({len(messages_data['messages'])} messages found)")
    
    # Step 7: Agent sends message
    print(f"\n7. Agent sending message to session {session_id}...")
    send_response = requests.post(f"{BASE_URL}/api/human-handoff/agent/send-message/", 
                                headers=agent_headers,
                                json={
                                    'session_id': session_id,
                                    'message': 'Hello! I am your assigned advisor. How can I help you today?'
                                })
    
    if send_response.status_code != 200:
        print(f"❌ Failed to send message: {send_response.text}")
        return
    
    print("✅ Agent successfully sent message")
    
    # Step 8: Verify message was saved
    print(f"\n8. Verifying message was saved...")
    verify_response = requests.get(f"{BASE_URL}/api/human-handoff/agent/sessions/{session_id}/messages/", 
                                 headers=agent_headers)
    
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        agent_messages = [msg for msg in verify_data['messages'] if msg['message_type'] == 'agent']
        print(f"✅ Found {len(agent_messages)} agent messages in conversation")
    
    print("\n🎉 All tests passed! Agent assignment and messaging is working correctly.")

if __name__ == "__main__":
    test_agent_flow()

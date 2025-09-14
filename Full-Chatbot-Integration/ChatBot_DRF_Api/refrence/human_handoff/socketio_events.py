"""
Real-time Communication for Human Handoff System
Flask-SocketIO events for real-time messaging between users and agents
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import session, request
from datetime import datetime
import json
from .models import db, ChatSession, Message, Agent
from .database import db_manager

# Global SocketIO instance
socketio = None

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    global socketio
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        transports=['websocket', 'polling']
    )

    # Register event handlers
    register_events()

    return socketio

def get_socketio():
    """Get the global SocketIO instance"""
    return socketio

def register_events():
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        emit('connected', {'status': 'Connected to server'})

    @socketio.on('join_agents_room')
    def handle_join_agents_room():
        """Handle agent joining the agents notification room"""
        join_room('agents')
        print(f"Agent joined agents room: {request.sid}")
        emit('joined_agents_room', {'status': 'Joined agents notification room'})

    @socketio.on('leave_agents_room')
    def handle_leave_agents_room():
        """Handle agent leaving the agents notification room"""
        leave_room('agents')
        print(f"Agent left agents room: {request.sid}")
        emit('left_agents_room', {'status': 'Left agents notification room'})

    @socketio.on('join_super_admin_room')
    def handle_join_super_admin_room():
        """Handle super admin joining the super admin notification room"""
        join_room('super_admins')
        print(f"Super admin joined super admin room: {request.sid}")
        emit('joined_super_admin_room', {'status': 'Joined super admin notification room'})

    @socketio.on('leave_super_admin_room')
    def handle_leave_super_admin_room():
        """Handle super admin leaving the super admin notification room"""
        leave_room('super_admins')
        print(f"Super admin left super admin room: {request.sid}")
        emit('left_super_admin_room', {'status': 'Left super admin notification room'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """Handle user/agent joining a session room"""
        session_id = data.get('session_id')
        user_type = data.get('user_type', 'user')  # 'user' or 'agent'
        
        if not session_id:
            emit('error', {'message': 'Session ID is required'})
            return
        
        # Join the session room
        join_room(session_id)
        
        # Store session info in SocketIO session
        session['socketio_session_id'] = session_id
        session['socketio_user_type'] = user_type
        
        print(f"{user_type} joined session: {session_id}")
        
        # Notify others in the room
        emit('user_joined', {
            'user_type': user_type,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=session_id, include_self=False)
        
        # Send confirmation to the user
        emit('joined_session', {
            'session_id': session_id,
            'user_type': user_type
        })
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """Handle user/agent leaving a session room"""
        session_id = data.get('session_id')
        user_type = session.get('socketio_user_type', 'user')
        
        if session_id:
            leave_room(session_id)
            
            # Notify others in the room
            emit('user_left', {
                'user_type': user_type,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id, include_self=False)
            
            print(f"{user_type} left session: {session_id}")
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle real-time message sending"""
        session_id = data.get('session_id')
        message_content = data.get('message', '').strip()
        sender_type = data.get('sender_type', 'user')
        sender_id = data.get('sender_id')

        if not session_id or not message_content:
            emit('error', {'message': 'Session ID and message content are required'})
            return

        try:
            # Check if db_manager is available
            if db_manager is None:
                print("Warning: db_manager is None, skipping database save")
                message = None
            else:
                # Save message to database
                message = db_manager.add_message(
                    session_id=session_id,
                    sender_type=sender_type,
                    sender_id=sender_id,
                    message_content=message_content,
                    metadata={
                        'real_time': True,
                        'socket_id': request.sid
                    }
                )

            # Prepare message data for broadcast (works with or without database)
            message_data = {
                'id': message.id if message else None,
                'session_id': session_id,
                'sender_type': sender_type,
                'sender_id': sender_id,
                'message_content': message_content,
                'timestamp': message.timestamp.isoformat() if message else datetime.utcnow().isoformat(),
                'socket_id': request.sid
            }

            # Broadcast message to all users in the session room
            emit('new_message', message_data, room=session_id)

            # If this is the first agent message, notify that human has taken over
            if sender_type == 'agent':
                # Check if this is the first agent message in this session
                from .models import Message
                agent_message_count = Message.query.filter_by(
                    session_id=session_id,
                    sender_type='agent'
                ).count()

                if agent_message_count == 1:  # This is the first agent message
                    emit('human_takeover', {
                        'session_id': session_id,
                        'agent_id': sender_id,
                        'message': 'You\'re now chatting with a human agent.',
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=session_id)

            print(f"Message sent in session {session_id}: {message_content[:50]}...")

            if message is None and db_manager is None:
                print("Warning: Message not saved to database (db_manager unavailable)")
                
        except Exception as e:
            print(f"Error handling message: {e}")
            emit('error', {'message': 'Failed to send message'})
    
    @socketio.on('agent_typing')
    def handle_agent_typing(data):
        """Handle agent typing indicator"""
        session_id = data.get('session_id')
        agent_id = data.get('agent_id')
        is_typing = data.get('is_typing', False)
        
        if session_id and agent_id:
            emit('agent_typing_status', {
                'agent_id': agent_id,
                'is_typing': is_typing,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id, include_self=False)
    
    @socketio.on('user_typing')
    def handle_user_typing(data):
        """Handle user typing indicator"""
        session_id = data.get('session_id')
        is_typing = data.get('is_typing', False)
        
        if session_id:
            emit('user_typing_status', {
                'is_typing': is_typing,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id, include_self=False)
    
    @socketio.on('session_escalated')
    def handle_session_escalated(data):
        """Handle session escalation notification"""
        session_id = data.get('session_id')
        reason = data.get('reason', 'Bot unable to help')
        
        if session_id:
            # Notify all agents about new escalated session
            emit('new_escalated_session', {
                'session_id': session_id,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True, namespace='/agent')
            
            # Notify user about escalation
            emit('session_escalated_notification', {
                'session_id': session_id,
                'message': 'Your conversation has been escalated to a human agent.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
    
    @socketio.on('agent_assigned')
    def handle_agent_assigned(data):
        """Handle agent assignment notification"""
        session_id = data.get('session_id')
        agent_id = data.get('agent_id')
        agent_name = data.get('agent_name')
        
        if session_id and agent_id:
            # Notify user about agent assignment
            emit('agent_assigned_notification', {
                'session_id': session_id,
                'agent_id': agent_id,
                'agent_name': agent_name,
                'message': f'Agent {agent_name} has been assigned to help you.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
    
    @socketio.on('session_completed')
    def handle_session_completed(data):
        """Handle session completion notification"""
        session_id = data.get('session_id')
        agent_id = data.get('agent_id')
        
        if session_id:
            # Notify user about session completion
            emit('session_completed_notification', {
                'session_id': session_id,
                'message': 'Your conversation has been completed. Thank you for using our service!',
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
    
    @socketio.on('get_session_status')
    def handle_get_session_status(data):
        """Handle request for session status"""
        session_id = data.get('session_id')
        
        if session_id:
            try:
                # Get session from database
                chat_session = ChatSession.query.filter_by(session_id=session_id).first()
                
                if chat_session:
                    status_data = {
                        'session_id': session_id,
                        'requires_human': chat_session.requires_human,
                        'status': chat_session.status,
                        'assigned_agent_id': chat_session.assigned_agent_id,
                        'escalated_at': chat_session.escalated_at.isoformat() if chat_session.escalated_at else None
                    }
                    
                    # If agent is assigned, get agent info
                    if chat_session.assigned_agent_id:
                        agent = Agent.query.get(chat_session.assigned_agent_id)
                        if agent:
                            status_data['agent_name'] = agent.name
                            status_data['agent_specialization'] = agent.specialization
                    
                    emit('session_status', status_data)
                else:
                    emit('error', {'message': 'Session not found'})
                    
            except Exception as e:
                print(f"Error getting session status: {e}")
                emit('error', {'message': 'Failed to get session status'})

def notify_session_escalated(session_id, reason="Bot unable to help"):
    """Notify about session escalation"""
    if socketio:
        socketio.emit('session_escalated', {
            'session_id': session_id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })

def notify_agent_assigned(session_id, agent_id, agent_name):
    """Notify about agent assignment"""
    if socketio:
        socketio.emit('agent_assigned', {
            'session_id': session_id,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })

def notify_session_completed(session_id, agent_id):
    """Notify about session completion"""
    if socketio:
        socketio.emit('session_completed', {
            'session_id': session_id,
            'agent_id': agent_id,
            'timestamp': datetime.utcnow().isoformat()
        })

def send_agent_message_to_user(session_id, message_content, agent_id, agent_name):
    """Send agent message to user in real-time"""
    if socketio:
        socketio.emit('new_message', {
            'session_id': session_id,
            'sender_type': 'agent',
            'sender_id': agent_id,
            'sender_name': agent_name,
            'message_content': message_content,
            'timestamp': datetime.utcnow().isoformat()
        }, room=session_id)

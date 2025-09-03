"""
Session Manager for Human Handoff System
Handles session tracking and conversation storage
"""

import uuid
from datetime import datetime
from flask import session, request
from .models import db, ChatSession, Message, get_or_create_session

class SessionManager:
    """Manages chat sessions and conversation tracking"""
    
    def __init__(self):
        self.fallback_keywords = [
            "sorry, i am unaware",
            "i'm not sure about that",
            "i apologize, but i'm not sure",
            "would you like to speak with",
            "contact with our customer service",
            "i don't have information about",
            "i'm unable to help with that"
        ]
    
    def get_session_id(self):
        """Get or create session ID for current user"""
        if 'chat_session_id' not in session:
            new_session_id = str(uuid.uuid4())
            session['chat_session_id'] = new_session_id
            print(f"Created new session ID: {new_session_id}")
        else:
            current_session_id = session['chat_session_id']
            print(f"Checking existing session: {current_session_id}")

            # Check if existing session is closed/completed and create new one if needed
            try:
                from .models import ChatSession, UserProfile
                existing_session = ChatSession.query.filter_by(session_id=current_session_id).first()
                if existing_session:
                    print(f"Found existing session: status={existing_session.status}, requires_human={existing_session.requires_human}")

                    # Only create new session if the session is truly closed/completed
                    # Don't create new session for escalated sessions with profiles (user should continue in same session)
                    if existing_session.status in ['closed', 'completed']:
                        new_session_id = str(uuid.uuid4())
                        print(f"Creating new session - previous session {current_session_id} was {existing_session.status}")
                        session['chat_session_id'] = new_session_id
                    elif existing_session.requires_human:
                        # Check if this session has a user profile - if so, keep using it
                        profile = UserProfile.query.filter_by(session_id=current_session_id).first()
                        if profile:
                            print(f"Keeping existing session {current_session_id} - has user profile and is being handled by agent")
                        else:
                            # No profile, create new session
                            new_session_id = str(uuid.uuid4())
                            print(f"Creating new session - previous session {current_session_id} requires human but has no profile")
                            session['chat_session_id'] = new_session_id
                else:
                    print(f"No existing session found in database for {current_session_id}")
            except Exception as e:
                print(f"Error checking existing session status: {e}")

        return session['chat_session_id']

    def reset_session(self):
        """Reset the current session - create a new session ID"""
        old_session_id = session.get('chat_session_id')
        session['chat_session_id'] = str(uuid.uuid4())
        session.pop('requires_human', None)
        session.pop('assigned_agent', None)
        session.pop('escalated_at', None)
        print(f"Session reset: {old_session_id} -> {session['chat_session_id']}")
        return session['chat_session_id']

    def get_user_id(self):
        """Get user ID from authenticated student or fallback"""
        # Try to get authenticated student ID first
        try:
            from flask_login import current_user
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                return str(current_user.id)
        except (ImportError, AttributeError):
            pass

        # Fallback for non-authenticated sessions (backward compatibility)
        user_agent = request.headers.get('User-Agent', '')
        remote_addr = request.remote_addr or 'unknown'
        return f"guest_{remote_addr}_{hash(user_agent) % 10000}"
    
    def start_session(self):
        """Start a new chat session"""
        session_id = self.get_session_id()
        user_id = self.get_user_id()
        
        # Get student_id if user is authenticated
        try:
            from flask_login import current_user
            student_id = current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None
        except (ImportError, AttributeError):
            student_id = None
        
        # Get or create session in database
        chat_session = get_or_create_session(session_id, user_id, student_id)
        
        return {
            'session_id': session_id,
            'user_id': user_id,
            'student_id': student_id,
            'chat_session': chat_session
        }
    
    def log_message(self, message_content, sender_type='user', sender_id=None, is_fallback=False, metadata=None):
        """Log a message to the current session"""
        session_id = self.get_session_id()

        # Ensure session exists
        self.start_session()

        # Add message to database
        try:
            message = Message(
                session_id=session_id,
                sender_type=sender_type,
                sender_id=sender_id,
                message_content=message_content,
                is_fallback=is_fallback
            )
            if metadata:
                message.set_metadata(metadata)

            db.session.add(message)
            db.session.commit()
            return message
        except Exception as e:
            db.session.rollback()
            print(f"Error adding message: {e}")
            return None
    
    def log_user_message(self, message_content, metadata=None):
        """Log a user message"""
        user_id = self.get_user_id()
        return self.log_message(
            message_content=message_content,
            sender_type='user',
            sender_id=user_id,
            metadata=metadata
        )
    
    def log_bot_message(self, message_content, is_fallback=False, metadata=None):
        """Log a bot message"""
        return self.log_message(
            message_content=message_content,
            sender_type='bot',
            sender_id='eduConsult_bot',
            is_fallback=is_fallback,
            metadata=metadata
        )
    
    def log_agent_message(self, message_content, agent_id, metadata=None):
        """Log an agent message"""
        return self.log_message(
            message_content=message_content,
            sender_type='agent',
            sender_id=agent_id,
            metadata=metadata
        )
    
    def detect_fallback(self, bot_response):
        """Detect if bot response indicates a fallback scenario"""
        if not bot_response:
            return False
        
        response_lower = bot_response.lower()
        return any(keyword in response_lower for keyword in self.fallback_keywords)
    
    def handle_fallback(self, bot_response, reason="Bot unable to provide adequate response"):
        """Handle fallback scenario by escalating to human"""
        session_id = self.get_session_id()

        # Log the fallback bot message
        self.log_bot_message(bot_response, is_fallback=True)

        # Escalate session to human
        try:
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if chat_session:
                chat_session.requires_human = True
                chat_session.status = 'escalated'
                chat_session.escalation_reason = reason
                chat_session.escalated_at = datetime.utcnow()
                db.session.commit()

                # Send real-time notification to all agents about new escalation
                try:
                    from human_handoff.socketio_events import get_socketio
                    socketio = get_socketio()
                    if socketio:
                        # Get session details for notification
                        latest_message = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.desc()).first()

                        notification_data = {
                            'session_id': session_id,
                            'escalation_reason': reason,
                            'escalated_at': chat_session.escalated_at.isoformat(),
                            'latest_message': latest_message.message_content[:100] + '...' if latest_message and latest_message.message_content else 'No messages',
                            'message_count': Message.query.filter_by(session_id=session_id).count(),
                            'priority': 'high' if any(keyword in reason.lower() for keyword in ['urgent', 'immediate', 'emergency']) else 'normal'
                        }

                        socketio.emit('new_escalation', notification_data, room='agents')

                        # Also notify super admins
                        socketio.emit('new_escalation', notification_data, room='super_admins')

                        print(f"📢 Sent escalation notification for session {session_id} to agents and super admins")
                except Exception as e:
                    print(f"Failed to send escalation notification: {e}")

                # Mark session as requiring human intervention
                from flask import session
                session['requires_human'] = True
                session['escalated_at'] = datetime.utcnow().isoformat()
                return True
        except Exception as e:
            db.session.rollback()
            print(f"Error escalating session: {e}")

        return False
    
    def is_session_escalated(self):
        """Check if current session is escalated to human"""
        return session.get('requires_human', False)

    def is_human_handling_session(self):
        """Check if a human agent is actively handling the current session"""
        session_id = self.get_session_id()

        try:
            # Get session from database
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if chat_session:
                # Session is being handled by human if:
                # 1. It requires human assistance AND
                # 2. Either it's escalated OR has an assigned agent AND
                # 3. The session is not closed or completed
                return (chat_session.requires_human and
                       (chat_session.status == 'escalated' or chat_session.assigned_agent_id is not None) and
                       chat_session.status not in ['closed', 'completed'])
        except Exception as e:
            print(f"Error checking human handling status: {e}")

        return False
    
    def get_session_info(self):
        """Get current session information"""
        session_id = self.get_session_id()

        try:
            # Get session from database
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if chat_session:
                return {
                    'session_id': session_id,
                    'requires_human': chat_session.requires_human,
                    'status': chat_session.status,
                    'assigned_agent_id': chat_session.assigned_agent_id,
                    'escalated_at': chat_session.escalated_at.isoformat() if chat_session.escalated_at else None
                }
        except Exception as e:
            print(f"Error getting session info: {e}")

        return {
            'session_id': session_id,
            'requires_human': False,
            'status': 'active',
            'assigned_agent_id': None,
            'escalated_at': None
        }
    
    def get_conversation_history(self, limit=50):
        """Get conversation history for current session"""
        session_id = self.get_session_id()

        try:
            messages = Message.query.filter_by(
                session_id=session_id
            ).order_by(Message.timestamp.asc()).limit(limit).all()
            return [message.to_dict() for message in messages]
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def assign_agent(self, agent_id):
        """Assign an agent to current session"""
        session_id = self.get_session_id()

        try:
            from .models import Agent, AgentSession

            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            agent = Agent.query.filter_by(agent_id=agent_id).first()

            if chat_session and agent and agent.can_take_session():
                # Update session
                chat_session.assigned_agent_id = agent.id
                chat_session.status = 'escalated'

                # Create agent session relationship
                agent_session = AgentSession(
                    agent_id=agent.id,
                    session_id=session_id
                )

                # Update agent current sessions count
                agent.current_sessions += 1
                agent.status = 'busy' if agent.current_sessions >= agent.max_concurrent_sessions else 'available'

                db.session.add(agent_session)
                db.session.commit()

                from flask import session
                session['assigned_agent'] = agent_id
                return True
        except Exception as e:
            db.session.rollback()
            print(f"Error assigning agent: {e}")

        return False
    
    def complete_session(self, agent_id=None):
        """Mark current session as completed"""
        from flask import session
        session_id = self.get_session_id()
        agent_id = agent_id or session.get('assigned_agent')

        if agent_id:
            try:
                from .models import Agent, AgentSession

                chat_session = ChatSession.query.filter_by(session_id=session_id).first()
                agent = Agent.query.filter_by(agent_id=agent_id).first()

                if chat_session and agent:
                    # Update session
                    chat_session.status = 'closed'
                    chat_session.resolved_at = datetime.utcnow()

                    # Update agent session
                    agent_session = AgentSession.query.filter_by(
                        agent_id=agent.id,
                        session_id=session_id,
                        status='active'
                    ).first()

                    if agent_session:
                        agent_session.status = 'completed'
                        agent_session.completed_at = datetime.utcnow()

                    # Update agent stats
                    agent.current_sessions = max(0, agent.current_sessions - 1)
                    agent.total_sessions_handled += 1
                    agent.status = 'available' if agent.current_sessions < agent.max_concurrent_sessions else 'busy'

                    db.session.commit()

                    # Clear session flags
                    session.pop('requires_human', None)
                    session.pop('assigned_agent', None)
                    session.pop('escalated_at', None)
                    return True
            except Exception as e:
                db.session.rollback()
                print(f"Error completing session: {e}")

        return False
    
    def clear_session(self):
        """Clear current session data"""
        session.pop('chat_session_id', None)
        session.pop('requires_human', None)
        session.pop('assigned_agent', None)
        session.pop('escalated_at', None)
    
    def get_session_analytics(self):
        """Get analytics for current session"""
        session_id = self.get_session_id()

        try:
            from .models import SessionAnalytics
            analytics = SessionAnalytics.query.filter_by(session_id=session_id).first()
            return analytics.to_dict() if analytics else None
        except Exception as e:
            print(f"Error getting session analytics: {e}")
            return None

# Global session manager instance
session_manager = SessionManager()

def init_session_manager():
    """Initialize session manager"""
    global session_manager
    session_manager = SessionManager()
    return session_manager

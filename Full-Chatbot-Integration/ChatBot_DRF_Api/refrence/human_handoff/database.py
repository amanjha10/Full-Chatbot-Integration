"""
Database initialization and management for Human Handoff System
"""

import sqlite3
import os
from datetime import datetime
from .models import db, ChatSession, Message, Agent, AgentSession, SessionAnalytics

class DatabaseManager:
    """Manages database operations for the human handoff system"""
    
    def __init__(self, db_path='human_handoff.db'):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure database file exists and create if not"""
        if not os.path.exists(self.db_path):
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
            
            # Create database file
            conn = sqlite3.connect(self.db_path)
            conn.close()
    
    def execute_schema(self, schema_file='human_handoff/database_schema.sql'):
        """Execute SQL schema file to create tables"""
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error executing schema: {e}")
            return False
    
    def add_message(self, session_id, sender_type, message_content, sender_id=None, is_fallback=False, metadata=None):
        """Add a message to the database"""
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
    
    def escalate_session(self, session_id, reason="Bot unable to help"):
        """Mark a session as requiring human intervention"""
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            if session:
                session.requires_human = True
                session.status = 'escalated'
                session.escalation_reason = reason
                session.escalated_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error escalating session: {e}")
            return False
    
    def assign_agent_to_session(self, session_id, agent_id):
        """Assign an agent to a session"""
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            agent = Agent.query.filter_by(agent_id=agent_id).first()
            
            if session and agent and agent.can_take_session():
                # Update session
                session.assigned_agent_id = agent.id
                session.status = 'escalated'
                
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
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error assigning agent: {e}")
            return False
    
    def get_pending_sessions(self):
        """Get all sessions that require human attention"""
        try:
            sessions = ChatSession.query.filter_by(
                requires_human=True,
                status='escalated'
            ).order_by(ChatSession.escalated_at.desc()).all()
            return [session.to_dict() for session in sessions]
        except Exception as e:
            print(f"Error getting pending sessions: {e}")
            return []
    
    def get_session_messages(self, session_id):
        """Get all messages for a session"""
        try:
            messages = Message.query.filter_by(
                session_id=session_id
            ).order_by(Message.timestamp.asc()).all()
            return [message.to_dict() for message in messages]
        except Exception as e:
            print(f"Error getting session messages: {e}")
            return []
    
    def get_agent_sessions(self, agent_id):
        """Get all active sessions for an agent"""
        try:
            agent = Agent.query.filter_by(agent_id=agent_id).first()
            if not agent:
                return []
            
            sessions = ChatSession.query.filter_by(
                assigned_agent_id=agent.id,
                status='escalated'
            ).order_by(ChatSession.updated_at.desc()).all()
            return [session.to_dict() for session in sessions]
        except Exception as e:
            print(f"Error getting agent sessions: {e}")
            return []
    
    def complete_session(self, session_id, agent_id):
        """Mark a session as completed by an agent"""
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            agent = Agent.query.filter_by(agent_id=agent_id).first()
            
            if session and agent:
                # Update session
                session.status = 'closed'
                session.resolved_at = datetime.utcnow()
                
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
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error completing session: {e}")
            return False
    
    def get_available_agents(self):
        """Get all available agents"""
        try:
            agents = Agent.query.filter_by(
                is_active=True,
                status='available'
            ).all()
            return [agent.to_dict() for agent in agents]
        except Exception as e:
            print(f"Error getting available agents: {e}")
            return []
    
    def update_agent_status(self, agent_id, status):
        """Update agent status"""
        try:
            agent = Agent.query.filter_by(agent_id=agent_id).first()
            if agent:
                agent.status = status
                agent.last_active = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error updating agent status: {e}")
            return False
    
    def get_session_analytics(self, session_id):
        """Get analytics for a specific session"""
        try:
            analytics = SessionAnalytics.query.filter_by(session_id=session_id).first()
            return analytics.to_dict() if analytics else None
        except Exception as e:
            print(f"Error getting session analytics: {e}")
            return None

# Global database manager instance
db_manager = None

def init_db_manager(app):
    """Initialize database manager with Flask app"""
    global db_manager
    db_path = os.path.join(app.instance_path, 'human_handoff.db')
    os.makedirs(app.instance_path, exist_ok=True)
    db_manager = DatabaseManager(db_path)
    return db_manager

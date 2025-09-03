"""
Database models for the Human Handoff System
SQLAlchemy models for chat sessions, messages, and agent management
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid

db = SQLAlchemy()

class Student(UserMixin, db.Model):
    """Model for student users (authentication)"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    country_of_interest = db.Column(db.String(50), nullable=True)
    field_of_study = db.Column(db.String(100), nullable=True)
    study_level = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', foreign_keys='ChatSession.student_id', backref='student', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get student's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'country_of_interest': self.country_of_interest,
            'field_of_study': self.field_of_study,
            'study_level': self.study_level,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class UserProfile(db.Model):
    """Model for user profile information collected during chat"""
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)  # Made nullable for guest users
    session_id = db.Column(db.String(100), nullable=False)
    persistent_user_id = db.Column(db.String(100), nullable=True, unique=True)  # For cross-session persistence
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # Added email field, nullable for skip option
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)  # Track when profile was last used

    # Relationship
    student = db.relationship('Student', backref='profile_info', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'session_id': self.session_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email or '-',  # Show '-' if email is not provided
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'student_email': self.student.email if self.student else None
        }

class UploadedFile(db.Model):
    """Model for uploaded files"""
    __tablename__ = 'uploaded_files'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    user_profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=True)
    original_name = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Secure filename with timestamp
    filepath = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_context = db.Column(db.Text, nullable=True)  # Associated message

    # Relationship
    user_profile = db.relationship('UserProfile', backref='uploaded_files')

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'original_name': self.original_name,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'message_context': self.message_context
        }

class ChatSession(db.Model):
    """Model for chat sessions"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(100))  # Keep for backward compatibility with guest sessions
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)  # New FK for authenticated users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, closed, escalated
    requires_human = db.Column(db.Boolean, default=False)
    assigned_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))
    escalation_reason = db.Column(db.Text)
    escalated_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    user_satisfaction_rating = db.Column(db.Integer)
    notes = db.Column(db.Text)
    queue_position = db.Column(db.Integer, nullable=True)  # Track position in queue
    estimated_wait_time = db.Column(db.Integer, nullable=True)  # Estimated wait time in seconds
    
    # Relationships
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan')
    assigned_agent = db.relationship('Agent', backref='assigned_sessions')
    analytics = db.relationship('SessionAnalytics', backref='session', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'requires_human': self.requires_human,
            'assigned_agent_id': self.assigned_agent_id,
            'escalation_reason': self.escalation_reason,
            'escalated_at': self.escalated_at.isoformat() if self.escalated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'user_satisfaction_rating': self.user_satisfaction_rating,
            'notes': self.notes
        }

class Message(db.Model):
    """Model for chat messages"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), db.ForeignKey('chat_sessions.session_id'), nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # user, bot, agent
    sender_id = db.Column(db.String(100))
    message_content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, system
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_fallback = db.Column(db.Boolean, default=False)
    message_metadata = db.Column(db.Text)  # JSON string for additional data
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sender_type': self.sender_type,
            'sender_id': self.sender_id,
            'message_content': self.message_content,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_fallback': self.is_fallback,
            'metadata': json.loads(self.message_metadata) if self.message_metadata else None
        }

    def set_metadata(self, data):
        """Set metadata as JSON string"""
        self.message_metadata = json.dumps(data) if data else None

    def get_metadata(self):
        """Get metadata as Python object"""
        return json.loads(self.message_metadata) if self.message_metadata else None

class Agent(db.Model):
    """Model for human agents"""
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    specialization = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=True)
    password_set = db.Column(db.Boolean, default=False)  # True if agent has set their password
    status = db.Column(db.String(20), default='offline')  # available, busy, offline
    max_concurrent_sessions = db.Column(db.Integer, default=5)
    current_sessions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    total_sessions_handled = db.Column(db.Integer, default=0)
    average_response_time = db.Column(db.Integer, default=0)  # in seconds
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    agent_sessions = db.relationship('AgentSession', backref='agent', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'specialization': self.specialization,
            'status': self.status,
            'max_concurrent_sessions': self.max_concurrent_sessions,
            'current_sessions': self.current_sessions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'total_sessions_handled': self.total_sessions_handled,
            'average_response_time': self.average_response_time,
            'is_active': self.is_active
        }
    
    def can_take_session(self):
        """Check if agent can take a new session"""
        return (self.is_active and
                self.status == 'available' and
                self.current_sessions < self.max_concurrent_sessions)

    def is_actually_online(self):
        """Check if agent is actually online (logged in and active recently)"""
        if not self.is_active or self.status == 'offline':
            return False

        if not self.last_active:
            return False

        # Agent is considered online if they were active in the last 5 minutes
        time_since_active = datetime.utcnow() - self.last_active
        return time_since_active.total_seconds() <= 300  # 5 minutes

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        self.password_set = True

    def check_password(self, password):
        """Check if provided password matches the hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_first_login(self):
        """Check if this is the agent's first login (no password set)"""
        return not self.password_set or not self.password_hash
    
    def reset_password(self):
        """Reset password - only for super admin use"""
        self.password_hash = None
        self.password_set = False

class AgentSession(db.Model):
    """Model for agent-session relationships"""
    __tablename__ = 'agent_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    session_id = db.Column(db.String(100), db.ForeignKey('chat_sessions.session_id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, completed, transferred
    assigned_by_super_admin = db.Column(db.Boolean, default=False)
    super_admin_id = db.Column(db.Integer, db.ForeignKey('super_admins.id'), nullable=True)
    
    __table_args__ = (db.UniqueConstraint('agent_id', 'session_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'assigned_by_super_admin': self.assigned_by_super_admin,
            'super_admin_id': self.super_admin_id
        }

class SessionAnalytics(db.Model):
    """Model for session analytics"""
    __tablename__ = 'session_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), db.ForeignKey('chat_sessions.session_id'), nullable=False)
    total_messages = db.Column(db.Integer, default=0)
    bot_messages = db.Column(db.Integer, default=0)
    user_messages = db.Column(db.Integer, default=0)
    agent_messages = db.Column(db.Integer, default=0)
    session_duration = db.Column(db.Integer, default=0)  # in seconds
    escalation_time = db.Column(db.Integer, default=0)  # time to escalation in seconds
    resolution_time = db.Column(db.Integer, default=0)  # time to resolution in seconds
    fallback_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'total_messages': self.total_messages,
            'bot_messages': self.bot_messages,
            'user_messages': self.user_messages,
            'agent_messages': self.agent_messages,
            'session_duration': self.session_duration,
            'escalation_time': self.escalation_time,
            'resolution_time': self.resolution_time,
            'fallback_count': self.fallback_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

def init_database(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Only try to insert default agents if the Agent table structure is complete
        try:
            # Test if we can query agents (this will fail if password_hash column doesn't exist)
            test_query = Agent.query.first()
            
            # Insert default agents if they don't exist
            default_agents = [
                {'agent_id': 'agent_001', 'name': 'Sarah Johnson', 'email': 'sarah.johnson@educonsult.com', 'specialization': 'General Counselor'},
                {'agent_id': 'agent_002', 'name': 'Michael Chen', 'email': 'michael.chen@educonsult.com', 'specialization': 'US Universities Specialist'},
                {'agent_id': 'agent_003', 'name': 'Emma Williams', 'email': 'emma.williams@educonsult.com', 'specialization': 'UK Universities Specialist'},
                {'agent_id': 'agent_004', 'name': 'David Kumar', 'email': 'david.kumar@educonsult.com', 'specialization': 'Technical Support'}
            ]
            
            for agent_data in default_agents:
                existing_agent = Agent.query.filter_by(agent_id=agent_data['agent_id']).first()
                if not existing_agent:
                    agent = Agent(**agent_data)
                    agent.set_password('agent123')  # Default password for demo
                    db.session.add(agent)
            
            db.session.commit()
        except Exception as e:
            # If there's an error (like missing password_hash column), just create the tables
            # The migration script will handle adding default agents with passwords
            db.session.rollback()
            print(f"Note: Agent initialization skipped, run migration script if needed: {e}")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {e}")

def get_or_create_session(session_id, user_id=None, student_id=None):
    """Get existing session or create new one"""
    session = ChatSession.query.filter_by(session_id=session_id).first()
    if not session:
        session = ChatSession(session_id=session_id, user_id=user_id, student_id=student_id)
        db.session.add(session)
        db.session.commit()
    else:
        # Update student_id if user becomes authenticated during session
        if student_id and not session.student_id:
            session.student_id = student_id
            db.session.commit()
    return session

class SuperAdmin(db.Model):
    """Model for super administrators who manage agent assignments"""
    __tablename__ = 'super_admins'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    permissions = db.Column(db.Text)  # JSON string for permissions

    # Relationships
    assigned_sessions = db.relationship('AgentSession', backref='super_admin', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def can_assign_sessions(self):
        """Check if super admin can assign sessions"""
        return self.is_active

    def get_managed_agents(self):
        """Get list of agents this super admin can manage"""
        # For now, super admin can manage all agents
        return Agent.query.filter_by(is_active=True).all()

    def get_agent_workload_summary(self):
        """Get summary of agent workloads"""
        agents = self.get_managed_agents()
        summary = []

        for agent in agents:
            pending_count = ChatSession.query.filter_by(
                assigned_agent_id=agent.id,
                status='escalated'
            ).count()

            active_count = AgentSession.query.filter_by(
                agent_id=agent.id,
                status='active'
            ).count()

            # Determine actual status based on whether agent is actually online
            if agent.is_actually_online():
                # Agent is online - use their current status
                if agent.current_sessions > 0:
                    actual_status = 'busy'
                elif agent.status in ['available', 'busy']:
                    actual_status = agent.status
                else:
                    actual_status = 'available'
            else:
                # Agent is not actually online - show as offline
                actual_status = 'offline'

            summary.append({
                'agent_id': agent.agent_id,
                'agent_name': agent.name,
                'status': actual_status,
                'current_sessions': agent.current_sessions,
                'max_capacity': agent.max_concurrent_sessions,
                'pending_assignments': pending_count,
                'active_sessions': active_count,
                'specialization': agent.specialization,
                'last_active': agent.last_active.isoformat() if agent.last_active else None,
                'workload_percentage': round((agent.current_sessions / max(agent.max_concurrent_sessions, 1)) * 100, 1)
            })

        return summary

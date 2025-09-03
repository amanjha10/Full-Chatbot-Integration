"""
Human Handoff System for EduConsult Chatbot
A modular system for escalating conversations to human agents
"""

from .models import db, ChatSession, Message, Agent, AgentSession, SessionAnalytics, init_database, get_or_create_session
from .database import DatabaseManager, db_manager, init_db_manager

__version__ = '1.0.0'
__all__ = [
    'db', 'ChatSession', 'Message', 'Agent', 'AgentSession', 'SessionAnalytics',
    'init_database', 'get_or_create_session', 'DatabaseManager', 'db_manager', 'init_db_manager'
]

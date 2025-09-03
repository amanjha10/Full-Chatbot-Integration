"""
Configuration for Human Handoff System
"""

import os
from datetime import timedelta

class HumanHandoffConfig:
    """Configuration class for human handoff system"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///human_handoff.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    SESSION_TIMEOUT = timedelta(hours=2)  # Session timeout
    MAX_CONCURRENT_SESSIONS_PER_AGENT = 5
    
    # Real-time Communication
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Agent Configuration
    DEFAULT_AGENTS = [
        {
            'agent_id': 'agent_001',
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@educonsult.com',
            'specialization': 'General Counselor',
            'max_concurrent_sessions': 5
        },
        {
            'agent_id': 'agent_002',
            'name': 'Michael Chen',
            'email': 'michael.chen@educonsult.com',
            'specialization': 'US Universities Specialist',
            'max_concurrent_sessions': 3
        },
        {
            'agent_id': 'agent_003',
            'name': 'Emma Williams',
            'email': 'emma.williams@educonsult.com',
            'specialization': 'UK Universities Specialist',
            'max_concurrent_sessions': 3
        },
        {
            'agent_id': 'agent_004',
            'name': 'David Kumar',
            'email': 'david.kumar@educonsult.com',
            'specialization': 'Technical Support',
            'max_concurrent_sessions': 4
        }
    ]
    
    # Escalation Configuration
    ESCALATION_TRIGGERS = [
        "sorry, i am unaware",
        "i'm not sure about that",
        "i apologize, but i'm not sure",
        "would you like to speak with",
        "contact with our customer service",
        "i don't have information about",
        "i'm unable to help with that"
    ]
    
    # Auto-escalation settings
    AUTO_ESCALATE_AFTER_FALLBACKS = 2  # Escalate after 2 fallback responses
    AUTO_ESCALATE_TIMEOUT = timedelta(minutes=10)  # Escalate if no response for 10 minutes
    
    # Notification Settings
    ENABLE_EMAIL_NOTIFICATIONS = False  # Set to True to enable email notifications
    ENABLE_SLACK_NOTIFICATIONS = False  # Set to True to enable Slack notifications
    
    # Analytics Configuration
    ENABLE_SESSION_ANALYTICS = True
    ANALYTICS_RETENTION_DAYS = 90  # Keep analytics for 90 days
    
    # Security Configuration
    AGENT_SESSION_TIMEOUT = timedelta(hours=8)  # Agent session timeout
    REQUIRE_AGENT_AUTHENTICATION = True
    
    # Performance Configuration
    MAX_MESSAGE_LENGTH = 2000  # Maximum message length
    MESSAGE_RATE_LIMIT = 10  # Messages per minute per user
    
    # UI Configuration
    CHAT_HISTORY_LIMIT = 100  # Number of messages to show in chat history
    REFRESH_INTERVAL = 30  # Auto-refresh interval in seconds
    
    @classmethod
    def get_config(cls):
        """Get configuration as dictionary"""
        return {
            'database_url': cls.DATABASE_URL,
            'session_timeout': cls.SESSION_TIMEOUT,
            'max_concurrent_sessions': cls.MAX_CONCURRENT_SESSIONS_PER_AGENT,
            'socketio_async_mode': cls.SOCKETIO_ASYNC_MODE,
            'socketio_cors_origins': cls.SOCKETIO_CORS_ALLOWED_ORIGINS,
            'default_agents': cls.DEFAULT_AGENTS,
            'escalation_triggers': cls.ESCALATION_TRIGGERS,
            'auto_escalate_after_fallbacks': cls.AUTO_ESCALATE_AFTER_FALLBACKS,
            'auto_escalate_timeout': cls.AUTO_ESCALATE_TIMEOUT,
            'enable_email_notifications': cls.ENABLE_EMAIL_NOTIFICATIONS,
            'enable_slack_notifications': cls.ENABLE_SLACK_NOTIFICATIONS,
            'enable_session_analytics': cls.ENABLE_SESSION_ANALYTICS,
            'analytics_retention_days': cls.ANALYTICS_RETENTION_DAYS,
            'agent_session_timeout': cls.AGENT_SESSION_TIMEOUT,
            'require_agent_authentication': cls.REQUIRE_AGENT_AUTHENTICATION,
            'max_message_length': cls.MAX_MESSAGE_LENGTH,
            'message_rate_limit': cls.MESSAGE_RATE_LIMIT,
            'chat_history_limit': cls.CHAT_HISTORY_LIMIT,
            'refresh_interval': cls.REFRESH_INTERVAL
        }

# Environment-specific configurations
class DevelopmentConfig(HumanHandoffConfig):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
class ProductionConfig(HumanHandoffConfig):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Use PostgreSQL in production
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/human_handoff')
    
    # Enhanced security in production
    REQUIRE_AGENT_AUTHENTICATION = True
    AGENT_SESSION_TIMEOUT = timedelta(hours=4)
    
    # Performance optimizations
    MAX_CONCURRENT_SESSIONS_PER_AGENT = 3
    MESSAGE_RATE_LIMIT = 5
    
class TestingConfig(HumanHandoffConfig):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'  # In-memory database for tests
    
    # Faster timeouts for testing
    SESSION_TIMEOUT = timedelta(minutes=5)
    AUTO_ESCALATE_TIMEOUT = timedelta(minutes=1)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])

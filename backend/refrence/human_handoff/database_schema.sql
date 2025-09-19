-- Human Handoff System Database Schema
-- SQLite database for managing chat sessions and human agent interactions

-- Chat Sessions Table
-- Stores individual chat sessions with users
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'closed', 'escalated')),
    requires_human BOOLEAN DEFAULT FALSE,
    assigned_agent_id INTEGER,
    escalation_reason TEXT,
    escalated_at TIMESTAMP,
    resolved_at TIMESTAMP,
    user_satisfaction_rating INTEGER CHECK (user_satisfaction_rating BETWEEN 1 AND 5),
    notes TEXT,
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id)
);

-- Messages Table
-- Stores all messages in chat sessions
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'bot', 'agent')),
    sender_id TEXT,
    message_content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'file', 'system')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_fallback BOOLEAN DEFAULT FALSE,
    metadata TEXT, -- JSON string for additional data
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Agents Table
-- Stores human agent information
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    specialization TEXT,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'busy', 'offline')),
    max_concurrent_sessions INTEGER DEFAULT 5,
    current_sessions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_sessions_handled INTEGER DEFAULT 0,
    average_response_time INTEGER DEFAULT 0, -- in seconds
    is_active BOOLEAN DEFAULT TRUE
);

-- Agent Sessions Table
-- Many-to-many relationship between agents and sessions
CREATE TABLE IF NOT EXISTS agent_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'transferred')),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id),
    UNIQUE(agent_id, session_id)
);

-- Session Analytics Table
-- Stores analytics data for sessions
CREATE TABLE IF NOT EXISTS session_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    total_messages INTEGER DEFAULT 0,
    bot_messages INTEGER DEFAULT 0,
    user_messages INTEGER DEFAULT 0,
    agent_messages INTEGER DEFAULT 0,
    session_duration INTEGER DEFAULT 0, -- in seconds
    escalation_time INTEGER DEFAULT 0, -- time to escalation in seconds
    resolution_time INTEGER DEFAULT 0, -- time to resolution in seconds
    fallback_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_requires_human ON chat_sessions(requires_human);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_assigned_agent ON chat_sessions(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_type ON messages(sender_type);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_is_fallback ON messages(is_fallback);

CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_id ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_session_id ON agent_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);

-- Insert default agents
INSERT OR IGNORE INTO agents (agent_id, name, email, specialization) VALUES 
('agent_001', 'Sarah Johnson', 'sarah.johnson@educonsult.com', 'General Counselor'),
('agent_002', 'Michael Chen', 'michael.chen@educonsult.com', 'US Universities Specialist'),
('agent_003', 'Emma Williams', 'emma.williams@educonsult.com', 'UK Universities Specialist'),
('agent_004', 'David Kumar', 'david.kumar@educonsult.com', 'Technical Support');

-- Triggers to update timestamps and analytics
CREATE TRIGGER IF NOT EXISTS update_chat_sessions_timestamp 
    AFTER UPDATE ON chat_sessions
    BEGIN
        UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_agent_last_active 
    AFTER INSERT ON messages
    WHEN NEW.sender_type = 'agent'
    BEGIN
        UPDATE agents SET last_active = CURRENT_TIMESTAMP 
        WHERE agent_id = NEW.sender_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_session_analytics_on_message
    AFTER INSERT ON messages
    BEGIN
        INSERT OR REPLACE INTO session_analytics (
            session_id, total_messages, bot_messages, user_messages, agent_messages, fallback_count
        )
        SELECT 
            NEW.session_id,
            COUNT(*) as total_messages,
            SUM(CASE WHEN sender_type = 'bot' THEN 1 ELSE 0 END) as bot_messages,
            SUM(CASE WHEN sender_type = 'user' THEN 1 ELSE 0 END) as user_messages,
            SUM(CASE WHEN sender_type = 'agent' THEN 1 ELSE 0 END) as agent_messages,
            SUM(CASE WHEN is_fallback = 1 THEN 1 ELSE 0 END) as fallback_count
        FROM messages 
        WHERE session_id = NEW.session_id;
    END;

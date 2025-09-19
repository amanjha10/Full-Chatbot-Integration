"""
Agent Dashboard Routes for Human Handoff System
Flask routes for agent management and conversation handling
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import re
from .models import db, ChatSession, Message, Agent, AgentSession
from .database import DatabaseManager
from .session_manager import session_manager

# Create blueprint for agent routes
agent_bp = Blueprint('agent', __name__, url_prefix='/agent')

@agent_bp.route('/login', methods=['GET', 'POST'])
def agent_login():
    """Agent login page"""
    if request.method == 'POST':
        agent_id = request.form.get('agent_id')
        password = request.form.get('password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Find the agent
        agent = Agent.query.filter_by(agent_id=agent_id, is_active=True).first()
        if not agent:
            return render_template('agent/login.html', error='Invalid agent ID')
        
        # Check if this is first-time login
        if agent.is_first_login():
            # First-time login - agent must set password
            if not new_password or not confirm_password:
                return render_template('agent/login.html', 
                                     error='Please set your password for first-time login',
                                     first_time=True,
                                     agent_id=agent_id)
            
            if new_password != confirm_password:
                return render_template('agent/login.html', 
                                     error='Passwords do not match',
                                     first_time=True,
                                     agent_id=agent_id)
            
            if len(new_password) < 6:
                return render_template('agent/login.html', 
                                     error='Password must be at least 6 characters long',
                                     first_time=True,
                                     agent_id=agent_id)
            
            # Set the new password
            agent.set_password(new_password)
            db.session.commit()
            
            # Log in the agent
            session['agent_id'] = agent_id
            session['agent_name'] = agent.name
            
            # Update agent status
            agent.status = 'available'
            agent.last_active = datetime.utcnow()
            db.session.commit()
            
            return redirect(url_for('agent.dashboard'))
        
        else:
            # Regular login - check existing password
            if agent.check_password(password):
                session['agent_id'] = agent_id
                session['agent_name'] = agent.name

                # Update agent status to available
                agent.status = 'available'
                agent.last_active = datetime.utcnow()
                db.session.commit()

                return redirect(url_for('agent.dashboard'))
            else:
                return render_template('agent/login.html', error='Invalid password')
    
    return render_template('agent/login.html')

@agent_bp.route('/logout')
def agent_logout():
    """Agent logout"""
    agent_id = session.get('agent_id')
    if agent_id:
        # Update agent status to offline
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if agent:
            agent.status = 'offline'
            agent.last_active = datetime.utcnow()
            db.session.commit()

    session.pop('agent_id', None)
    session.pop('agent_name', None)
    return redirect(url_for('agent.agent_login'))

@agent_bp.route('/dashboard')
def dashboard():
    """Agent dashboard - main page"""
    if 'agent_id' not in session:
        return redirect(url_for('agent.agent_login'))
    
    agent_id = session['agent_id']
    
    # Get agent information
    agent = Agent.query.filter_by(agent_id=agent_id).first()
    if not agent:
        return redirect(url_for('agent.agent_login'))

    # Update agent activity - mark as active when accessing dashboard
    # Only update status if agent is actually logged in (has session)
    if 'agent_id' in session and session['agent_id'] == agent.agent_id:
        agent.last_active = datetime.utcnow()
        agent.status = 'available' if agent.current_sessions < agent.max_concurrent_sessions else 'busy'
        db.session.commit()
    
    # Get pending sessions (not assigned to any agent)
    pending_sessions = ChatSession.query.filter_by(
        requires_human=True,
        status='escalated',
        assigned_agent_id=None
    ).order_by(ChatSession.escalated_at.asc()).all()

    # Get agent's assigned sessions
    assigned_sessions = ChatSession.query.filter_by(
        assigned_agent_id=agent.id,
        status='escalated'
    ).order_by(ChatSession.updated_at.desc()).all()


    return render_template('agent/dashboard.html',
                         agent=agent,
                         pending_sessions=pending_sessions,
                         assigned_sessions=assigned_sessions)

@agent_bp.route('/api/pending-sessions')
def api_pending_sessions():
    """API endpoint to get pending sessions"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized', 'redirect': '/agent/login'}), 401

    try:
        # Update agent activity - only if they're actually logged in
        agent = Agent.query.filter_by(agent_id=session['agent_id']).first()
        if agent and 'agent_id' in session:
            agent.last_active = datetime.utcnow()
            # Only update status to available/busy if agent is logged in
            agent.status = 'available' if agent.current_sessions < agent.max_concurrent_sessions else 'busy'
            db.session.commit()
        # Get current agent
        current_agent = Agent.query.filter_by(agent_id=session['agent_id']).first()

        pending_sessions = ChatSession.query.filter_by(
            requires_human=True,
            status='escalated',
            assigned_agent_id=None
        ).order_by(ChatSession.escalated_at.asc()).all()

        sessions_data = []
        for session_obj in pending_sessions:
            session_dict = session_obj.to_dict()

            # Add intelligent assignment suggestions (temporarily disabled to debug)
            try:
                session_dict['assignment_suggestions'] = get_assignment_suggestions(session_obj, current_agent)
                session_dict['priority'] = calculate_session_priority(session_obj)
                session_dict['estimated_complexity'] = estimate_session_complexity(session_obj)
                session_dict['recommended_for_you'] = is_session_recommended_for_agent(session_obj, current_agent)
            except Exception as e:
                print(f"Error in helper functions: {e}")
                # Provide default values
                session_dict['assignment_suggestions'] = []
                session_dict['priority'] = 1
                session_dict['estimated_complexity'] = 'Low'
                session_dict['recommended_for_you'] = False

            sessions_data.append(session_dict)

        # Sort by priority and recommendation (recommended for current agent first, then by priority)
        sessions_data.sort(key=lambda x: (x['recommended_for_you'], x['priority']), reverse=True)

        return jsonify({'sessions': sessions_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/my-sessions')
def api_my_sessions():
    """API endpoint to get agent's assigned sessions"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized', 'redirect': '/agent/login'}), 401

    try:
        # Update agent activity - only if they're actually logged in
        agent = Agent.query.filter_by(agent_id=session['agent_id']).first()
        if agent and 'agent_id' in session:
            agent.last_active = datetime.utcnow()
            # Only update status to available/busy if agent is logged in
            agent.status = 'available' if agent.current_sessions < agent.max_concurrent_sessions else 'busy'
            db.session.commit()
        agent_id = session['agent_id']
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        sessions = ChatSession.query.filter_by(
            assigned_agent_id=agent.id
        ).filter(
            ChatSession.status.in_(['escalated', 'assigned', 'active'])
        ).order_by(ChatSession.updated_at.desc()).all()

        sessions_data = [session.to_dict() for session in sessions]
        return jsonify({'sessions': sessions_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/session/<session_id>/messages')
def api_session_messages(session_id):
    """API endpoint to get messages for a specific session"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        messages = Message.query.filter_by(
            session_id=session_id
        ).order_by(Message.timestamp.asc()).all()

        messages_data = [message.to_dict() for message in messages]
        return jsonify({'messages': messages_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/session/<session_id>/assign', methods=['POST'])
def api_assign_session(session_id):
    """API endpoint to assign a session to the current agent"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        agent_id = session['agent_id']

        # Get the session and agent
        chat_session = ChatSession.query.filter_by(session_id=session_id).first()
        agent = Agent.query.filter_by(agent_id=agent_id).first()

        if not chat_session or not agent:
            return jsonify({'success': False, 'message': 'Session or agent not found'}), 404

        # Check if session is already assigned
        if chat_session.assigned_agent_id:
            assigned_agent = Agent.query.get(chat_session.assigned_agent_id)
            return jsonify({
                'success': False,
                'message': f'Session already assigned to {assigned_agent.name if assigned_agent else "another agent"}'
            }), 400

        if not agent.can_take_session():
            return jsonify({'success': False, 'message': 'Agent cannot take more sessions'}), 400

        # Assign the session
        chat_session.assigned_agent_id = agent.id
        chat_session.status = 'assigned'

        # Check if agent session relationship already exists
        existing_agent_session = AgentSession.query.filter_by(
            agent_id=agent.id,
            session_id=session_id
        ).first()

        if existing_agent_session:
            # Update existing record
            existing_agent_session.status = 'active'
            existing_agent_session.assigned_at = datetime.utcnow()
        else:
            # Create new agent session relationship
            agent_session = AgentSession(
                agent_id=agent.id,
                session_id=session_id
            )
            db.session.add(agent_session)

        # Update agent current sessions count
        agent.current_sessions += 1
        agent.status = 'busy' if agent.current_sessions >= agent.max_concurrent_sessions else 'available'
        agent.last_active = datetime.utcnow()
        db.session.commit()

        # Emit real-time notification to all agents about session assignment
        from human_handoff.socketio_events import socketio
        socketio.emit('session_assigned', {
            'session_id': session_id,
            'agent_name': agent.name,
            'agent_id': agent.agent_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room='agents')

        return jsonify({
            'success': True,
            'message': f'Session assigned to {agent.name} successfully',
            'agent_name': agent.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/session/<session_id>/send-message', methods=['POST'])
def api_send_message(session_id):
    """API endpoint for agent to send a message"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return jsonify({'error': 'Message content is required'}), 400
        
        agent_id = session['agent_id']

        # Add message to database
        message = Message(
            session_id=session_id,
            sender_type='agent',
            sender_id=agent_id,
            message_content=message_content
        )
        message.set_metadata({'agent_name': session.get('agent_name')})

        db.session.add(message)
        db.session.commit()

        if message:
            # Broadcast message to user via SocketIO
            try:
                from human_handoff.socketio_events import get_socketio
                socketio = get_socketio()
                if socketio:
                    socketio.emit('new_message', {
                        'session_id': session_id,
                        'sender_type': 'agent',
                        'sender_id': agent_id,
                        'sender_name': session.get('agent_name'),
                        'message_content': message_content,
                        'timestamp': message.timestamp.isoformat()
                    }, room=session_id)

                    print(f"Broadcasted agent message to session {session_id}: {message_content[:50]}...")
                else:
                    print("SocketIO instance not available")
            except Exception as e:
                print(f"Error broadcasting message: {e}")

            return jsonify({
                'success': True,
                'message': message.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to send message'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/session/<session_id>/complete', methods=['POST'])
def api_complete_session(session_id):
    """API endpoint to mark a session as completed"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        agent_id = session['agent_id']

        # Get the session and agent
        chat_session = ChatSession.query.filter_by(session_id=session_id).first()
        agent = Agent.query.filter_by(agent_id=agent_id).first()

        if not chat_session or not agent:
            return jsonify({'success': False, 'message': 'Session or agent not found'}), 404

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

        return jsonify({'success': True, 'message': 'Session completed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/session/<session_id>')
def session_detail(session_id):
    """Session detail page for agents"""
    if 'agent_id' not in session:
        return redirect(url_for('agent.agent_login'))
    
    # Get session information
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        return "Session not found", 404
    
    # Get messages for the session
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()
    
    # Get agent information
    agent_id = session['agent_id']
    agent = Agent.query.filter_by(agent_id=agent_id).first()
    
    return render_template('agent/session_detail.html',
                         session=chat_session,
                         messages=messages,
                         agent=agent)

@agent_bp.route('/api/agents/status', methods=['POST'])
def api_update_agent_status():
    """API endpoint to update agent status"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        status = data.get('status')

        if status not in ['available', 'busy', 'offline']:
            return jsonify({'error': 'Invalid status'}), 400

        agent_id = session['agent_id']
        agent = Agent.query.filter_by(agent_id=agent_id).first()

        if not agent:
            return jsonify({'success': False, 'message': 'Agent not found'}), 404

        agent.status = status
        agent.last_active = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'status': status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/scheduler-status')
def api_scheduler_status():
    """API endpoint to get scheduler status for agents"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from .daily_scheduler import get_scheduler_status
        status = get_scheduler_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/my-stats')
def api_my_stats():
    """API endpoint to get agent's personal statistics"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        agent_id = session['agent_id']
        agent = Agent.query.filter_by(agent_id=agent_id).first()

        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        return jsonify({
            'total_sessions_handled': agent.total_sessions_handled,
            'current_sessions': agent.current_sessions,
            'max_concurrent_sessions': agent.max_concurrent_sessions,
            'status': agent.status,
            'average_response_time': agent.average_response_time
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/api/session/<session_id>/analytics')
def api_session_analytics(session_id):
    """API endpoint to get session analytics"""
    if 'agent_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from .models import SessionAnalytics
        analytics = SessionAnalytics.query.filter_by(session_id=session_id).first()

        if analytics:
            return jsonify({'analytics': analytics.to_dict()})
        else:
            return jsonify({'analytics': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper function to check if agent is authenticated
def require_agent_auth():
    """Decorator to require agent authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'agent_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Helper functions for intelligent assignment

def get_assignment_suggestions(chat_session, current_agent):
    """Get intelligent assignment suggestions for a session"""
    suggestions = []

    # Get all available agents
    available_agents = Agent.query.filter_by(status='available').all()

    for agent in available_agents:
        if agent.can_take_session():
            score = calculate_agent_match_score(chat_session, agent)
            suggestions.append({
                'agent_id': agent.agent_id,
                'agent_name': agent.name,
                'specialization': agent.specialization,
                'match_score': score,
                'current_load': agent.current_sessions,
                'max_capacity': agent.max_concurrent_sessions,
                'is_current_agent': agent.id == current_agent.id if current_agent else False
            })

    # Sort by match score (highest first)
    suggestions.sort(key=lambda x: x['match_score'], reverse=True)
    return suggestions[:3]  # Return top 3 suggestions

def calculate_agent_match_score(chat_session, agent):
    """Calculate how well an agent matches a session"""
    score = 0

    # Base score for availability
    if agent.status == 'available':
        score += 10

    # Workload factor (prefer agents with lower current load)
    load_factor = 1 - (agent.current_sessions / max(agent.max_concurrent_sessions, 1))
    score += load_factor * 20

    # Specialization matching
    if agent.specialization and chat_session.escalation_reason:
        specialization_keywords = {
            'visa': ['visa', 'immigration', 'documentation'],
            'scholarship': ['scholarship', 'funding', 'financial'],
            'academic': ['academic', 'course', 'program', 'university'],
            'general': ['general', 'information', 'guidance']
        }

        reason_lower = chat_session.escalation_reason.lower()
        spec_lower = agent.specialization.lower()

        for spec_type, keywords in specialization_keywords.items():
            if spec_type in spec_lower:
                for keyword in keywords:
                    if keyword in reason_lower:
                        score += 15
                        break

    # Experience factor (agents who handled more sessions get slight preference)
    experience_factor = min(agent.total_sessions_handled / 100, 1) * 5
    score += experience_factor

    # Recent activity factor (prefer recently active agents)
    if agent.last_active:
        hours_since_active = (datetime.utcnow() - agent.last_active).total_seconds() / 3600
        if hours_since_active < 1:
            score += 5
        elif hours_since_active < 24:
            score += 2

    return round(score, 2)

def calculate_session_priority(chat_session):
    """Calculate session priority based on various factors"""
    priority = 1  # Base priority

    # Time-based priority (older sessions get higher priority)
    if chat_session.escalated_at:
        hours_waiting = (datetime.utcnow() - chat_session.escalated_at).total_seconds() / 3600
        if hours_waiting > 2:
            priority += 2
        elif hours_waiting > 1:
            priority += 1

    # Urgency keywords in escalation reason
    if chat_session.escalation_reason:
        urgent_keywords = ['urgent', 'emergency', 'asap', 'immediate', 'deadline']
        reason_lower = chat_session.escalation_reason.lower()
        for keyword in urgent_keywords:
            if keyword in reason_lower:
                priority += 3
                break

    # Message count (more messages might indicate complexity)
    message_count = Message.query.filter_by(session_id=chat_session.session_id).count()
    if message_count > 10:
        priority += 1

    return min(priority, 5)  # Cap at 5

def estimate_session_complexity(chat_session):
    """Estimate session complexity"""
    complexity = 'Low'

    # Check message content for complexity indicators
    messages = Message.query.filter_by(session_id=chat_session.session_id).all()

    complex_keywords = ['legal', 'documentation', 'visa', 'immigration', 'complex', 'multiple', 'urgent']
    simple_keywords = ['information', 'general', 'basic', 'simple']

    complex_count = 0
    simple_count = 0

    for message in messages:
        if message.message_content:
            content_lower = message.message_content.lower()
            for keyword in complex_keywords:
                if keyword in content_lower:
                    complex_count += 1
            for keyword in simple_keywords:
                if keyword in content_lower:
                    simple_count += 1

    if complex_count > simple_count and complex_count > 2:
        complexity = 'High'
    elif complex_count > 0 or len(messages) > 5:
        complexity = 'Medium'

    return complexity

def is_session_recommended_for_agent(chat_session, agent):
    """Check if session is specifically recommended for the agent"""
    if not agent:
        return False

    match_score = calculate_agent_match_score(chat_session, agent)
    return match_score > 25  # Threshold for recommendation

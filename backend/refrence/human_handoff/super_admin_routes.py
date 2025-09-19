"""
Super Admin Routes for Managing Agent Assignments
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
import json
from .models import db, SuperAdmin, Agent, ChatSession, AgentSession, Message
from .socketio_events import get_socketio

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

def super_admin_required(f):
    """Decorator to require super admin authentication"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'super_admin_id' not in session:
            return redirect(url_for('super_admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@super_admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Super admin login"""
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        password = request.form.get('password')
        
        # For demo purposes, simple authentication
        # In production, use proper password hashing
        if admin_id == 'super_admin' and password == 'admin123':
            # Get or create super admin
            super_admin = SuperAdmin.query.filter_by(admin_id=admin_id).first()
            if not super_admin:
                super_admin = SuperAdmin(
                    admin_id=admin_id,
                    name='Super Administrator',
                    email='admin@educonsult.com',
                    password_hash='hashed_password',  # In production, hash this
                    is_active=True
                )
                db.session.add(super_admin)
                db.session.commit()
            
            # Update last login
            super_admin.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session
            session['super_admin_id'] = super_admin.id
            session['super_admin_name'] = super_admin.name
            
            return redirect(url_for('super_admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('super_admin/login.html')

@super_admin_bp.route('/logout')
def logout():
    """Super admin logout"""
    session.pop('super_admin_id', None)
    session.pop('super_admin_name', None)
    return redirect(url_for('super_admin.login'))

@super_admin_bp.route('/dashboard')
@super_admin_required
def dashboard():
    """Super admin dashboard"""
    super_admin = SuperAdmin.query.get(session['super_admin_id'])
    
    # Get pending sessions that need assignment
    pending_sessions = ChatSession.query.filter_by(
        requires_human=True,
        status='escalated',
        assigned_agent_id=None
    ).order_by(ChatSession.escalated_at.desc()).all()
    
    # Get agent workload summary
    agent_summary = super_admin.get_agent_workload_summary()
    
    # Get recent assignments made by this super admin
    recent_assignments = AgentSession.query.filter_by(
        super_admin_id=super_admin.id,
        assigned_by_super_admin=True
    ).order_by(AgentSession.assigned_at.desc()).limit(10).all()
    
    return render_template('super_admin/dashboard.html',
                         super_admin=super_admin,
                         pending_sessions=pending_sessions,
                         agent_summary=agent_summary,
                         recent_assignments=recent_assignments)

@super_admin_bp.route('/api/pending-sessions')
@super_admin_required
def api_pending_sessions():
    """API endpoint for pending sessions"""
    try:
        sessions = ChatSession.query.filter_by(
            requires_human=True,
            status='escalated',
            assigned_agent_id=None
        ).order_by(ChatSession.escalated_at.asc()).all()
        
        session_data = []
        for session in sessions:
            # Get latest message
            latest_message = Message.query.filter_by(
                session_id=session.session_id
            ).order_by(Message.timestamp.desc()).first()
            
            # Calculate priority and complexity
            priority = calculate_session_priority(session)
            complexity = estimate_session_complexity(session)
            
            session_data.append({
                'session_id': session.session_id,
                'escalated_at': session.escalated_at.isoformat() if session.escalated_at else None,
                'escalation_reason': session.escalation_reason,
                'priority': priority,
                'estimated_complexity': complexity,
                'latest_message': latest_message.message_content[:100] + '...' if latest_message and latest_message.message_content else 'No messages',
                'message_count': Message.query.filter_by(session_id=session.session_id).count(),
                'waiting_time': str(datetime.utcnow() - session.escalated_at) if session.escalated_at else 'Unknown'
            })
        
        return jsonify({'sessions': session_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/agents')
@super_admin_required
def api_agents():
    """API endpoint for agent information"""
    try:
        super_admin = SuperAdmin.query.get(session['super_admin_id'])
        agent_summary = super_admin.get_agent_workload_summary()
        
        return jsonify({'agents': agent_summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/assign-session', methods=['POST'])
@super_admin_required
def api_assign_session():
    """API endpoint to assign session to agent"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        agent_id = data.get('agent_id')
        
        if not session_id or not agent_id:
            return jsonify({'error': 'Session ID and Agent ID are required'}), 400
        
        # Get session and agent
        chat_session = ChatSession.query.filter_by(session_id=session_id).first()
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Allow super admin to reassign sessions
        if chat_session.assigned_agent_id:
            # If reassigning to the same agent, just update the record
            if chat_session.assigned_agent_id == agent.id:
                print(f"Super admin reassigning session {session_id} to same agent {agent.name}")
            else:
                # Reassigning to different agent - decrease old agent's session count
                old_agent = Agent.query.get(chat_session.assigned_agent_id)
                if old_agent and old_agent.current_sessions > 0:
                    old_agent.current_sessions -= 1
                    old_agent.status = 'available' if old_agent.current_sessions < old_agent.max_concurrent_sessions else 'busy'
                print(f"Super admin reassigning session {session_id} from {old_agent.name if old_agent else 'Unknown'} to {agent.name}")
        
        if not agent.can_take_session():
            return jsonify({'error': f'Agent {agent.name} cannot take more sessions'}), 400
        
        # Assign session
        chat_session.assigned_agent_id = agent.id
        chat_session.status = 'assigned'
        chat_session.updated_at = datetime.utcnow()
        
        # Update agent
        agent.current_sessions += 1
        agent.last_active = datetime.utcnow()
        
        # Check if agent session record already exists
        existing_agent_session = AgentSession.query.filter_by(
            agent_id=agent.id,
            session_id=session_id
        ).first()

        if existing_agent_session:
            # Update existing record
            existing_agent_session.assigned_by_super_admin = True
            existing_agent_session.super_admin_id = session['super_admin_id']
            existing_agent_session.assigned_at = datetime.utcnow()
            existing_agent_session.status = 'active'
        else:
            # Create new agent session record
            agent_session = AgentSession(
                agent_id=agent.id,
                session_id=session_id,
                assigned_by_super_admin=True,
                super_admin_id=session['super_admin_id']
            )
            db.session.add(agent_session)
        db.session.commit()
        
        # Send real-time notification to agent
        try:
            socketio = get_socketio()
            if socketio:
                notification_data = {
                    'session_id': session_id,
                    'assigned_by': 'Super Admin',
                    'assigned_at': datetime.utcnow().isoformat(),
                    'escalation_reason': chat_session.escalation_reason,
                    'priority': 'high'  # Super admin assignments are high priority
                }
                
                # Send to specific agent
                socketio.emit('session_assigned_by_super_admin', notification_data, room=f'agent_{agent.agent_id}')
                
                # Send to all agents for dashboard updates
                socketio.emit('session_assigned', {
                    'session_id': session_id,
                    'agent_id': agent.agent_id,
                    'agent_name': agent.name,
                    'assigned_by_super_admin': True
                }, room='agents')
                
                print(f"📢 Super admin assigned session {session_id} to {agent.name}")
        except Exception as e:
            print(f"Failed to send assignment notification: {e}")
        
        return jsonify({
            'message': f'Session assigned to {agent.name} successfully',
            'agent_name': agent.name,
            'session_id': session_id,
            'assigned_by_super_admin': True
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/agent-details/<agent_id>')
@super_admin_required
def api_agent_details(agent_id):
    """Get detailed information about an agent"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Get agent's current sessions
        current_sessions = AgentSession.query.filter_by(
            agent_id=agent.id,
            status='active'
        ).all()
        
        session_details = []
        for agent_session in current_sessions:
            chat_session = ChatSession.query.filter_by(
                session_id=agent_session.session_id
            ).first()
            
            if chat_session:
                session_details.append({
                    'session_id': chat_session.session_id,
                    'escalated_at': chat_session.escalated_at.isoformat() if chat_session.escalated_at else None,
                    'escalation_reason': chat_session.escalation_reason,
                    'assigned_at': agent_session.assigned_at.isoformat() if agent_session.assigned_at else None,
                    'assigned_by_super_admin': agent_session.assigned_by_super_admin
                })
        
        return jsonify({
            'agent': agent.to_dict(),
            'current_sessions': session_details,
            'session_count': len(session_details)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/reset-agent-password', methods=['POST'])
@super_admin_required
def api_reset_agent_password():
    """API endpoint to reset agent password"""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        
        if not agent_id:
            return jsonify({'error': 'Agent ID is required'}), 400
        
        # Get the agent
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Reset the password
        agent.reset_password()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Password reset successful for {agent.name}. Agent must set new password on next login.',
            'agent_name': agent.name,
            'agent_id': agent.agent_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/manage-agents')
@super_admin_required
def manage_agents():
    """Super admin agent management page"""
    super_admin = SuperAdmin.query.get(session['super_admin_id'])
    
    # Get all agents
    agents = Agent.query.filter_by(is_active=True).all()
    
    return render_template('super_admin/manage_agents.html',
                         super_admin=super_admin,
                         agents=agents)

# Add user management routes
@super_admin_bp.route('/users')
@super_admin_required
def user_management():
    """User management page"""
    from .models import UserProfile, Student

    # Get all user profiles with optional student information (left join)
    profiles = db.session.query(UserProfile, Student).outerjoin(
        Student, UserProfile.student_id == Student.id
    ).order_by(UserProfile.created_at.desc()).all()

    return render_template('super_admin/user_management.html', profiles=profiles)

@super_admin_bp.route('/api/users')
@super_admin_required
def api_get_users():
    """API endpoint to get user profiles with pagination"""
    try:
        from .models import UserProfile, Student
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)  # 10 users per page as requested
        search = request.args.get('search', '', type=str)
        favorite_filter = request.args.get('favorite', '', type=str)
        
        # Build base query - use left join to include profiles without students
        query = db.session.query(UserProfile, Student).outerjoin(
            Student, UserProfile.student_id == Student.id
        )

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    UserProfile.name.ilike(search_term),
                    UserProfile.phone.ilike(search_term),
                    UserProfile.email.ilike(search_term),
                    Student.email.ilike(search_term)
                )
            )
        
        # Apply favorite filter
        if favorite_filter == 'favorites':
            query = query.filter(UserProfile.is_favorite == True)
        elif favorite_filter == 'non-favorites':
            query = query.filter(UserProfile.is_favorite == False)
        
        # Order by creation date (newest first)
        query = query.order_by(UserProfile.created_at.desc())
        
        # Apply pagination
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        users_data = []
        for profile, student in paginated.items:
            # Use profile email if available, otherwise student email, otherwise '-'
            email = profile.email or (student.email if student else '-')
            users_data.append({
                'id': profile.id,
                'name': profile.name,
                'phone': profile.phone,
                'email': email,
                'is_favorite': profile.is_favorite,
                'created_at': profile.created_at.isoformat(),
                'student_id': student.id if student else None,
                'last_login': student.last_login.isoformat() if student and student.last_login else None
            })
        
        # Calculate stats
        total_users = paginated.total
        favorite_users = db.session.query(UserProfile).filter_by(is_favorite=True).count()

        # Calculate new users today
        from datetime import date
        today = date.today()
        new_today = db.session.query(UserProfile).filter(
            db.func.date(UserProfile.created_at) == today
        ).count()

        # Calculate verified phones (assuming all profiles have verified phones)
        verified_phones = total_users

        return jsonify({
            'users': users_data,
            'current_page': paginated.page,
            'total_pages': paginated.pages,
            'total': paginated.total,
            'pagination': {
                'page': paginated.page,
                'pages': paginated.pages,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
                'next_num': paginated.next_num,
                'prev_num': paginated.prev_num
            },
            'stats': {
                'total_users': total_users,
                'favorite_users': favorite_users,
                'new_today': new_today,
                'verified_phones': verified_phones
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/users/<int:profile_id>/toggle-favorite', methods=['POST'])
@super_admin_required
def api_toggle_user_favorite(profile_id):
    """API endpoint to toggle user favorite status"""
    try:
        from .models import UserProfile
        
        profile = UserProfile.query.get(profile_id)
        if not profile:
            return jsonify({'error': 'User profile not found'}), 404
        
        profile.is_favorite = not profile.is_favorite
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_favorite': profile.is_favorite,
            'message': f'User {"added to" if profile.is_favorite else "removed from"} favorites'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/users/export-excel')
@super_admin_required
def api_export_users_excel():
    """API endpoint to export users to Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        from flask import send_file
        import os
        from .models import UserProfile, Student

        # Get all user profiles with student information
        profiles = db.session.query(UserProfile, Student).outerjoin(
            Student, UserProfile.student_id == Student.id
        ).order_by(UserProfile.created_at.desc()).all()

        # Prepare data for Excel
        excel_data = []
        for profile, student in profiles:
            email = profile.email or (student.email if student else '-')
            excel_data.append({
                'Name': profile.name,
                'Phone': profile.phone,
                'Email': email,
                'Is Favorite': 'Yes' if profile.is_favorite else 'No',
                'Registration Date': profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Last Login': student.last_login.strftime('%Y-%m-%d %H:%M:%S') if student and student.last_login else 'Never'
            })

        # Create DataFrame
        df = pd.DataFrame(excel_data)

        # Create user_data directory if it doesn't exist
        user_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')
        os.makedirs(user_data_dir, exist_ok=True)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Users', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Users']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'users_export_{timestamp}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except ImportError:
        return jsonify({'error': 'pandas and openpyxl are required for Excel export. Please install them.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/users/clear-non-favorites', methods=['POST'])
@super_admin_required
def api_clear_non_favorites():
    """API endpoint to clear all non-favorite users"""
    try:
        from .models import UserProfile

        # Count non-favorite users
        non_favorite_count = UserProfile.query.filter_by(is_favorite=False).count()

        if non_favorite_count == 0:
            return jsonify({
                'success': True,
                'message': 'No non-favorite users to clear',
                'deleted_count': 0
            })

        # Delete non-favorite users
        deleted_count = UserProfile.query.filter_by(is_favorite=False).delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully cleared {deleted_count} non-favorite users',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def calculate_session_priority(session):
    """Calculate session priority (1-5, 5 being highest)"""
    priority = 1
    
    if session.escalated_at:
        # Higher priority for longer waiting sessions
        waiting_time = datetime.utcnow() - session.escalated_at
        if waiting_time > timedelta(hours=2):
            priority += 2
        elif waiting_time > timedelta(hours=1):
            priority += 1
    
    # Check for urgent keywords
    if session.escalation_reason:
        urgent_keywords = ['urgent', 'emergency', 'immediate', 'asap', 'critical']
        if any(keyword in session.escalation_reason.lower() for keyword in urgent_keywords):
            priority += 2
    
    return min(priority, 5)

def estimate_session_complexity(session):
    """Estimate session complexity"""
    message_count = Message.query.filter_by(session_id=session.session_id).count()
    
    if message_count > 10:
        return 'High'
    elif message_count > 5:
        return 'Medium'
    else:
        return 'Low'

@super_admin_bp.route('/api/clear-pending-sessions', methods=['POST'])
@super_admin_required
def api_clear_pending_sessions():
    """API endpoint to clear all pending sessions"""
    try:
        # Get all pending sessions
        pending_sessions = ChatSession.query.filter_by(
            requires_human=True,
            status='escalated',
            assigned_agent_id=None
        ).all()

        cleared_count = len(pending_sessions)

        if cleared_count == 0:
            return jsonify({
                'success': True,
                'message': 'No pending sessions to clear',
                'cleared_count': 0
            })

        # Clear pending sessions by marking them as resolved
        for session in pending_sessions:
            session.status = 'resolved'
            session.requires_human = False
            session.updated_at = datetime.utcnow()

            # Add a system message indicating the session was cleared
            system_message = Message(
                session_id=session.session_id,
                sender_type='system',
                message_content='Session cleared by Super Admin - marked as resolved',
                timestamp=datetime.utcnow()
            )
            db.session.add(system_message)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully cleared {cleared_count} pending sessions',
            'cleared_count': cleared_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/reset-agent-status', methods=['POST'])
@super_admin_required
def api_reset_agent_status():
    """API endpoint to reset all agent statuses and sessions"""
    try:
        # Get all agents
        agents = Agent.query.all()

        reset_count = len(agents)
        total_sessions_cleared = 0

        if reset_count == 0:
            return jsonify({
                'success': True,
                'message': 'No agents to reset',
                'reset_count': 0,
                'sessions_cleared': 0
            })

        # Reset all agents
        for agent in agents:
            # Count current sessions before reset
            total_sessions_cleared += agent.current_sessions

            # Reset agent status
            agent.current_sessions = 0
            agent.status = 'offline'  # Set to offline, they need to login to be available
            agent.last_active = datetime.utcnow()

        # Also clear any active agent sessions
        active_agent_sessions = AgentSession.query.filter_by(status='active').all()
        for agent_session in active_agent_sessions:
            agent_session.status = 'completed'
            agent_session.ended_at = datetime.utcnow()

        # Reset any assigned chat sessions back to escalated
        assigned_sessions = ChatSession.query.filter(
            ChatSession.assigned_agent_id.isnot(None),
            ChatSession.status == 'assigned'
        ).all()

        for session in assigned_sessions:
            session.assigned_agent_id = None
            session.status = 'escalated'
            session.updated_at = datetime.utcnow()

            # Add a system message
            system_message = Message(
                session_id=session.session_id,
                sender_type='system',
                message_content='Session reset by Super Admin - returned to pending queue',
                timestamp=datetime.utcnow()
            )
            db.session.add(system_message)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully reset {reset_count} agents and cleared {total_sessions_cleared} active sessions',
            'reset_count': reset_count,
            'sessions_cleared': total_sessions_cleared,
            'reassigned_sessions': len(assigned_sessions)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/daily-reset', methods=['POST'])
@super_admin_required
def api_daily_reset():
    """API endpoint for daily reset (can be called manually or by scheduler)"""
    try:
        # Reset agent status
        agents = Agent.query.all()
        for agent in agents:
            agent.current_sessions = 0
            agent.status = 'offline'  # Set to offline, they need to login to be available
            agent.last_active = datetime.utcnow()

        # Clear pending sessions
        pending_sessions = ChatSession.query.filter_by(
            requires_human=True,
            status='escalated',
            assigned_agent_id=None
        ).all()

        for session in pending_sessions:
            session.status = 'resolved'
            session.requires_human = False
            session.updated_at = datetime.utcnow()

            # Add system message
            system_message = Message(
                session_id=session.session_id,
                sender_type='system',
                message_content='Daily reset - session automatically resolved',
                timestamp=datetime.utcnow()
            )
            db.session.add(system_message)

        # Complete active agent sessions
        active_agent_sessions = AgentSession.query.filter_by(status='active').all()
        for agent_session in active_agent_sessions:
            agent_session.status = 'completed'
            agent_session.ended_at = datetime.utcnow()

        # Reset assigned sessions
        assigned_sessions = ChatSession.query.filter(
            ChatSession.assigned_agent_id.isnot(None),
            ChatSession.status == 'assigned'
        ).all()

        for session in assigned_sessions:
            session.assigned_agent_id = None
            session.status = 'resolved'
            session.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Daily reset completed successfully',
            'agents_reset': len(agents),
            'pending_sessions_cleared': len(pending_sessions),
            'active_sessions_completed': len(active_agent_sessions),
            'assigned_sessions_reset': len(assigned_sessions),
            'reset_time': datetime.utcnow().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/scheduler-status')
@super_admin_required
def api_scheduler_status():
    """API endpoint to get scheduler status"""
    try:
        from .daily_scheduler import get_scheduler_status
        status = get_scheduler_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/add-agent', methods=['POST'])
@super_admin_required
def api_add_agent():
    """API endpoint to add a new agent"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'email', 'specialization']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.title()} is required'}), 400

        name = data.get('name').strip()
        email = data.get('email').strip().lower()
        specialization = data.get('specialization').strip()
        max_concurrent_sessions = int(data.get('max_concurrent_sessions', 3))

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Check if email already exists
        existing_agent = Agent.query.filter_by(email=email).first()
        if existing_agent:
            return jsonify({'error': 'An agent with this email already exists'}), 400

        # Generate unique agent_id
        import uuid
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        # Ensure agent_id is unique
        while Agent.query.filter_by(agent_id=agent_id).first():
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        # Create new agent
        new_agent = Agent(
            agent_id=agent_id,
            name=name,
            email=email,
            specialization=specialization,
            max_concurrent_sessions=max_concurrent_sessions,
            status='offline',  # Start as offline
            is_active=True
        )

        db.session.add(new_agent)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Agent {name} added successfully',
            'agent_id': agent_id,
            'agent': {
                'id': new_agent.id,
                'agent_id': agent_id,
                'name': name,
                'email': email,
                'specialization': specialization,
                'max_concurrent_sessions': max_concurrent_sessions,
                'status': 'offline'
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/delete-agent', methods=['DELETE'])
@super_admin_required
def api_delete_agent():
    """API endpoint to delete an agent"""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')

        if not agent_id:
            return jsonify({'error': 'Agent ID is required'}), 400

        # Find the agent
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        agent_name = agent.name

        # Check if agent has active sessions
        active_sessions = ChatSession.query.filter_by(
            assigned_agent_id=agent.id,
            status='assigned'
        ).count()

        if active_sessions > 0:
            return jsonify({
                'error': f'Cannot delete agent {agent_name}. They have {active_sessions} active session(s). Please reassign or complete these sessions first.'
            }), 400

        # End any agent sessions
        agent_sessions = AgentSession.query.filter_by(agent_id=agent.id, status='active').all()
        for session in agent_sessions:
            session.status = 'completed'
            session.ended_at = datetime.utcnow()

        # Remove agent from any assigned sessions (set to None)
        assigned_sessions = ChatSession.query.filter_by(assigned_agent_id=agent.id).all()
        for session in assigned_sessions:
            session.assigned_agent_id = None
            session.status = 'escalated'  # Return to pending queue
            session.updated_at = datetime.utcnow()

            # Add system message
            system_message = Message(
                session_id=session.session_id,
                sender_type='system',
                message_content=f'Agent {agent_name} was deleted - session returned to queue',
                timestamp=datetime.utcnow()
            )
            db.session.add(system_message)

        # Delete the agent
        db.session.delete(agent)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Agent {agent_name} deleted successfully',
            'sessions_reassigned': len(assigned_sessions),
            'agent_sessions_ended': len(agent_sessions)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@super_admin_bp.route('/api/fix-stuck-sessions', methods=['POST'])
@super_admin_required
def api_fix_stuck_sessions():
    """API endpoint to fix sessions that are stuck in escalated state"""
    try:
        # Find sessions that are marked as requiring human but have no agent assigned
        # and are not actually escalated (probably from profile collection issues)
        stuck_sessions = ChatSession.query.filter(
            ChatSession.requires_human == True,
            ChatSession.assigned_agent_id == None,
            ChatSession.status != 'escalated'
        ).all()

        fixed_count = 0
        for session in stuck_sessions:
            # Check if this session has recent profile collection messages
            recent_messages = Message.query.filter_by(
                session_id=session.session_id
            ).order_by(Message.timestamp.desc()).limit(5).all()

            # If the session seems to be stuck in profile collection, reset it
            profile_keywords = ['name', 'phone', 'email', 'profile', 'collection']
            has_profile_messages = any(
                any(keyword in msg.message_content.lower() for keyword in profile_keywords)
                for msg in recent_messages
            )

            if has_profile_messages or session.status == 'active':
                session.requires_human = False
                session.status = 'active'
                session.escalation_reason = None
                session.escalated_at = None
                session.updated_at = datetime.utcnow()
                fixed_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Fixed {fixed_count} stuck sessions',
            'fixed_count': fixed_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

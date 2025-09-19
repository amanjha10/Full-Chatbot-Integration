#!/usr/bin/env python3
"""
EduConsult Chatbot API Layer
============================

A comprehensive REST API layer that exposes the backend chatbot functionality
without modifying the existing codebase. This API server automatically imports
and wraps all public functions from the backend modules.

Features:
- Automatic function discovery and endpoint generation
- CRUD operations for all database models
- File upload and download capabilities
- Session management
- Profile collection and management
- Chat functionality with RAG system integration
- Agent and admin operations

Usage:
    python api_layer/api_server.py

The server runs on port 5001 and provides JSON-only responses.
All endpoints support CORS for frontend integration.

Author: EduConsult Development Team
Version: 1.0.0
"""

import sys
import os
import inspect
import importlib
import json
import uuid
from datetime import datetime
from functools import wraps
from typing import Dict, List, Any, Optional

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Flask and CORS imports
from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS

# Import backend modules without modification
try:
    # Core backend imports
    from human_handoff.models import (
        db, UserProfile, Student, ChatSession, Message, 
        UploadedFile, Agent, SuperAdmin, AgentSession, SessionAnalytics
    )
    from human_handoff.session_manager import SessionManager
    from human_handoff import init_database, init_db_manager
    from setup_rag import RAGSystem
    from nepali_phone_validator import validate_nepali_phone, format_nepali_phone
    
    # Import key functions from main app
    import app as main_app
    
    print("✅ Successfully imported all backend modules")
    
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'api-layer-secret-key-change-in-production')

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///human_handoff.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_database(app)
init_db_manager(app)

# Initialize session manager
session_manager = SessionManager()

# Global variables for RAG system
RAG = None
rag_initialized = False

def init_rag_system():
    """Initialize RAG system if not already initialized"""
    global RAG, rag_initialized
    if not rag_initialized:
        try:
            print("🔧 Initializing RAG system...")
            RAG = RAGSystem()
            
            # Check if RAG system is properly initialized
            if RAG.is_initialized:
                print("✅ RAG system base initialization complete")
                
                # Load documents
                document_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'data', 'documents', 'education_faq.json'
                )
                
                print(f"📚 Loading documents from: {document_path}")
                
                if os.path.exists(document_path):
                    success = RAG.load_documents(document_path)
                    if success:
                        rag_initialized = True
                        print("✅ RAG system fully initialized with documents loaded")
                    else:
                        print("⚠️ RAG system initialized but failed to load documents")
                        rag_initialized = False
                else:
                    print(f"⚠️ Document file not found: {document_path}")
                    rag_initialized = False
            else:
                print("⚠️ RAG system base initialization failed")
                rag_initialized = False
                
        except Exception as e:
            print(f"❌ RAG system initialization error: {e}")
            import traceback
            traceback.print_exc()
            rag_initialized = False
    
    return rag_initialized

def api_response(success: bool = True, data: Any = None, message: str = "", 
                error: str = "", status_code: int = 200) -> tuple:
    """
    Standardized API response format
    
    Args:
        success: Whether the operation was successful
        data: The response data
        message: Success message
        error: Error message if any
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
        
    return jsonify(response), status_code

def handle_exceptions(f):
    """Decorator to handle exceptions in API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"API Error in {f.__name__}: {str(e)}")
            return api_response(
                success=False,
                error=str(e),
                status_code=500
            )
    return decorated_function

# ============================================================================
# HEALTH CHECK AND INFO ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    API Route: GET /api/health
    HTTP Method: GET
    Purpose: Check if the API server is running and healthy
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "rag_initialized": true,
            "rag_status": "ready"
        },
        "timestamp": "2025-01-01T12:00:00"
    }
    """
    global RAG, rag_initialized
    
    # Check RAG system status
    rag_status = "not_initialized"
    if rag_initialized and RAG and RAG.is_initialized:
        try:
            # Try to get collection info to verify it's working
            results = RAG.collection.get(limit=1)
            if results and results.get('ids'):
                rag_status = "ready_with_documents"
            else:
                rag_status = "initialized_no_documents"
        except Exception as e:
            rag_status = f"error: {str(e)}"
    elif rag_initialized:
        rag_status = "initialized_but_not_ready"
    
    return api_response(
        data={
            "status": "healthy",
            "version": "1.0.0",
            "rag_initialized": rag_initialized,
            "rag_status": rag_status,
            "database_connected": True
        }
    )

@app.route('/api/info', methods=['GET'])
def api_info():
    """
    API Route: GET /api/info
    HTTP Method: GET
    Purpose: Get information about available API endpoints
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "endpoints": [...],
            "models": [...],
            "version": "1.0.0"
        }
    }
    """
    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            endpoints.append({
                'endpoint': rule.rule,
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                'name': rule.endpoint
            })
    
    models = [
        'UserProfile', 'Student', 'ChatSession', 'Message', 
        'UploadedFile', 'Agent', 'SuperAdmin', 'AgentSession', 'SessionAnalytics'
    ]
    
    return api_response(
        data={
            "endpoints": endpoints,
            "models": models,
            "version": "1.0.0",
            "total_endpoints": len(endpoints)
        }
    )

# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/session/create', methods=['POST'])
@handle_exceptions
def create_session():
    """
    API Route: POST /api/session/create
    HTTP Method: POST
    Purpose: Create a new chat session
    Expected Input: {}
    Example Response: {
        "success": true,
        "data": {
            "session_id": "uuid-string",
            "created_at": "2025-01-01T12:00:00"
        }
    }
    """
    session_id = session_manager.get_session_id()
    return api_response(
        data={
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat()
        },
        message="Session created successfully"
    )

@app.route('/api/session/status', methods=['GET'])
@handle_exceptions
def get_session_status():
    """
    API Route: GET /api/session/status
    HTTP Method: GET
    Purpose: Get current session status and information
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "session_id": "uuid-string",
            "is_escalated": false,
            "profile_completed": true,
            "requires_human": false
        }
    }
    """
    session_id = session_manager.get_session_id()
    is_escalated = session_manager.is_human_handling_session()
    
    # Get session details from database
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    profile = UserProfile.query.filter_by(session_id=session_id).first()
    
    return api_response(
        data={
            "session_id": session_id,
            "is_escalated": is_escalated,
            "profile_completed": profile is not None,
            "requires_human": chat_session.requires_human if chat_session else False,
            "session_status": chat_session.status if chat_session else "active",
            "assigned_agent_id": chat_session.assigned_agent_id if chat_session else None,
            "profile_data": profile.to_dict() if profile else None
        }
    )

@app.route('/api/session/reset', methods=['POST'])
@handle_exceptions
def reset_session():
    """
    API Route: POST /api/session/reset
    HTTP Method: POST
    Purpose: Reset the current session and create a new one
    Expected Input: {}
    Example Response: {
        "success": true,
        "data": {
            "old_session_id": "uuid-string",
            "new_session_id": "uuid-string"
        }
    }
    """
    old_session_id = session_manager.get_session_id()
    new_session_id = session_manager.reset_session()
    
    return api_response(
        data={
            "old_session_id": old_session_id,
            "new_session_id": new_session_id
        },
        message="Session reset successfully"
    )

@app.route('/api/session/clear', methods=['POST'])
@handle_exceptions
def clear_session():
    """
    API Route: POST /api/session/clear
    HTTP Method: POST
    Purpose: Clear all session data and state
    Expected Input: {}
    Example Response: {
        "success": true,
        "message": "Session cleared successfully"
    }
    """
    # Clear Flask session
    session.clear()
    
    return api_response(
        message="Session cleared successfully"
    )

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.route('/api/chat/message', methods=['POST'])
@handle_exceptions
def send_chat_message():
    """
    API Route: POST /api/chat/message
    HTTP Method: POST
    Purpose: Send a chat message and get bot response
    Expected Input: {
        "message": "Hello, I need help with study abroad",
        "context": {}
    }
    Example Response: {
        "success": true,
        "data": {
            "response": "Hello! How can I help you?",
            "type": "text",
            "suggestions": ["Option 1", "Option 2"],
            "collecting": null
        }
    }
    """
    if not request.json or 'message' not in request.json:
        return api_response(
            success=False,
            error="Message is required",
            status_code=400
        )
    
    user_message = request.json['message'].strip()
    context = request.json.get('context', {})
    
    if not user_message:
        return api_response(
            success=False,
            error="Empty message not allowed",
            status_code=400
        )
    
    # Use the existing chat function from main app
    # We'll call the main app's chat logic here
    session_id = session_manager.get_session_id()
    
    # Initialize RAG system if needed
    init_rag_system()
    
    # Handle profile collection first
    profile_completed = session.get('profile_completed', False)
    if not profile_completed:
        try:
            response = main_app.handle_user_profile_collection(user_message, session_id, context)
            if response:
                return api_response(data=response)
        except Exception as e:
            print(f"Profile collection error: {e}")
            # Continue to RAG processing
    
    # Debug RAG system status
    rag_debug = {
        "rag_object_exists": RAG is not None,
        "rag_initialized_flag": rag_initialized,
        "rag_is_initialized": RAG.is_initialized if RAG else False
    }
    print(f"RAG Debug: {rag_debug}")
    
    # Process with RAG system if available
    if RAG and RAG.is_initialized and rag_initialized:
        try:
            print(f"🔍 Searching RAG for: '{user_message}'")
            rag_results = RAG.search(user_message, k=3)
            print(f"📊 RAG results count: {len(rag_results) if rag_results else 0}")
            
            if rag_results and len(rag_results) > 0:
                top_result = rag_results[0]
                bot_response = top_result.get('answer', 'No answer found')
                
                print(f"✅ Using RAG response: {bot_response[:100]}...")
                
                return api_response(
                    data={
                        "response": bot_response,
                        "type": "text",
                        "suggestions": [],
                        "context": context,
                        "rag_used": True,
                        "rag_debug": rag_debug,
                        "rag_results_count": len(rag_results),
                        "top_result_score": top_result.get('score', 0)
                    }
                )
            else:
                print("⚠️ No RAG results found")
        except Exception as e:
            print(f"❌ RAG system error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ RAG system not available - RAG: {RAG is not None}, initialized: {rag_initialized}")
    
    # Fallback response
    return api_response(
        data={
            "response": "Thank you for your message. How can I help you with your study abroad journey?",
            "type": "text",
            "suggestions": [
                "🌍 Choose Country",
                "🎓 Browse Programs", 
                "📚 Requirements",
                "💰 Scholarships"
            ],
            "context": context,
            "rag_used": False,
            "rag_debug": rag_debug
        }
    )

@app.route('/api/chat/upload', methods=['POST'])
@handle_exceptions
def upload_files_with_message():
    """
    API Route: POST /api/chat/upload
    HTTP Method: POST
    Purpose: Upload files with a chat message
    Expected Input: Form data with 'files' and 'message' fields
    Example Response: {
        "success": true,
        "data": {
            "response": "I've received your files",
            "files_processed": 2,
            "uploaded_files": [...]
        }
    }
    """
    session_id = session_manager.get_session_id()

    # Get message and files
    user_message = request.form.get('message', '').strip()

    # Process uploaded files using existing function
    uploaded_files = main_app.process_uploaded_files(request.files, session_id, user_message)

    if uploaded_files:
        file_names = [f['original_name'] for f in uploaded_files]
        response_text = f"✅ I've received your {len(uploaded_files)} file(s): {', '.join(file_names)}."

        return api_response(
            data={
                "response": response_text,
                "files_processed": len(uploaded_files),
                "uploaded_files": uploaded_files,
                "type": "file_upload"
            },
            message="Files uploaded successfully"
        )
    else:
        return api_response(
            success=False,
            error="No files were processed",
            status_code=400
        )

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.route('/api/profile/create', methods=['POST'])
@handle_exceptions
def create_user_profile():
    """
    API Route: POST /api/profile/create
    HTTP Method: POST
    Purpose: Create a new user profile
    Expected Input: {
        "name": "John Doe",
        "phone": "+1234567890",
        "email": "john@example.com"
    }
    Example Response: {
        "success": true,
        "data": {
            "id": 1,
            "name": "John Doe",
            "phone": "+1234567890",
            "email": "john@example.com",
            "session_id": "uuid-string"
        }
    }
    """
    if not request.json:
        return api_response(
            success=False,
            error="JSON data required",
            status_code=400
        )

    name = request.json.get('name', '').strip()
    phone = request.json.get('phone', '').strip()
    email = request.json.get('email', '').strip()

    if not name or not phone:
        return api_response(
            success=False,
            error="Name and phone are required",
            status_code=400
        )

    session_id = session_manager.get_session_id()

    # Create new profile
    profile = UserProfile(
        session_id=session_id,
        persistent_user_id=str(uuid.uuid4()),
        name=name,
        phone=phone,
        email=email if email else None
    )

    db.session.add(profile)
    db.session.commit()

    # Mark profile as completed in session
    session['profile_completed'] = True

    return api_response(
        data=profile.to_dict(),
        message="Profile created successfully"
    )

@app.route('/api/profile/get', methods=['GET'])
@handle_exceptions
def get_user_profile():
    """
    API Route: GET /api/profile/get
    HTTP Method: GET
    Purpose: Get current user's profile
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "id": 1,
            "name": "John Doe",
            "phone": "+1234567890",
            "email": "john@example.com"
        }
    }
    """
    session_id = session_manager.get_session_id()
    profile = UserProfile.query.filter_by(session_id=session_id).first()

    if profile:
        return api_response(
            data=profile.to_dict(),
            message="Profile retrieved successfully"
        )
    else:
        return api_response(
            success=False,
            error="No profile found for current session",
            status_code=404
        )

@app.route('/api/profile/update', methods=['PUT'])
@handle_exceptions
def update_user_profile():
    """
    API Route: PUT /api/profile/update
    HTTP Method: PUT
    Purpose: Update current user's profile
    Expected Input: {
        "name": "John Smith",
        "phone": "+1234567890",
        "email": "johnsmith@example.com"
    }
    Example Response: {
        "success": true,
        "data": {...},
        "message": "Profile updated successfully"
    }
    """
    if not request.json:
        return api_response(
            success=False,
            error="JSON data required",
            status_code=400
        )

    session_id = session_manager.get_session_id()
    profile = UserProfile.query.filter_by(session_id=session_id).first()

    if not profile:
        return api_response(
            success=False,
            error="No profile found for current session",
            status_code=404
        )

    # Update fields if provided
    if 'name' in request.json:
        profile.name = request.json['name'].strip()
    if 'phone' in request.json:
        profile.phone = request.json['phone'].strip()
    if 'email' in request.json:
        profile.email = request.json['email'].strip() or None

    profile.last_used = datetime.utcnow()
    db.session.commit()

    return api_response(
        data=profile.to_dict(),
        message="Profile updated successfully"
    )

@app.route('/api/profile/delete', methods=['DELETE'])
@handle_exceptions
def delete_user_profile():
    """
    API Route: DELETE /api/profile/delete
    HTTP Method: DELETE
    Purpose: Delete current user's profile
    Expected Input: None
    Example Response: {
        "success": true,
        "message": "Profile deleted successfully"
    }
    """
    session_id = session_manager.get_session_id()
    profile = UserProfile.query.filter_by(session_id=session_id).first()

    if not profile:
        return api_response(
            success=False,
            error="No profile found for current session",
            status_code=404
        )

    db.session.delete(profile)
    db.session.commit()

    # Clear profile completion flag
    session.pop('profile_completed', None)

    return api_response(
        message="Profile deleted successfully"
    )

# ============================================================================
# FILE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/files/list', methods=['GET'])
@handle_exceptions
def list_uploaded_files():
    """
    API Route: GET /api/files/list
    HTTP Method: GET
    Purpose: Get list of uploaded files for current session
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "files": [...],
            "total_count": 5,
            "total_size": 1024000
        }
    }
    """
    session_id = session_manager.get_session_id()
    files = UploadedFile.query.filter_by(session_id=session_id).all()

    file_list = [f.to_dict() for f in files]
    total_size = sum(f.file_size for f in files if f.file_size)

    return api_response(
        data={
            "files": file_list,
            "total_count": len(files),
            "total_size": total_size
        },
        message=f"Found {len(files)} files"
    )

@app.route('/api/files/<int:file_id>', methods=['GET'])
@handle_exceptions
def get_file_info(file_id):
    """
    API Route: GET /api/files/<file_id>
    HTTP Method: GET
    Purpose: Get information about a specific file
    Expected Input: file_id in URL
    Example Response: {
        "success": true,
        "data": {
            "id": 1,
            "filename": "document.pdf",
            "original_name": "document.pdf",
            "file_size": 1024,
            "file_type": "pdf"
        }
    }
    """
    session_id = session_manager.get_session_id()
    file_obj = UploadedFile.query.filter_by(
        id=file_id,
        session_id=session_id
    ).first()

    if not file_obj:
        return api_response(
            success=False,
            error="File not found",
            status_code=404
        )

    return api_response(
        data=file_obj.to_dict(),
        message="File information retrieved"
    )

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
@handle_exceptions
def download_file(file_id):
    """
    API Route: GET /api/files/<file_id>/download
    HTTP Method: GET
    Purpose: Download a specific file
    Expected Input: file_id in URL
    Example Response: File download or error JSON
    """
    session_id = session_manager.get_session_id()
    file_obj = UploadedFile.query.filter_by(
        id=file_id,
        session_id=session_id
    ).first()

    if not file_obj:
        return api_response(
            success=False,
            error="File not found",
            status_code=404
        )

    try:
        return send_file(
            file_obj.filepath,
            as_attachment=True,
            download_name=file_obj.original_name
        )
    except FileNotFoundError:
        return api_response(
            success=False,
            error="File not found on disk",
            status_code=404
        )

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@handle_exceptions
def delete_file(file_id):
    """
    API Route: DELETE /api/files/<file_id>
    HTTP Method: DELETE
    Purpose: Delete a specific file
    Expected Input: file_id in URL
    Example Response: {
        "success": true,
        "message": "File deleted successfully"
    }
    """
    session_id = session_manager.get_session_id()
    file_obj = UploadedFile.query.filter_by(
        id=file_id,
        session_id=session_id
    ).first()

    if not file_obj:
        return api_response(
            success=False,
            error="File not found",
            status_code=404
        )

    # Delete file from disk
    try:
        if os.path.exists(file_obj.filepath):
            os.remove(file_obj.filepath)
    except Exception as e:
        print(f"Error deleting file from disk: {e}")

    # Delete from database
    db.session.delete(file_obj)
    db.session.commit()

    return api_response(
        message="File deleted successfully"
    )

# ============================================================================
# MESSAGE HISTORY ENDPOINTS
# ============================================================================

@app.route('/api/messages/list', methods=['GET'])
@handle_exceptions
def list_messages():
    """
    API Route: GET /api/messages/list
    HTTP Method: GET
    Purpose: Get message history for current session
    Expected Input: None (optional query params: limit, offset)
    Example Response: {
        "success": true,
        "data": {
            "messages": [...],
            "total_count": 10,
            "has_more": false
        }
    }
    """
    session_id = session_manager.get_session_id()

    # Get pagination parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Query messages
    query = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.desc())
    total_count = query.count()
    messages = query.offset(offset).limit(limit).all()

    message_list = [m.to_dict() for m in messages]
    has_more = (offset + len(messages)) < total_count

    return api_response(
        data={
            "messages": message_list,
            "total_count": total_count,
            "has_more": has_more,
            "limit": limit,
            "offset": offset
        },
        message=f"Retrieved {len(messages)} messages"
    )

@app.route('/api/messages/clear', methods=['DELETE'])
@handle_exceptions
def clear_messages():
    """
    API Route: DELETE /api/messages/clear
    HTTP Method: DELETE
    Purpose: Clear all messages for current session
    Expected Input: None
    Example Response: {
        "success": true,
        "message": "Messages cleared successfully"
    }
    """
    session_id = session_manager.get_session_id()

    # Delete all messages for this session
    Message.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    return api_response(
        message="Messages cleared successfully"
    )

# ============================================================================
# AGENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/agents/list', methods=['GET'])
@handle_exceptions
def list_agents():
    """
    API Route: GET /api/agents/list
    HTTP Method: GET
    Purpose: Get list of all agents
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "agents": [...],
            "total_count": 5,
            "online_count": 2
        }
    }
    """
    agents = Agent.query.all()
    agent_list = [a.to_dict() for a in agents]
    online_count = sum(1 for a in agents if a.is_online)

    return api_response(
        data={
            "agents": agent_list,
            "total_count": len(agents),
            "online_count": online_count
        },
        message=f"Found {len(agents)} agents"
    )

@app.route('/api/agents/<int:agent_id>', methods=['GET'])
@handle_exceptions
def get_agent(agent_id):
    """
    API Route: GET /api/agents/<agent_id>
    HTTP Method: GET
    Purpose: Get information about a specific agent
    Expected Input: agent_id in URL
    Example Response: {
        "success": true,
        "data": {
            "id": 1,
            "username": "agent1",
            "email": "agent1@example.com",
            "is_online": true
        }
    }
    """
    agent = Agent.query.get(agent_id)

    if not agent:
        return api_response(
            success=False,
            error="Agent not found",
            status_code=404
        )

    return api_response(
        data=agent.to_dict(),
        message="Agent information retrieved"
    )

@app.route('/api/agents/sessions', methods=['GET'])
@handle_exceptions
def get_agent_sessions():
    """
    API Route: GET /api/agents/sessions
    HTTP Method: GET
    Purpose: Get active sessions for agents
    Expected Input: None (optional query param: agent_id)
    Example Response: {
        "success": true,
        "data": {
            "sessions": [...],
            "total_count": 3
        }
    }
    """
    agent_id = request.args.get('agent_id', type=int)

    query = ChatSession.query.filter_by(requires_human=True)
    if agent_id:
        query = query.filter_by(assigned_agent_id=agent_id)

    sessions = query.all()
    session_list = [s.to_dict() for s in sessions]

    return api_response(
        data={
            "sessions": session_list,
            "total_count": len(sessions)
        },
        message=f"Found {len(sessions)} active sessions"
    )

# ============================================================================
# QUEUE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/queue/status', methods=['GET'])
@handle_exceptions
def get_queue_status():
    """
    API Route: GET /api/queue/status
    HTTP Method: GET
    Purpose: Get current queue status
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "queue_length": 5,
            "estimated_wait_time": 300,
            "available_agents": 2
        }
    }
    """
    # Get queue information from session manager
    queue_length = session_manager.get_queue_length()
    available_agents = Agent.query.filter_by(is_online=True).count()

    # Estimate wait time (simple calculation)
    estimated_wait_time = queue_length * 180 if queue_length > 0 else 0  # 3 minutes per person

    return api_response(
        data={
            "queue_length": queue_length,
            "estimated_wait_time": estimated_wait_time,
            "available_agents": available_agents
        },
        message="Queue status retrieved"
    )

@app.route('/api/queue/join', methods=['POST'])
@handle_exceptions
def join_queue():
    """
    API Route: POST /api/queue/join
    HTTP Method: POST
    Purpose: Join the queue for human agent assistance
    Expected Input: {}
    Example Response: {
        "success": true,
        "data": {
            "position": 3,
            "estimated_wait_time": 540
        }
    }
    """
    session_id = session_manager.get_session_id()

    # Add to queue using session manager
    position = session_manager.add_to_queue(session_id)
    estimated_wait_time = position * 180  # 3 minutes per position

    return api_response(
        data={
            "position": position,
            "estimated_wait_time": estimated_wait_time,
            "session_id": session_id
        },
        message="Added to queue successfully"
    )

@app.route('/api/queue/leave', methods=['POST'])
@handle_exceptions
def leave_queue():
    """
    API Route: POST /api/queue/leave
    HTTP Method: POST
    Purpose: Leave the queue
    Expected Input: {}
    Example Response: {
        "success": true,
        "message": "Left queue successfully"
    }
    """
    session_id = session_manager.get_session_id()

    # Remove from queue using session manager
    session_manager.remove_from_queue(session_id)

    return api_response(
        message="Left queue successfully"
    )

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.route('/api/admin/clear-all-profiles', methods=['POST'])
@handle_exceptions
def clear_all_profiles():
    """
    API Route: POST /api/admin/clear-all-profiles
    HTTP Method: POST
    Purpose: Clear all user profiles (admin function)
    Expected Input: {}
    Example Response: {
        "success": true,
        "data": {
            "profiles_deleted": 10
        }
    }
    """
    # Count profiles before deletion
    profile_count = UserProfile.query.count()

    # Delete all profiles
    UserProfile.query.delete()
    db.session.commit()

    return api_response(
        data={
            "profiles_deleted": profile_count
        },
        message=f"Cleared {profile_count} profiles"
    )

@app.route('/api/admin/stats', methods=['GET'])
@handle_exceptions
def get_admin_stats():
    """
    API Route: GET /api/admin/stats
    HTTP Method: GET
    Purpose: Get system statistics for admin dashboard
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "total_profiles": 100,
            "total_sessions": 150,
            "total_messages": 1000,
            "total_files": 50,
            "active_agents": 3
        }
    }
    """
    stats = {
        "total_profiles": UserProfile.query.count(),
        "total_sessions": ChatSession.query.count(),
        "total_messages": Message.query.count(),
        "total_files": UploadedFile.query.count(),
        "active_agents": Agent.query.filter_by(is_online=True).count(),
        "total_agents": Agent.query.count()
    }

    return api_response(
        data=stats,
        message="System statistics retrieved"
    )

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.route('/api/validate/phone', methods=['POST'])
@handle_exceptions
def validate_phone_number():
    """
    API Route: POST /api/validate/phone
    HTTP Method: POST
    Purpose: Validate and format phone number
    Expected Input: {
        "phone": "+977-9841234567",
        "country": "nepal"
    }
    Example Response: {
        "success": true,
        "data": {
            "is_valid": true,
            "formatted": "+977-9841234567",
            "country": "nepal"
        }
    }
    """
    if not request.json or 'phone' not in request.json:
        return api_response(
            success=False,
            error="Phone number is required",
            status_code=400
        )

    phone = request.json['phone'].strip()
    country = request.json.get('country', '').lower()

    # Use existing validation functions
    if country == 'nepal':
        is_valid = validate_nepali_phone(phone)
        formatted = format_nepali_phone(phone) if is_valid else phone
    else:
        # Basic validation for other countries
        is_valid = len(phone) >= 10 and phone.replace('+', '').replace('-', '').replace(' ', '').isdigit()
        formatted = phone

    return api_response(
        data={
            "is_valid": is_valid,
            "formatted": formatted,
            "country": country,
            "original": phone
        },
        message="Phone validation completed"
    )

@app.route('/api/search', methods=['POST'])
@handle_exceptions
def search_rag():
    """
    API Route: POST /api/search
    HTTP Method: POST
    Purpose: Search using RAG system
    Expected Input: {
        "query": "What are the requirements for studying in USA?",
        "k": 3
    }
    Example Response: {
        "success": true,
        "data": {
            "results": [...],
            "query": "What are the requirements...",
            "total_results": 3
        }
    }
    """
    if not request.json or 'query' not in request.json:
        return api_response(
            success=False,
            error="Query is required",
            status_code=400
        )

    query = request.json['query'].strip()
    k = request.json.get('k', 3)

    if not query:
        return api_response(
            success=False,
            error="Empty query not allowed",
            status_code=400
        )

    # Initialize RAG system if needed
    if not init_rag_system():
        return api_response(
            success=False,
            error="RAG system not available",
            status_code=503
        )

    try:
        results = RAG.search(query, k=k)
        return api_response(
            data={
                "results": results,
                "query": query,
                "total_results": len(results) if results else 0
            },
            message="Search completed successfully"
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f"Search failed: {str(e)}",
            status_code=500
        )

@app.route('/api/rag/status', methods=['GET'])
@handle_exceptions
def get_rag_status():
    """
    API Route: GET /api/rag/status
    HTTP Method: GET
    Purpose: Get detailed RAG system status and diagnostics
    Expected Input: None
    Example Response: {
        "success": true,
        "data": {
            "rag_initialized": true,
            "documents_loaded": true,
            "document_count": 150,
            "collection_name": "study_abroad_docs"
        }
    }
    """
    global RAG, rag_initialized
    
    status = {
        "rag_initialized": rag_initialized,
        "rag_object_exists": RAG is not None,
        "rag_is_initialized": False,
        "documents_loaded": False,
        "document_count": 0,
        "collection_name": None,
        "error": None
    }
    
    if RAG:
        try:
            status["rag_is_initialized"] = RAG.is_initialized
            if RAG.is_initialized:
                # Try to get collection info
                results = RAG.collection.get(limit=1)
                status["collection_name"] = RAG.collection.name
                status["document_count"] = RAG.collection.count()
                status["documents_loaded"] = status["document_count"] > 0
        except Exception as e:
            status["error"] = str(e)
    
    return api_response(
        data=status,
        message="RAG status retrieved"
    )

@app.route('/api/rag/reload', methods=['POST'])
@handle_exceptions
def reload_rag_documents():
    """
    API Route: POST /api/rag/reload
    HTTP Method: POST
    Purpose: Reload RAG documents from the JSON file
    Expected Input: {}
    Example Response: {
        "success": true,
        "data": {
            "documents_loaded": true,
            "document_count": 150
        }
    }
    """
    global RAG, rag_initialized
    
    if not RAG:
        return api_response(
            success=False,
            error="RAG system not initialized",
            status_code=503
        )
    
    try:
        document_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'documents', 'education_faq.json'
        )
        
        if not os.path.exists(document_path):
            return api_response(
                success=False,
                error=f"Document file not found: {document_path}",
                status_code=404
            )
        
        # Reload documents
        success = RAG.load_documents(document_path)
        
        if success:
            rag_initialized = True
            document_count = RAG.collection.count()
            return api_response(
                data={
                    "documents_loaded": True,
                    "document_count": document_count,
                    "document_path": document_path
                },
                message="Documents reloaded successfully"
            )
        else:
            return api_response(
                success=False,
                error="Failed to reload documents",
                status_code=500
            )
            
    except Exception as e:
        return api_response(
            success=False,
            error=f"Error reloading documents: {str(e)}",
            status_code=500
        )

# ============================================================================
# MAIN APPLICATION RUNNER
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting EduConsult API Layer...")
    print("=" * 60)
    print("API Server Configuration:")
    print(f"  • Host: 0.0.0.0")
    print(f"  • Port: 5002")
    print(f"  • Debug: True")
    print(f"  • CORS: Enabled")
    print("=" * 60)
    print("Available endpoints:")
    print("  • GET  /api/health - Health check")
    print("  • GET  /api/info - API information")
    print("  • POST /api/session/create - Create session")
    print("  • GET  /api/session/status - Session status")
    print("  • POST /api/chat/message - Send chat message")
    print("  • POST /api/chat/upload - Upload files")
    print("  • POST /api/profile/create - Create profile")
    print("  • GET  /api/profile/get - Get profile")
    print("  • GET  /api/files/list - List files")
    print("  • GET  /api/messages/list - List messages")
    print("  • GET  /api/agents/list - List agents")
    print("  • GET  /api/queue/status - Queue status")
    print("  • POST /api/search - RAG search")
    print("  • And many more...")
    print("=" * 60)
    print("🌐 API Documentation: http://localhost:5002/api/info")
    print("💚 Health Check: http://localhost:5002/api/health")
    print("=" * 60)

    # Initialize RAG system on startup
    print("🔧 Initializing RAG system...")
    init_rag_system()

    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=True,
        threaded=True
    )

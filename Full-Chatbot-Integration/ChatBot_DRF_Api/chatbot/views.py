# chatbot/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from authentication.permissions import IsSuperAdmin
import uuid
import json
import re
import os

from .models import ChatSession, UserProfile, ChatMessage, UploadedFile, RAGDocument, ChatbotConfiguration
from .serializers import (
    ChatRequestSerializer, ChatResponseSerializer, UserProfileSerializer,
    ProfileCollectionRequestSerializer, PhoneValidationRequestSerializer,
    PhoneValidationResponseSerializer, ChatSessionSerializer, ChatMessageSerializer,
    FileUploadRequestSerializer, FileUploadResponseSerializer, UploadedFileSerializer,
    ChatbotConfigurationSerializer, ChatbotConfigurationUpdateSerializer
)
from .utils.phone_validator import validate_phone_number, validate_name, validate_email, validate_nepali_phone
from .utils.rag_system import rag_system
from .utils.file_handler import FileUploadHandler
from .utils.security import rate_limit, FileValidator, WebSocketAuth
from authentication.models import User
from admin_dashboard.models import Agent


def _auto_refresh_vectors():
    """Helper function to automatically refresh vector database"""
    try:
        import subprocess
        import sys
        refresh_script_path = os.path.join(settings.BASE_DIR, 'refresh_vectors.py')

        if os.path.exists(refresh_script_path):
            result = subprocess.run([
                sys.executable, refresh_script_path
            ], capture_output=True, text=True, cwd=settings.BASE_DIR)

            if result.returncode == 0:
                print("✅ Vector database auto-refreshed successfully")
            else:
                print(f"⚠️ Vector refresh warning: {result.stderr}")
        else:
            print("⚠️ Vector refresh script not found")
    except Exception as e:
        print(f"⚠️ Auto vector refresh failed: {e}")
        raise e


# Constants from Flask reference
COUNTRIES = [
    'United States', 'Canada', 'United Kingdom', 'Australia',
    'Germany', 'France', 'Netherlands', 'New Zealand',
    'Singapore', 'Ireland', 'Japan', 'South Korea', 'Other'
]

COUNTRY_CODES = [
    {'code': '+977', 'country': 'Nepal', 'flag': '🇳🇵'},
    {'code': '+91', 'country': 'India', 'flag': '🇮🇳'},
    {'code': '+1', 'country': 'United States/Canada', 'flag': '🇺🇸🇨🇦'},
    {'code': '+44', 'country': 'United Kingdom', 'flag': '🇬🇧'},
    {'code': '+61', 'country': 'Australia', 'flag': '🇦🇺'},
    {'code': '+49', 'country': 'Germany', 'flag': '🇩🇪'},
    {'code': '+33', 'country': 'France', 'flag': '🇫🇷'},
    {'code': '+31', 'country': 'Netherlands', 'flag': '🇳🇱'},
    {'code': '+64', 'country': 'New Zealand', 'flag': '🇳🇿'},
    {'code': '+65', 'country': 'Singapore', 'flag': '🇸🇬'},
    {'code': '+353', 'country': 'Ireland', 'flag': '🇮🇪'},
    {'code': '+81', 'country': 'Japan', 'flag': '🇯🇵'},
    {'code': '+86', 'country': 'China', 'flag': '🇨🇳'},
    {'code': '+880', 'country': 'Bangladesh', 'flag': '🇧🇩'},
    {'code': '+94', 'country': 'Sri Lanka', 'flag': '🇱🇰'}
]

GREETING_KEYWORDS = [
    'hello', 'hi', 'hey', 'how are you', 'good morning', 'good afternoon',
    'good evening', 'greetings', "what's up", "how's it going", 'namaste'
]

def get_company_id_from_request(request):
    """Extract company_id from request - either from JWT token or request data"""
    company_id = None
    
    # First try to get from request data (for visitor chats with company context)
    if hasattr(request, 'data') and 'company_id' in request.data:
        company_id = request.data.get('company_id')
    
    # If not found, try to extract from JWT token (for agent/admin requests)
    if not company_id:
        try:
            jwt_auth = JWTAuthentication()
            auth_header = jwt_auth.get_header(request)
            if auth_header:
                raw_token = jwt_auth.get_raw_token(auth_header)
                if raw_token:
                    validated_token = jwt_auth.get_validated_token(raw_token)
                    user_id = validated_token['user_id']
                    user = User.objects.get(id=user_id)
                    
                    if user.role == User.Role.AGENT:
                        # Get company_id from agent profile
                        agent = Agent.objects.get(user=user)
                        company_id = agent.company_id
                    elif user.role in [User.Role.ADMIN, User.Role.SUPERADMIN]:
                        # Get company_id from user
                        company_id = user.company_id
        except Exception:
            # Catch all exceptions to prevent 500 errors
            pass
    
    return company_id

def get_or_create_session(session_id=None, company_id=None):
    """Get existing session or create new one with company_id"""
    if session_id and company_id:
        try:
            return ChatSession.objects.get(session_id=session_id, company_id=company_id)
        except ChatSession.DoesNotExist:
            pass
    
    # Create new session - company_id is required for new sessions
    if not company_id:
        raise ValueError("company_id is required for creating new chat sessions")
    
    new_session_id = str(uuid.uuid4())
    return ChatSession.objects.create(session_id=new_session_id, company_id=company_id)

def is_greeting_query(user_message):
    """Check if a message is a greeting"""
    msg = user_message.lower().strip()
    if msg in GREETING_KEYWORDS:
        return True
    for greeting in GREETING_KEYWORDS:
        if msg.startswith(greeting + ' '):
            return True
    return False

def get_rag_response(user_input, company_id=None):
    """
    Query RAG system for document-based answers with company priority

    Args:
        user_input: User's question
        company_id: Company ID for prioritized search

    Returns:
        tuple: (result_dict, similarity_score)
    """
    try:
        result = rag_system.get_best_answer(user_input, min_score=0.2, company_id=company_id)
        if result:
            # Use similarity score if available, otherwise fall back to score
            score = result.get('similarity', result.get('score', 0))
            return result, score
        return None, 0.0
    except Exception as e:
        print(f"Error in RAG response: {e}")
        return None, 0.0

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def chat_message_view(request):
    """
    Handle chat messages from users
    POST /api/chatbot/chat/
    
    Request:
    {
        "message": "Hello, I want to study abroad",
        "session_id": "optional_session_id",
        "context": "Initial conversation",
        "company_id": "COMP_123" // Required for visitor chats, or extracted from JWT for agents
    }
    
    Response:
    {
        "response": "Hello! I'd be happy to help...",
        "suggestions": ["🌍 Choose Country", "🎓 Browse Programs"],
        "type": "bot_response",
        "session_id": "session_uuid",
        "escalated": false
    }
    """

    # Handle GET request for API information
    if request.method == 'GET':
        return Response({
            'message': 'Chat API is working!',
            'method': 'POST',
            'endpoint': '/api/chatbot/chat/',
            'required_fields': ['message', 'company_id'],
            'optional_fields': ['session_id', 'file'],
            'example_request': {
                'message': 'Hello, I want to study abroad',
                'company_id': 'TEST001'
            }
        })

    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user_message = serializer.validated_data.get('message', '')
    session_id = serializer.validated_data.get('session_id')
    context = serializer.validated_data.get('context', 'Initial conversation')
    attachment_ids = serializer.validated_data.get('attachment_ids', [])
    
    # Extract company_id from request (either from data or JWT token)
    company_id = get_company_id_from_request(request)
    print(f"DEBUG: Chat request - company_id: {company_id}, message: {user_message[:50]}...")

    if not company_id:
        print("DEBUG: No company_id found in request")
        return Response({
            'error': 'company_id is required. Please provide company_id in request data or authenticate with valid JWT token.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create session with company isolation
    try:
        chat_session = get_or_create_session(session_id, company_id)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user message with attachments
    user_message_obj = ChatMessage.objects.create(
        session=chat_session,
        message_type='user',
        content=user_message if user_message else None,
        metadata={'context': context, 'has_attachments': bool(attachment_ids)}
    )
    
    # Attach files if provided
    if attachment_ids:
        try:
            uploaded_files = UploadedFile.objects.filter(
                id__in=attachment_ids,
                session=chat_session,
                company_id=company_id
            )
            user_message_obj.attachments.set(uploaded_files)
        except Exception as e:
            return Response({
                'error': f'Failed to attach files: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update user activity if profile exists
    profile = chat_session.user_profile
    if profile:
        profile.update_last_used()

    # Check if session needs profile collection
    if not profile:
        print(f"DEBUG: No profile for session {chat_session.session_id}")
        print(f"DEBUG: Current collection state: {chat_session.profile_collection_state}")
        print(f"DEBUG: User message: '{user_message}'")

        # Handle profile collection for new users
        if chat_session.profile_collection_state == 'name':
            # Check if this is the first message (welcome already sent)
            bot_messages = ChatMessage.objects.filter(session=chat_session, message_type='bot').count()
            print(f"DEBUG: Bot messages count: {bot_messages}")

            if bot_messages == 0:
                # First message - send welcome and ask for name
                print("DEBUG: Sending welcome message")
                welcome_response = {
                    'response': "Hello! 👋 Welcome to EduConsult. I'm here to help you with your study abroad journey.<br><br>To get started, I'll need to collect some information. What's your full name?",
                    'suggestions': ['Example: John Doe'],
                    'type': 'profile_collection',
                    'collecting': 'name',
                    'session_id': chat_session.session_id
                }

                # Log bot response
                ChatMessage.objects.create(
                    session=chat_session,
                    message_type='bot',
                    content=welcome_response['response'],
                    metadata={'source': 'profile_collection', 'type': 'welcome'}
                )

                return Response(welcome_response)
        
        # Continue with profile collection
        print("DEBUG: Calling handle_profile_collection")
        profile_response = handle_profile_collection(user_message, chat_session)
        print(f"DEBUG: Profile response: {profile_response}")
        if profile_response:
            # Log bot response
            metadata = {
                'source': 'profile_collection', 
                'type': profile_response['type']
            }
            if 'collecting' in profile_response:
                metadata['collecting'] = profile_response['collecting']
            if 'temp_data' in profile_response:
                metadata['temp_data'] = profile_response['temp_data']
                
            ChatMessage.objects.create(
                session=chat_session,
                message_type='bot',
                content=profile_response['response'],
                metadata=metadata
            )
            profile_response['session_id'] = chat_session.session_id
            return Response(profile_response)
    
    # Check if session is escalated to human
    if hasattr(chat_session, 'handoff'):
        # Get the handoff session to find assigned agent
        handoff_session = chat_session.handoff
        
        # Broadcast message to assigned agent via WebSocket if agent is assigned
        if handoff_session.agent:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from django.utils import timezone
            
            channel_layer = get_channel_layer()
            
            # Prepare file attachment data for WebSocket
            file_data = {}
            if user_message_obj.attachments.exists():
                first_attachment = user_message_obj.attachments.first()
                file_data = {
                    'file_url': first_attachment.get_file_url(),
                    'file_name': first_attachment.original_name,
                    'file_type': first_attachment.file_type
                }
            
            # Send to agent dashboard WebSocket
            async_to_sync(channel_layer.group_send)(
                f'agent_{handoff_session.agent.id}',
                {
                    'type': 'chat_message',
                    'data': {
                        'session_id': chat_session.session_id,
                        'message': user_message,
                        'sender': 'user',
                        'sender_name': chat_session.user_profile.name if chat_session.user_profile else 'User',
                        'timestamp': str(timezone.now()),
                        **file_data
                    }
                }
            )
            
            # Also send to chat WebSocket for real-time user interface
            async_to_sync(channel_layer.group_send)(
                f'chat_{company_id}_{chat_session.session_id}',
                {
                    'type': 'chat_message',
                    'message_id': user_message_obj.id,
                    'sender_type': 'user',
                    'message': user_message,
                    'timestamp': user_message_obj.timestamp.isoformat(),
                    'sender_name': chat_session.user_profile.name if chat_session.user_profile else 'User',
                    **file_data
                }
            )
        
        return Response({
            'response': '',
            'suggestions': [],
            'type': 'human_handling',
            'escalated': True,
            'session_id': chat_session.session_id
        })
    
    # Handle menu navigation
    if user_message.lower() in ['explore countries', 'choose country', '🌍 choose country']:
        response = {
            'response': "Here are the top study destinations. Which country interests you?",
            'suggestions': [
                '🇺🇸 United States', '🇨🇦 Canada', '🇬🇧 United Kingdom',
                '🇦🇺 Australia', '🇩🇪 Germany', 'More countries', '🎓 Browse by Field'
            ],
            'type': 'country_selection',
            'session_id': chat_session.session_id
        }
    elif user_message.lower() in ['browse programs', '🎓 browse programs']:
        response = {
            'response': "What type of program are you interested in?",
            'suggestions': [
                '🎓 Undergraduate Programs', '🎓 Graduate Programs', '🎓 PhD Programs',
                '💼 MBA Programs', '🔬 Research Programs', 'Back to main menu'
            ],
            'type': 'program_selection',
            'session_id': chat_session.session_id
        }
    elif user_message.lower() in ['talk to advisor', '🗣️ talk to advisor', 'human agent'] or \
         any(phrase in user_message.lower() for phrase in ['talk to advisor', 'human advisor', 'speak to human', 'talk to human', 'human agent', 'real person', 'live agent']):
        response = escalate_to_human(chat_session, user_message)
    else:
        # Try RAG system first with company-specific priority
        rag_result, rag_score = get_rag_response(user_message, company_id)

        if rag_result:  # Remove score threshold check since we handle it in RAG system now
            # Personalize response based on company context
            personalized_answer = rag_result['answer']

            # Add company context if it's a company-specific FAQ
            if rag_result.get('source_type') == 'company_faq':
                company_name = rag_result.get('document', '').replace(' Company FAQ', '')
                if company_name and company_name != company_id:
                    personalized_answer = f"As {company_name}'s assistant, {personalized_answer}"

            response = {
                'response': personalized_answer,
                'suggestions': ['🌍 Choose Country', '🎓 Browse Programs', '🗣️ Talk to Advisor'],
                'type': 'rag_response',
                'session_id': chat_session.session_id,
                'source': rag_result.get('source_type', 'general_faq'),
                'company_specific': rag_result.get('source_type') == 'company_faq'
            }
        # Special handling for "who are you" type questions with company fallback
        elif any(phrase in user_message.lower() for phrase in ['who are you', 'what are you', 'who r u', 'introduce yourself']):
            # Get company name from database or use company_id
            try:
                from authentication.models import User
                company_user = User.objects.filter(company_id=company_id, role=User.Role.ADMIN).first()
                company_name = company_user.name if company_user else company_id
            except:
                company_name = company_id

            response = {
                'response': f"I am {company_name}'s AI assistant, here to help you with your study abroad journey. How can I assist you today?",
                'suggestions': ['🌍 Choose Country', '🎓 Browse Programs', '🗣️ Talk to Advisor'],
                'type': 'company_fallback_response',
                'session_id': chat_session.session_id,
                'source': 'company_fallback',
                'company_specific': True
            }
        elif is_greeting_query(user_message):
            response = {
                'response': "Hello! 👋 Welcome to EduConsult. I'm here to help you with your study abroad journey. How can I assist you today?",
                'suggestions': [
                    '🌍 Choose Country', '🎓 Browse Programs', 
                    '📚 Requirements', '💰 Scholarships', '🗣️ Talk to Advisor'
                ],
                'type': 'greeting_response',
                'session_id': chat_session.session_id
            }
        else:
            response = {
                'response': "I'd be happy to help you with your study abroad plans. Could you please tell me which country you're interested in or what specific information you need?",
                'suggestions': [
                    '🌍 Choose Country', '🎓 Browse Programs',
                    '📚 Requirements', '🗣️ Talk to Advisor'
                ],
                'type': 'clarification_needed',
                'session_id': chat_session.session_id
            }
    
    # Log bot response
    ChatMessage.objects.create(
        session=chat_session,
        message_type='bot',
        content=response['response'],
        metadata={'source': 'bot', 'type': response['type']}
    )
    
    # Add user message and attachments to response
    response['user_message'] = ChatMessageSerializer(user_message_obj).data
    if attachment_ids:
        response['attachments'] = [
            UploadedFileSerializer(file).data 
            for file in user_message_obj.attachments.all()
        ]
    
    return Response(response)

def handle_profile_collection(user_message, chat_session):
    """Handle user profile collection flow using session state"""
    # Check if profile already exists
    if chat_session.user_profile:
        return None
    
    # Get current collection state from session
    collecting_state = chat_session.profile_collection_state
    temp_data = chat_session.temp_profile_data or {}
    
    if collecting_state == 'name':
        # Validate name
        is_valid, error_msg = validate_name(user_message)
        if not is_valid:
            return {
                'response': f"I'm sorry, but {error_msg}. Please enter your full name:",
                'suggestions': [],
                'type': 'profile_collection',
                'collecting': 'name'
            }
        
        # Store name and move to next state
        temp_data['name'] = user_message.strip()
        chat_session.temp_profile_data = temp_data
        chat_session.profile_collection_state = 'country_code'
        chat_session.save()
        
        # Ask for country code
        country_suggestions = [f"{cc['code']} {cc['flag']} {cc['country']}" for cc in COUNTRY_CODES[:8]]
        
        return {
            'response': f"Nice to meet you, {user_message.strip()}! 👋<br><br>Now I need your phone number. Please first select your country code:",
            'suggestions': country_suggestions + ['Show more countries'],
            'type': 'profile_collection',
            'collecting': 'country_code',
            'temp_data': temp_data
        }
    
    elif collecting_state == 'country_code':
        # Extract country code from selection
        country_code = '+977'  # Default
        for cc in COUNTRY_CODES:
            if cc['code'] in user_message or cc['country'].lower() in user_message.lower():
                country_code = cc['code']
                break
        
        temp_data['country_code'] = country_code
        chat_session.temp_profile_data = temp_data
        chat_session.profile_collection_state = 'phone'
        chat_session.save()
        
        return {
            'response': f"Great! Now please enter your phone number (without the country code {country_code}):",
            'suggestions': ['Example: 9841234567'],
            'type': 'profile_collection',
            'collecting': 'phone',
            'temp_data': temp_data
        }
    
    elif collecting_state == 'phone':
        # Validate phone number
        country_code = temp_data.get('country_code', '+977')
        is_valid, error_msg = validate_phone_number(user_message, country_code)
        
        if not is_valid:
            return {
                'response': f"I'm sorry, but {error_msg}. Please enter a valid phone number:",
                'suggestions': ['Example: 9841234567'],
                'type': 'profile_collection',
                'collecting': 'phone',
                'temp_data': temp_data
            }
        
        temp_data['phone'] = f"{country_code}-{user_message.strip()}"
        chat_session.temp_profile_data = temp_data
        chat_session.profile_collection_state = 'email'
        chat_session.save()
        
        return {
            'response': "Perfect! Now, would you like to provide your email address? (You can skip this by typing 'skip')",
            'suggestions': ['Example: your.email@example.com', 'Skip'],
            'type': 'profile_collection',
            'collecting': 'email',
            'temp_data': temp_data
        }
    
    elif collecting_state == 'email':
        # Handle optional email - user can skip
        email = user_message.strip().lower()
        
        if email in ['skip', 'no', 'no thanks', 'pass']:
            # Skip email, move to address
            temp_data['email'] = None
            chat_session.temp_profile_data = temp_data
            chat_session.profile_collection_state = 'address'
            chat_session.save()
            
            return {
                'response': "No problem! Finally, please provide your address:",
                'suggestions': ['Example: City, Country'],
                'type': 'profile_collection',
                'collecting': 'address',
                'temp_data': temp_data
            }
        else:
            # Validate email if provided
            if '@' not in email or '.' not in email:
                return {
                    'response': "Please enter a valid email address or type 'skip' to continue without email:",
                    'suggestions': ['Example: your.email@example.com', 'Skip'],
                    'type': 'profile_collection',
                    'collecting': 'email',
                    'temp_data': temp_data
                }
            
            temp_data['email'] = user_message.strip()
            chat_session.temp_profile_data = temp_data
            chat_session.profile_collection_state = 'address'
            chat_session.save()
            
            return {
                'response': "Great! Finally, please provide your address:",
                'suggestions': ['Example: City, Country'],
                'type': 'profile_collection',
                'collecting': 'address',
                'temp_data': temp_data
            }
    
    elif collecting_state == 'address':
        # Create user profile
        temp_data['address'] = user_message.strip()
        
        # Create UserProfile with all collected data including company_id
        user_profile = UserProfile.objects.create(
            session_id=chat_session.session_id,
            company_id=chat_session.company_id,  # Use company_id from session
            persistent_user_id=f"user_{uuid.uuid4().hex[:12]}",
            name=temp_data['name'],
            phone=temp_data['phone'],
            email=temp_data['email'],
            address=temp_data['address'],
            country_code=temp_data.get('country_code', '+977')
        )
        
        # Link to session and mark as complete
        chat_session.user_profile = user_profile
        chat_session.profile_completed = True
        chat_session.profile_collection_state = 'complete'
        chat_session.temp_profile_data = {}  # Clear temp data
        chat_session.save()
        
        return {
            'response': f"Thank you, {temp_data['name']}! Your profile is now complete. 🎉<br><br>How can I help you with your education abroad journey?",
            'suggestions': [
                '🌍 Explore Countries',
                '🎓 Browse Programs', 
                '💰 Financial Aid Info',
                '📋 Admission Requirements',
                '🗣️ Talk to Advisor'
            ],
            'type': 'profile_complete'
        }
    
    return None

def process_chat_message(chat_session, user_message):
    """
    Process a chat message and return response
    This function contains the main chatbot logic extracted from chat_message_view
    """
    try:
        # Save user message
        user_message_obj = ChatMessage.objects.create(
            session=chat_session,
            message_type='user',
            content=user_message,
            metadata={'context': 'Initial conversation', 'has_attachments': False}
        )

        # Check if session is escalated - if so, broadcast to agents
        from human_handoff.models import HumanHandoffSession
        try:
            handoff_session = HumanHandoffSession.objects.get(
                chat_session=chat_session,
                resolved_at__isnull=True
            )
            # Session is escalated - broadcast user message to agent
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                room_group_name = f'chat_{chat_session.company_id}_{chat_session.session_id}'
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': user_message_obj.id,
                        'sender_type': 'user',
                        'message': user_message,
                        'timestamp': user_message_obj.timestamp.isoformat(),
                        'sender_name': chat_session.user_profile.name if chat_session.user_profile else 'User'
                    }
                )
            
            # Return escalated response
            return {
                'response': '🔄 Your conversation has been escalated to a human agent. Please wait for assistance.',
                'suggestions': [],
                'type': 'human_handling',
                'escalated': True
            }
        except HumanHandoffSession.DoesNotExist:
            pass  # Not escalated, continue with normal processing

        # Update user activity if profile exists
        profile = chat_session.user_profile
        if profile:
            profile.update_last_used()

        # Check if session needs profile collection
        if not profile:
            return handle_profile_collection(chat_session, user_message)

        # Check for human handoff request
        if any(keyword in user_message.lower() for keyword in ['human', 'agent', 'talk to someone', 'speak to agent']):
            return escalate_to_human(chat_session, user_message)

        # Process regular chat message
        return process_regular_message(chat_session, user_message, profile)

    except Exception as e:
        print(f"DEBUG: Error in process_chat_message: {e}")
        return {
            'response': 'Sorry, I encountered an error. Please try again.',
            'suggestions': [],
            'escalated': False
        }


def process_regular_message(chat_session, user_message, profile):
    """Process regular chat message after profile collection"""
    # Simple response for now - you can enhance this with RAG system
    response_text = "Thank you for your message! How can I help you with your education abroad journey?"

    suggestions = [
        '🌍 Explore Countries',
        '🎓 Browse Programs',
        '💰 Financial Aid Info',
        '📋 Admission Requirements',
        '🗣️ Talk to Advisor'
    ]

    # Log bot response
    ChatMessage.objects.create(
        session=chat_session,
        message_type='bot',
        content=response_text,
        metadata={'source': 'regular_chat'}
    )

    return {
        'response': response_text,
        'suggestions': suggestions,
        'type': 'regular',
        'session_id': chat_session.session_id
    }


def escalate_to_human(chat_session, reason):
    """Escalate session to human agent"""
    from human_handoff.models import HumanHandoffSession

    print(f"DEBUG: Escalating session {chat_session.session_id} for company {chat_session.company_id}")

    # Create handoff session using the correct model that matches the dashboard
    handoff_session, created = HumanHandoffSession.objects.get_or_create(
        chat_session=chat_session,
        defaults={
            'escalation_reason': reason,
            'priority': 'medium'
        }
    )

    if created:
        print(f"DEBUG: Created new handoff session {handoff_session.id}")

        # Send real-time notification to admin dashboard for this company
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                # Notify company's admin dashboard
                async_to_sync(channel_layer.group_send)(
                    f'handoff_{chat_session.company_id}',
                    {
                        'type': 'session_escalated',
                        'data': {
                            'session_id': chat_session.session_id,
                            'company_id': chat_session.company_id,
                            'reason': reason,
                            'priority': 'medium',
                            'timestamp': str(timezone.now())
                        }
                    }
                )
                print(f"DEBUG: Sent escalation notification to company {chat_session.company_id}")
            except Exception as e:
                print(f"DEBUG: Error sending escalation notification: {e}")

    # Update chat session status
    chat_session.status = 'escalated'
    chat_session.save()

    return {
        'response': "🔄 Your conversation has been escalated to a human agent. Please wait for assistance.",
        'suggestions': [],
        'type': 'escalated',
        'escalated': True,
        'session_id': chat_session.session_id
    }


def collect_name(chat_session, user_message):
    """Collect user name"""
    name = user_message.strip()
    if len(name) < 2:
        return {
            'response': "Please provide a valid name with at least 2 characters.",
            'suggestions': ['Example: John Doe'],
            'type': 'profile_collection',
            'collecting': 'name'
        }

    # Update session state
    chat_session.profile_collection_state = 'phone'
    chat_session.save()

    # Store name temporarily
    chat_session.temp_profile_data = {'name': name}
    chat_session.save()

    response = {
        'response': f"Nice to meet you, {name}! 👋<br><br>Now I need your phone number. Please first select your country code:",
        'suggestions': [
            '+977 🇳🇵 Nepal',
            '+91 🇮🇳 India',
            '+1 🇺🇸🇨🇦 United States/Canada',
            '+44 🇬🇧 United Kingdom',
            '+61 🇦🇺 Australia',
            'Show more countries'
        ],
        'type': 'profile_collection',
        'collecting': 'phone',
        'session_id': chat_session.session_id
    }

    # Log bot response
    ChatMessage.objects.create(
        session=chat_session,
        message_type='bot',
        content=response['response'],
        metadata={'source': 'profile_collection', 'type': 'phone_request'}
    )

    return response


def collect_phone(chat_session, user_message):
    """Collect user phone"""
    # Simple phone collection - you can enhance this
    phone = user_message.strip()

    # Get stored name
    temp_data = getattr(chat_session, 'temp_profile_data', {})
    temp_data['phone'] = phone
    chat_session.temp_profile_data = temp_data

    # Update session state
    chat_session.profile_collection_state = 'email'
    chat_session.save()

    response = {
        'response': "Perfect! Now, would you like to provide your email address? (You can skip this by typing 'skip')",
        'suggestions': ['Example: your.email@example.com', 'Skip'],
        'type': 'profile_collection',
        'collecting': 'email',
        'session_id': chat_session.session_id
    }

    # Log bot response
    ChatMessage.objects.create(
        session=chat_session,
        message_type='bot',
        content=response['response'],
        metadata={'source': 'profile_collection', 'type': 'email_request'}
    )

    return response


def collect_email(chat_session, user_message):
    """Collect user email"""
    email = user_message.strip().lower()

    # Get stored data
    temp_data = getattr(chat_session, 'temp_profile_data', {})

    if email != 'skip':
        temp_data['email'] = email

    chat_session.temp_profile_data = temp_data
    chat_session.profile_collection_state = 'address'
    chat_session.save()

    response = {
        'response': "Finally, please provide your address:",
        'suggestions': ['Example: City, Country'],
        'type': 'profile_collection',
        'collecting': 'address',
        'session_id': chat_session.session_id
    }

    # Log bot response
    ChatMessage.objects.create(
        session=chat_session,
        message_type='bot',
        content=response['response'],
        metadata={'source': 'profile_collection', 'type': 'address_request'}
    )

    return response


def collect_address(chat_session, user_message):
    """Collect user address and complete profile"""
    address = user_message.strip()

    # Get stored data
    temp_data = getattr(chat_session, 'temp_profile_data', {})
    temp_data['address'] = address

    # Create user profile
    try:
        profile = UserProfile.objects.create(
            session_id=chat_session.session_id,
            name=temp_data.get('name', 'Unknown'),
            phone=temp_data.get('phone', ''),
            email=temp_data.get('email', ''),
            address=address,
            company_id=chat_session.company_id
        )

        # Update session
        chat_session.profile_collection_state = 'completed'
        chat_session.temp_profile_data = {}
        chat_session.save()

        response = {
            'response': f"Thank you, {profile.name}! Your profile is now complete. 🎉<br><br>How can I help you with your education abroad journey?",
            'suggestions': [
                '🌍 Explore Countries',
                '🎓 Browse Programs',
                '💰 Financial Aid Info',
                '📋 Admission Requirements',
                '🗣️ Talk to Advisor'
            ],
            'type': 'profile_complete',
            'session_id': chat_session.session_id
        }

        # Log bot response
        ChatMessage.objects.create(
            session=chat_session,
            message_type='bot',
            content=response['response'],
            metadata={'source': 'profile_collection', 'type': 'completion'}
        )

        return response

    except Exception as e:
        print(f"DEBUG: Error creating profile: {e}")
        return {
            'response': 'Sorry, there was an error saving your profile. Please try again.',
            'suggestions': [],
            'type': 'error'
        }

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_phone_view(request):
    """
    Validate phone number
    POST /api/chatbot/validate-phone/
    
    Request:
    {
        "phone": "9841234567",
        "country_code": "+977"
    }
    
    Response:
    {
        "valid": true,
        "message": "Valid Nepali mobile number.",
        "provider": "NTC"
    }
    """
    serializer = PhoneValidationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    
    is_valid, message = validate_phone_number(phone, country_code)
    
    # Extract provider info for Nepal
    provider = None
    if country_code == '+977' and is_valid:
        result = validate_nepali_phone(phone)
        provider = result.get('provider')
    
    response_data = {
        'valid': is_valid,
        'message': message,
        'provider': provider
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def session_status_view(request):
    """
    Get session status
    GET /api/chatbot/session-status/?session_id=xxx
    
    Response:
    {
        "session_id": "session_uuid",
        "status": "active",
        "is_escalated": false,
        "user_profile": {...}
    }
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        is_escalated = hasattr(chat_session, 'handoff')
        
        response_data = {
            'session_id': chat_session.session_id,
            'status': chat_session.status,
            'is_escalated': is_escalated,
            'user_profile': UserProfileSerializer(chat_session.user_profile).data if chat_session.user_profile else None
        }
        
        return Response(response_data)
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def country_codes_view(request):
    """
    Get available country codes
    GET /api/chatbot/country-codes/

    Response:
    [
        {"code": "+977", "country": "Nepal", "flag": "🇳🇵"},
        ...
    ]
    """
    return Response(COUNTRY_CODES)


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_history_view(request):
    """
    Get chat history for a session
    GET /api/chatbot/chat-history/?session_id=xxx&company_id=yyy

    Response:
    {
        "session_id": "session_uuid",
        "messages": [
            {
                "id": 1,
                "message_type": "user",
                "content": "Hello",
                "timestamp": "2025-01-01T12:00:00Z",
                "attachments": []
            },
            {
                "id": 2,
                "message_type": "bot",
                "content": "Hi! How can I help you?",
                "timestamp": "2025-01-01T12:00:01Z",
                "attachments": []
            }
        ],
        "session_info": {
            "status": "active",
            "profile_completed": false,
            "is_escalated": false
        }
    }
    """
    session_id = request.GET.get('session_id')
    company_id = request.GET.get('company_id')

    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not company_id:
        return Response({'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get session with company isolation
        chat_session = ChatSession.objects.get(session_id=session_id, company_id=company_id)

        # Get messages for this session
        messages = ChatMessage.objects.filter(session=chat_session).order_by('timestamp')

        # Serialize messages
        message_data = []
        for message in messages:
            # Get attachments
            attachments = []
            for attachment in message.attachments.all():
                attachments.append({
                    'id': attachment.id,
                    'file_url': attachment.get_file_url(),
                    'original_name': attachment.original_name,
                    'file_type': attachment.file_type,
                    'file_size': attachment.file_size
                })

            message_data.append({
                'id': message.id,
                'message_type': message.message_type,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'attachments': attachments,
                'metadata': message.metadata
            })

        # Check if session is escalated
        is_escalated = hasattr(chat_session, 'handoff')

        response_data = {
            'session_id': chat_session.session_id,
            'messages': message_data,
            'session_info': {
                'status': chat_session.status,
                'profile_completed': chat_session.profile_completed,
                'is_escalated': is_escalated,
                'created_at': chat_session.created_at.isoformat(),
                'updated_at': chat_session.updated_at.isoformat()
            }
        }

        return Response(response_data)

    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


# Plan Management Views
@api_view(['GET'])
@permission_classes([AllowAny])
def plans_list_view(request):
    """
    Get all available plans
    GET /api/chatbot/plans/

    Response:
    {
        "plans": [
            {
                "id": 1,
                "name": "Bronze",
                "icon": "🥉",
                "price": "2000.00",
                "subtitle": "Basic Plan",
                "max_agents": "2",
                "gradient": "from-amber-800 via-yellow-600 to-amber-900",
                "text_color": "text-white",
                "border_color": "border-amber-400",
                "button_color": "bg-amber-600 hover:bg-amber-700",
                "shine_color": "rgba(255, 215, 0, 0.8)",
                "features": [
                    {
                        "text": "Basic chatbot (FAQ + RAG-lite)",
                        "included": true
                    }
                ]
            }
        ]
    }
    """
    from .models import Plan, PlanFeature

    try:
        plans = Plan.objects.filter(is_active=True).prefetch_related('features')

        plans_data = []
        for plan in plans:
            features_data = []
            for feature in plan.features.all():
                features_data.append({
                    'text': feature.text,
                    'included': feature.included
                })

            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'icon': plan.icon,
                'price': str(plan.price) if plan.price else None,
                'subtitle': plan.subtitle,
                'max_agents': plan.max_agents,
                'gradient': plan.gradient,
                'text_color': plan.text_color,
                'border_color': plan.border_color,
                'button_color': plan.button_color,
                'shine_color': plan.shine_color,
                'features': features_data
            })

        return Response(plans_data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsSuperAdmin])
def plan_update_view(request, plan_id):
    """
    Update a plan (SuperAdmin only)
    PUT /api/chatbot/plans/{plan_id}/

    Request:
    {
        "name": "Bronze",
        "subtitle": "Small Companies",
        "price": 2500.00,
        "max_agents": "3"
    }
    """
    from .models import Plan

    try:
        plan = Plan.objects.get(id=plan_id, is_active=True)

        # Update allowed fields
        if 'name' in request.data:
            plan.name = request.data['name']
        if 'subtitle' in request.data:
            plan.subtitle = request.data['subtitle']
        if 'price' in request.data:
            plan.price = request.data['price']
        if 'max_agents' in request.data:
            plan.max_agents = request.data['max_agents']

        plan.save()

        return Response({
            'id': plan.id,
            'name': plan.name,
            'subtitle': plan.subtitle,
            'price': str(plan.price) if plan.price else None,
            'max_agents': plan.max_agents,
            'message': 'Plan updated successfully'
        })

    except Plan.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def superadmin_plans_list_view(request):
    """
    SuperAdmin Plans List
    GET /api/superadmin/plans

    Returns all plans with full details for SuperAdmin editing
    """
    from .models import Plan

    try:
        plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'name')

        plans_data = []
        for plan in plans:
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'for_whom': plan.subtitle,  # subtitle is "for_whom"
                'price': float(plan.price) if plan.price else None,
                'max_agents': plan.max_agents,
                'features_line': plan.features_line,
                'css_meta': {
                    'gradient': plan.gradient,
                    'text_color': plan.text_color,
                    'border_color': plan.border_color,
                    'button_color': plan.button_color,
                    'shine_color': plan.shine_color
                },
                'icon': plan.icon,
                'sort_order': plan.sort_order
            })

        return Response(plans_data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsSuperAdmin])
def superadmin_plan_update_view(request, plan_id):
    """
    SuperAdmin Plan Update
    PUT /api/superadmin/plans/:id

    Updates a plan with new values
    """
    from .models import Plan

    try:
        plan = Plan.objects.get(id=plan_id, is_active=True)

        # Update basic fields
        if 'name' in request.data:
            plan.name = request.data['name']
        if 'for_whom' in request.data:
            plan.subtitle = request.data['for_whom']  # subtitle is "for_whom"
        if 'price' in request.data:
            plan.price = request.data['price']
        if 'max_agents' in request.data:
            plan.max_agents = str(request.data['max_agents'])
        if 'features_line' in request.data:
            plan.features_line = request.data['features_line']

        # Update CSS metadata
        if 'css_meta' in request.data:
            css_meta = request.data['css_meta']
            if 'gradient' in css_meta:
                plan.gradient = css_meta['gradient']
            if 'text_color' in css_meta:
                plan.text_color = css_meta['text_color']
            if 'border_color' in css_meta:
                plan.border_color = css_meta['border_color']
            if 'button_color' in css_meta:
                plan.button_color = css_meta['button_color']
            if 'shine_color' in css_meta:
                plan.shine_color = css_meta['shine_color']

        plan.save()

        return Response({
            'id': plan.id,
            'name': plan.name,
            'for_whom': plan.subtitle,
            'price': float(plan.price) if plan.price else None,
            'max_agents': plan.max_agents,
            'features_line': plan.features_line,
            'css_meta': {
                'gradient': plan.gradient,
                'text_color': plan.text_color,
                'border_color': plan.border_color,
                'button_color': plan.button_color,
                'shine_color': plan.shine_color
            },
            'message': 'Plan updated successfully'
        })

    except Plan.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_plans_view(request):
    """
    Get all plans for Admin users (read-only for upgrade modal)
    GET /api/chatbot/admin/plans/
    """
    from .models import Plan

    try:
        plans = Plan.objects.all().order_by('sort_order')
        plans_data = []

        for plan in plans:
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'for_whom': plan.subtitle,  # subtitle is the "for_whom" field
                'price': float(plan.price) if plan.price else None,
                'max_agents': plan.max_agents,
                'features_line': plan.features_line,
                'css_meta': {
                    'gradient': plan.gradient,
                    'text_color': plan.text_color,
                    'border_color': plan.border_color,
                    'button_color': plan.button_color,
                    'shine_color': plan.shine_color,
                },
                'icon': plan.icon,
                'sort_order': plan.sort_order,
            })

        return Response(plans_data)

    except Exception as e:
        return Response({
            'error': f'Failed to fetch plans: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_subscription_view(request, company_id):
    """
    Company Subscription Details
    GET /api/company/:company_id/subscription

    Returns current subscription for company
    """
    from .models import CompanyPlan

    try:
        # Check if user has access to this company
        if request.user.role != 'SUPERADMIN' and request.user.company_id != company_id:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            company_plan = CompanyPlan.objects.get(company_id=company_id, is_active=True)
            plan = company_plan.current_plan

            return Response({
                'plan_id': plan.id,
                'plan_name': plan.name,
                'price': float(plan.price) if plan.price else None,
                'max_agents': plan.max_agents,
                'status': 'active' if company_plan.is_active else 'inactive',
                'for_whom': plan.subtitle,
                'features_line': plan.features_line
            })

        except CompanyPlan.DoesNotExist:
            return Response({'error': 'No active subscription found'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_upgrade_request_view(request, company_id):
    """
    Company Upgrade Request
    POST /api/company/:company_id/upgrade-request

    Creates an upgrade request for the company
    """
    from .models import Plan, CompanyPlan, PlanUpgradeRequest

    try:
        # Check if user has access to this company
        if request.user.role != 'SUPERADMIN' and request.user.company_id != company_id:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        requested_plan_id = request.data.get('requested_plan_id')
        if not requested_plan_id:
            return Response({'error': 'requested_plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get requested plan
        try:
            requested_plan = Plan.objects.get(id=requested_plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({'error': 'Invalid plan ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Get current plan
        try:
            company_plan = CompanyPlan.objects.get(company_id=company_id, is_active=True)
            current_plan = company_plan.current_plan
        except CompanyPlan.DoesNotExist:
            return Response({'error': 'No active subscription found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if there's already a pending request
        existing_request = PlanUpgradeRequest.objects.filter(
            company_id=company_id,
            status='pending'
        ).first()

        if existing_request:
            return Response({'error': 'There is already a pending upgrade request'}, status=status.HTTP_400_BAD_REQUEST)

        # Create upgrade request
        upgrade_request = PlanUpgradeRequest.objects.create(
            company_id=company_id,
            current_plan=current_plan,
            requested_plan=requested_plan,
            reason=request.data.get('reason', ''),
            requested_by=request.user.username
        )

        return Response({
            'success': True,
            'request_id': upgrade_request.id,
            'message': f'Upgrade request from {current_plan.name} to {requested_plan.name} submitted successfully'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def superadmin_upgrade_requests_view(request):
    """
    SuperAdmin Upgrade Requests List
    GET /api/superadmin/upgrade-requests

    Returns all upgrade requests for SuperAdmin review
    """
    from .models import PlanUpgradeRequest
    from authentication.models import User

    try:
        requests = PlanUpgradeRequest.objects.all().order_by('-request_date')

        requests_data = []
        for req in requests:
            # Get company name from user
            try:
                user = User.objects.get(company_id=req.company_id)
                company_name = user.email  # Use email as company name for now
            except User.DoesNotExist:
                company_name = req.company_id

            requests_data.append({
                'id': req.id,
                'company_name': company_name,
                'company_id': req.company_id,
                'current_plan': req.current_plan.name,
                'requested_plan': req.requested_plan.name,
                'status': req.status,
                'requested_date': req.request_date.isoformat(),
                'reason': req.reason,
                'requested_by': req.requested_by
            })

        return Response(requests_data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def superadmin_approve_upgrade_request_view(request, request_id):
    """
    SuperAdmin Approve Upgrade Request
    POST /api/superadmin/upgrade-requests/:request_id/approve

    Approves an upgrade request and updates company subscription
    """
    from .models import PlanUpgradeRequest, CompanyPlan

    try:
        # Get the upgrade request
        try:
            upgrade_request = PlanUpgradeRequest.objects.get(id=request_id)
        except PlanUpgradeRequest.DoesNotExist:
            return Response({'error': 'Upgrade request not found'}, status=status.HTTP_404_NOT_FOUND)

        if upgrade_request.status != 'pending':
            return Response({'error': 'Request has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

        # Update company plan
        try:
            company_plan = CompanyPlan.objects.get(company_id=upgrade_request.company_id, is_active=True)
            company_plan.current_plan = upgrade_request.requested_plan
            company_plan.save()
        except CompanyPlan.DoesNotExist:
            # Create new company plan if doesn't exist
            company_plan = CompanyPlan.objects.create(
                company_id=upgrade_request.company_id,
                current_plan=upgrade_request.requested_plan,
                is_active=True
            )

        # Update request status
        upgrade_request.status = 'approved'
        upgrade_request.approved_by = request.user.username
        upgrade_request.response_date = timezone.now()
        upgrade_request.admin_notes = request.data.get('notes', 'Approved by SuperAdmin')
        upgrade_request.save()

        return Response({
            'success': True,
            'message': f'Upgrade request approved. {upgrade_request.company_id} upgraded to {upgrade_request.requested_plan.name}'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def superadmin_company_subscriptions_view(request):
    """
    SuperAdmin Company Subscriptions List
    GET /api/chatbot/superadmin/company-subscriptions/

    Returns all company subscriptions with current plan data from chatbot app
    """
    from .models import CompanyPlan, Plan
    from authentication.models import User

    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        search = request.GET.get('search', '')
        plan_filter = request.GET.get('plan', '')
        status_filter = request.GET.get('status', '')

        # Get all company plans
        company_plans = CompanyPlan.objects.filter(is_active=True)

        # Apply filters
        if search:
            # Get company IDs that match the search
            matching_users = User.objects.filter(
                Q(email__icontains=search) | Q(company_id__icontains=search)
            ).values_list('company_id', flat=True)
            company_plans = company_plans.filter(company_id__in=matching_users)

        if plan_filter:
            company_plans = company_plans.filter(current_plan__name=plan_filter)

        if status_filter:
            if status_filter == 'active':
                company_plans = company_plans.filter(is_active=True)
            elif status_filter == 'inactive':
                company_plans = company_plans.filter(is_active=False)

        # Order by creation date
        company_plans = company_plans.order_by('-created_at')

        # Pagination
        total = company_plans.count()
        start = (page - 1) * page_size
        end = start + page_size
        company_plans = company_plans[start:end]

        # Build response data
        results = []
        for cp in company_plans:
            # Get company name from user
            try:
                user = User.objects.get(company_id=cp.company_id)
                company_name = user.email.split('@')[0].title()  # Use email prefix as company name
            except User.DoesNotExist:
                company_name = cp.company_id

            # Get plan history (simplified)
            plan_history = []
            # You can add plan history logic here if needed

            # Handle custom plan values
            if cp.current_plan.name == 'Custom' and hasattr(cp, 'custom_price') and hasattr(cp, 'custom_max_agents'):
                price = float(cp.custom_price) if cp.custom_price else 0
                max_agents = str(cp.custom_max_agents) if cp.custom_max_agents else cp.current_plan.max_agents
            else:
                price = float(cp.current_plan.price) if cp.current_plan.price else 0
                max_agents = cp.current_plan.max_agents

            results.append({
                'id': cp.id,
                'company_name': company_name,
                'company_id': cp.company_id,
                'plan_name': cp.current_plan.name,
                'price': price,
                'max_agents': max_agents,
                'created_at': cp.created_at.isoformat(),
                'expiry_date': cp.plan_end_date.isoformat() if cp.plan_end_date else None,
                'status': 'active' if cp.is_active else 'inactive',
                'plan_history': plan_history
            })

        return Response({
            'count': total,
            'results': results
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def superadmin_change_company_plan_view(request, company_id):
    """
    SuperAdmin Change Company Plan
    POST /api/chatbot/superadmin/company/:company_id/change-plan/

    Allows SuperAdmin to manually change a company's plan
    """
    from .models import Plan as ChatbotPlan
    from authentication.models import User, Plan as AuthPlan, UserPlanAssignment

    try:
        plan_id = request.data.get('plan_id')
        custom_max_agents = request.data.get('custom_max_agents')
        custom_price = request.data.get('custom_price')
        reason = request.data.get('reason', 'Manual plan change by SuperAdmin')

        if not plan_id:
            return Response({'error': 'plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the new chatbot plan
        try:
            new_chatbot_plan = ChatbotPlan.objects.get(id=plan_id, is_active=True)
        except ChatbotPlan.DoesNotExist:
            return Response({'error': 'Invalid plan ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the company user
        try:
            user = User.objects.get(company_id=company_id, role=User.Role.ADMIN)
        except User.DoesNotExist:
            return Response({'error': 'Company admin not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get current active assignment
        current_assignment = UserPlanAssignment.objects.filter(
            user=user,
            status='active'
        ).first()

        if not current_assignment:
            return Response({'error': 'No active plan assignment found'}, status=status.HTTP_404_NOT_FOUND)

        old_plan_name = current_assignment.plan.plan_name

        # Map plan name to authentication model format
        plan_name_mapping = {
            'Bronze': 'bronze',
            'Silver': 'silver',
            'Gold': 'gold',
            'Platinum': 'platinum',
            'Diamond': 'diamond',
            'Custom': 'custom'
        }

        plan_name_db = plan_name_mapping.get(new_chatbot_plan.name)
        if not plan_name_db:
            return Response({'error': f'Unknown plan name: {new_chatbot_plan.name}'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle custom plan values
        max_agents = int(new_chatbot_plan.max_agents) if new_chatbot_plan.max_agents.isdigit() else 2
        price = new_chatbot_plan.price if new_chatbot_plan.price else 0

        if new_chatbot_plan.name == 'Custom':
            if not custom_max_agents or not custom_price:
                return Response({
                    'error': 'custom_max_agents and custom_price are required for Custom plan'
                }, status=status.HTTP_400_BAD_REQUEST)
            max_agents = custom_max_agents
            price = custom_price

        # Create or update the authentication plan with correct values
        auth_plan, created = AuthPlan.objects.get_or_create(
            plan_name=plan_name_db,
            company_name=company_id,
            defaults={
                'max_agents': max_agents,
                'price': price,
                'is_active': True
            }
        )

        # If plan already existed, update it with correct values from chatbot plan
        if not created:
            auth_plan.max_agents = max_agents
            auth_plan.price = price
            auth_plan.is_active = True
            auth_plan.save()

        # Update existing assignment to 'upgraded' status
        current_assignment.status = 'upgraded'
        current_assignment.notes = f'Plan changed by SuperAdmin: {reason}'
        current_assignment.save()

        # Create new plan assignment
        new_assignment = UserPlanAssignment.objects.create(
            user=user,
            plan=auth_plan,
            status='active',
            notes=f'Plan changed by SuperAdmin from {old_plan_name} to {new_chatbot_plan.name}: {reason}'
        )

        # Update CompanyPlan to sync with the new assignment
        from .models import CompanyPlan
        try:
            company_plan = CompanyPlan.objects.get(company_id=company_id)
            company_plan.current_plan = new_chatbot_plan
            company_plan.is_active = True
            company_plan.save()
            print(f"Updated CompanyPlan for {company_id} to {new_chatbot_plan.name}")
        except CompanyPlan.DoesNotExist:
            # Create new CompanyPlan if it doesn't exist
            CompanyPlan.objects.create(
                company_id=company_id,
                current_plan=new_chatbot_plan,
                is_active=True
            )
            print(f"Created new CompanyPlan for {company_id} with {new_chatbot_plan.name}")

        return Response({
            'success': True,
            'message': f'Company {company_id} plan changed from {old_plan_name} to {new_chatbot_plan.name}',
            'old_plan': old_plan_name,
            'new_plan': new_chatbot_plan.name,
            'max_agents': max_agents,
            'price': str(price)
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def superadmin_faq_list_view(request):
    """
    SuperAdmin FAQ Management
    GET /api/chatbot/superadmin/faqs/ - List all FAQs
    POST /api/chatbot/superadmin/faqs/ - Add new FAQ
    """
    import json
    import uuid
    import os
    from django.conf import settings

    try:
        # Use the correct path within Full-Chatbot-Integration
        faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', 'education_faq.json')

        if request.method == 'GET':
            # Read and return all FAQs
            if not os.path.exists(faq_file_path):
                return Response({'count': 0, 'results': []})

            with open(faq_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Flatten all FAQs into a single list
            all_faqs = []
            for category_key, category_data in data.items():
                if isinstance(category_data, dict):
                    for subcategory_key, subcategory_faqs in category_data.items():
                        if isinstance(subcategory_faqs, list):
                            for faq in subcategory_faqs:
                                faq_item = {
                                    'id': faq.get('chunk_id', str(uuid.uuid4())),
                                    'question': faq.get('question', ''),
                                    'answer': faq.get('answer', ''),
                                    'category': f"{category_key}.{subcategory_key}",
                                    'section': faq.get('section', ''),
                                    'document': faq.get('document', ''),
                                    'chunk_id': faq.get('chunk_id', ''),
                                    'page': faq.get('page', 0)
                                }
                                all_faqs.append(faq_item)

            return Response({
                'count': len(all_faqs),
                'results': all_faqs
            })

        elif request.method == 'POST':
            # Add new FAQ
            question = request.data.get('question')
            answer = request.data.get('answer')
            category = request.data.get('category', 'general_queries.custom_entries')
            section = request.data.get('section', 'Custom FAQ')

            if not question or not answer:
                return Response({'error': 'Question and answer are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Parse category
            if '.' in category:
                category_key, subcategory_key = category.split('.', 1)
            else:
                category_key = 'general_queries'
                subcategory_key = 'custom_entries'

            # Create new FAQ entry
            new_faq = {
                'question': question,
                'answer': answer,
                'section': section,
                'page': 0,
                'document': 'Admin Added FAQ',
                'chunk_id': str(uuid.uuid4())
            }

            # Load existing data or create new structure
            if os.path.exists(faq_file_path):
                with open(faq_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}

            # Ensure category structure exists
            if category_key not in data:
                data[category_key] = {}
            if subcategory_key not in data[category_key]:
                data[category_key][subcategory_key] = []

            # Add new FAQ
            data[category_key][subcategory_key].append(new_faq)

            # Save updated JSON
            os.makedirs(os.path.dirname(faq_file_path), exist_ok=True)
            with open(faq_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Automatically refresh vector database
            try:
                _auto_refresh_vectors()
            except Exception as vector_error:
                print(f"Warning: Vector database refresh failed: {vector_error}")

            return Response({
                'success': True,
                'message': 'FAQ added successfully',
                'faq': new_faq
            })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsSuperAdmin])
def superadmin_faq_detail_view(request, faq_id):
    """
    SuperAdmin FAQ Detail Management
    PUT /api/chatbot/superadmin/faqs/:id/ - Update FAQ
    DELETE /api/chatbot/superadmin/faqs/:id/ - Delete FAQ
    """
    import json
    import os
    from django.conf import settings

    try:
        # Use the correct path within Full-Chatbot-Integration
        faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', 'education_faq.json')

        if not os.path.exists(faq_file_path):
            return Response({'error': 'FAQ file not found'}, status=status.HTTP_404_NOT_FOUND)

        with open(faq_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Find the FAQ by chunk_id
        found_faq = None
        found_location = None

        for category_key, category_data in data.items():
            if isinstance(category_data, dict):
                for subcategory_key, subcategory_faqs in category_data.items():
                    if isinstance(subcategory_faqs, list):
                        for i, faq in enumerate(subcategory_faqs):
                            if faq.get('chunk_id') == faq_id:
                                found_faq = faq
                                found_location = (category_key, subcategory_key, i)
                                break
                    if found_faq:
                        break
            if found_faq:
                break

        if not found_faq:
            return Response({'error': 'FAQ not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'PUT':
            # Update FAQ
            question = request.data.get('question')
            answer = request.data.get('answer')
            category = request.data.get('category')
            section = request.data.get('section', 'Custom FAQ')

            if not question or not answer:
                return Response({'error': 'Question and answer are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Update the FAQ
            category_key, subcategory_key, index = found_location
            data[category_key][subcategory_key][index].update({
                'question': question,
                'answer': answer,
                'section': section
            })

            # If category changed, move the FAQ
            if category and category != f"{category_key}.{subcategory_key}":
                if '.' in category:
                    new_category_key, new_subcategory_key = category.split('.', 1)
                else:
                    new_category_key = 'general_queries'
                    new_subcategory_key = 'custom_entries'

                # Remove from old location
                updated_faq = data[category_key][subcategory_key].pop(index)

                # Add to new location
                if new_category_key not in data:
                    data[new_category_key] = {}
                if new_subcategory_key not in data[new_category_key]:
                    data[new_category_key][new_subcategory_key] = []

                data[new_category_key][new_subcategory_key].append(updated_faq)

            # Save updated JSON
            with open(faq_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Automatically refresh vector database
            try:
                _auto_refresh_vectors()
            except Exception as vector_error:
                print(f"Warning: Vector database refresh failed: {vector_error}")

            return Response({
                'success': True,
                'message': 'FAQ updated successfully'
            })

        elif request.method == 'DELETE':
            # Delete FAQ
            category_key, subcategory_key, index = found_location
            deleted_faq = data[category_key][subcategory_key].pop(index)

            # Save updated JSON
            with open(faq_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Automatically refresh vector database
            try:
                _auto_refresh_vectors()
            except Exception as vector_error:
                print(f"Warning: Vector database refresh failed: {vector_error}")

            return Response({
                'success': True,
                'message': 'FAQ deleted successfully'
            })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def superadmin_refresh_vectors_view(request):
    """
    SuperAdmin Refresh Vector Database - PRODUCTION SAFE
    POST /api/chatbot/superadmin/faqs/refresh-vectors/

    Uses the centralized, thread-safe vector refresh manager
    """
    try:
        from .utils.vector_refresh_manager import vector_refresh_manager

        # Check if refresh is already in progress
        if vector_refresh_manager.is_refresh_in_progress():
            return Response({
                'success': False,
                'message': 'Vector refresh already in progress',
                'status': 'in_progress'
            }, status=status.HTTP_409_CONFLICT)

        # Start the refresh
        result = vector_refresh_manager.refresh_general_vectors()

        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'status': result['status'],
                'timestamp': result.get('timestamp'),
                'details': 'General FAQ vectors have been safely refreshed using production-safe methods'
            })
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'status': result['status'],
                'details': 'Vector refresh failed - check server logs for details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({
            'error': f'Failed to refresh vectors: {str(e)}',
            'details': 'An unexpected error occurred during vector database refresh'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def superadmin_decline_upgrade_request_view(request, request_id):
    """
    SuperAdmin Decline Upgrade Request
    POST /api/superadmin/upgrade-requests/:request_id/decline

    Declines an upgrade request
    """
    from .models import PlanUpgradeRequest

    try:
        # Get the upgrade request
        try:
            upgrade_request = PlanUpgradeRequest.objects.get(id=request_id)
        except PlanUpgradeRequest.DoesNotExist:
            return Response({'error': 'Upgrade request not found'}, status=status.HTTP_404_NOT_FOUND)

        if upgrade_request.status != 'pending':
            return Response({'error': 'Request has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

        # Update request status
        upgrade_request.status = 'rejected'
        upgrade_request.approved_by = request.user.username
        upgrade_request.response_date = timezone.now()
        upgrade_request.admin_notes = request.data.get('notes', 'Declined by SuperAdmin')
        upgrade_request.save()

        return Response({
            'success': True,
            'message': f'Upgrade request declined for {upgrade_request.company_id}'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_plan_view(request):
    """
    Get current plan for a company
    GET /api/chatbot/company-plan/?company_id=xxx

    Response:
    {
        "company_id": "ZIL001",
        "current_plan": "Bronze",
        "requested_plan": "Gold",
        "has_pending_request": true
    }
    """
    from .models import CompanyPlan, PlanUpgradeRequest

    company_id = request.GET.get('company_id')
    if not company_id:
        return Response({'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get company plan from authentication system (the real system)
        try:
            from authentication.models import User, UserPlanAssignment
            user = User.objects.get(company_id=company_id)
            active_assignment = UserPlanAssignment.objects.filter(
                user=user, status='active'
            ).select_related('plan').first()

            if active_assignment:
                current_plan = active_assignment.plan.plan_name
            else:
                current_plan = "Bronze"  # Default
        except:
            # Fallback to chatbot system if authentication system fails
            try:
                company_plan = CompanyPlan.objects.select_related('current_plan', 'requested_plan').get(
                    company_id=company_id, is_active=True
                )
                current_plan = company_plan.current_plan.name
            except CompanyPlan.DoesNotExist:
                current_plan = "Bronze"  # Default

        requested_plan = None

        # Check for pending upgrade requests in chatbot system
        pending_request = PlanUpgradeRequest.objects.filter(
            company_id=company_id,
            status='pending'
        ).first()

        has_pending_request = pending_request is not None
        if has_pending_request:
            requested_plan = pending_request.requested_plan.name
        else:
            requested_plan = None

        return Response({
            'company_id': company_id,
            'current_plan': current_plan,
            'requested_plan': requested_plan,
            'has_pending_request': has_pending_request
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_plan_upgrade_view(request):
    """
    Request plan upgrade (Admin only)
    POST /api/chatbot/request-plan-upgrade/

    Request:
    {
        "requested_plan": "Gold",
        "reason": "Need more features"
    }

    Response:
    {
        "success": true,
        "message": "Plan upgrade request submitted successfully",
        "request_id": 123
    }
    """
    from .models import Plan, CompanyPlan, PlanUpgradeRequest

    # Get company_id from authenticated user
    company_id = request.user.company_id
    requested_plan_name = request.data.get('requested_plan')
    reason = request.data.get('reason', '')

    if not requested_plan_name:
        return Response({
            'error': 'requested_plan is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get requested plan
        try:
            requested_plan = Plan.objects.get(name=requested_plan_name, is_active=True)
        except Plan.DoesNotExist:
            return Response({'error': 'Invalid plan name'}, status=status.HTTP_400_BAD_REQUEST)

        # Get current plan from authentication system
        try:
            from authentication.models import User, UserPlanAssignment
            user = User.objects.get(company_id=company_id)
            active_assignment = UserPlanAssignment.objects.filter(
                user=user, status='active'
            ).select_related('plan').first()

            if active_assignment:
                current_plan_name = active_assignment.plan.plan_name
            else:
                current_plan_name = "bronze"  # Default
        except:
            current_plan_name = "bronze"  # Default

        # Check if already on requested plan
        if current_plan_name.lower() == requested_plan_name.lower():
            return Response({
                'error': 'You are already on this plan'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing pending request
        existing_request = PlanUpgradeRequest.objects.filter(
            company_id=company_id,
            status='pending'
        ).first()

        if existing_request:
            return Response({
                'error': 'You already have a pending upgrade request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create upgrade request in chatbot system
        upgrade_request = PlanUpgradeRequest.objects.create(
            company_id=company_id,
            current_plan=requested_plan,  # Using chatbot plan object
            requested_plan=requested_plan,
            reason=reason,
            requested_by=request.user.username if request.user.is_authenticated else 'Anonymous'
        )

        # Also create request in admin dashboard system so it appears in superadmin dashboard
        try:
            from admin_dashboard.models import PlanUpgradeRequest as AdminPlanUpgradeRequest
            from authentication.models import User

            # Get the company name
            try:
                user = User.objects.get(company_id=company_id)
                company_name = f"{user.first_name} {user.last_name}".strip() or "Unknown Company"
            except User.DoesNotExist:
                company_name = f"Company {company_id}"

            # Create admin dashboard request
            AdminPlanUpgradeRequest.objects.create(
                company_id=company_id,
                company_name=company_name,
                current_plan=current_plan_name,
                requested_plan=requested_plan_name,
                reason=reason,
                requested_by=user if 'user' in locals() else None,
                status='PENDING'
            )
        except Exception as e:
            print(f"Failed to create admin dashboard request: {e}")
            # Don't fail the main request if admin dashboard creation fails

        # Try to update company plan to show pending request (if exists)
        try:
            company_plan = CompanyPlan.objects.get(company_id=company_id, is_active=True)
            company_plan.requested_plan = requested_plan
            company_plan.save()
        except CompanyPlan.DoesNotExist:
            pass  # No company plan in chatbot system, that's ok

        return Response({
            'success': True,
            'message': 'Plan upgrade request submitted successfully',
            'request_id': upgrade_request.id
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_plan_upgrade_view(request):
    """
    Cancel pending plan upgrade request
    POST /api/chatbot/cancel-plan-upgrade/

    Request:
    {
        "company_id": "ZIL001"
    }

    Response:
    {
        "success": true,
        "message": "Plan upgrade request cancelled successfully"
    }
    """
    from .models import CompanyPlan, PlanUpgradeRequest

    company_id = request.data.get('company_id')

    if not company_id:
        return Response({
            'error': 'company_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Check for existing pending request
        existing_request = PlanUpgradeRequest.objects.filter(
            company_id=company_id,
            status='pending'
        ).first()

        if not existing_request:
            return Response({
                'error': 'No pending upgrade request found'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cancel the request
        existing_request.status = 'cancelled'
        existing_request.save()

        # Update company plan to clear pending request
        try:
            company_plan = CompanyPlan.objects.get(company_id=company_id, is_active=True)
            company_plan.requested_plan = None
            company_plan.save()
        except CompanyPlan.DoesNotExist:
            pass  # Company plan doesn't exist, nothing to update

        return Response({
            'success': True,
            'message': 'Plan upgrade request cancelled successfully'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_agent_limit_chatbot_view(request):
    """
    Check agent limits based on chatbot plan system
    GET /api/chatbot/check-agent-limit/?company_id=ZIL001

    Response:
    {
        "can_create": true,
        "current_count": 2,
        "max_allowed": 4,
        "plan_name": "Silver",
        "suggestion": "Upgrade to Gold plan for more agents"
    }
    """
    from .models import CompanyPlan, Plan
    from admin_dashboard.models import Agent

    company_id = request.GET.get('company_id')

    if not company_id:
        return Response({
            'error': 'company_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get company plan from authentication system (the real system)
        try:
            from authentication.models import User, UserPlanAssignment
            user = User.objects.get(company_id=company_id)
            active_assignment = UserPlanAssignment.objects.filter(
                user=user, status='active'
            ).select_related('plan').first()

            if active_assignment:
                current_plan_name = active_assignment.plan.plan_name
                max_agents = active_assignment.plan.max_agents
            else:
                current_plan_name = "Bronze"
                max_agents = 2  # Default Bronze limit
        except:
            # Fallback to chatbot system
            try:
                company_plan = CompanyPlan.objects.select_related('current_plan').get(
                    company_id=company_id, is_active=True
                )
                current_plan_name = company_plan.current_plan.name
                max_agents_str = company_plan.current_plan.max_agents
                if max_agents_str.lower() == 'unlimited':
                    max_agents = 999999  # Large number for unlimited
                else:
                    max_agents = int(max_agents_str)
            except CompanyPlan.DoesNotExist:
                current_plan_name = "Bronze"
                max_agents = 2  # Default Bronze limit

        # Count current agents
        current_agent_count = Agent.objects.filter(company_id=company_id).count()

        can_create = current_agent_count < max_agents

        response_data = {
            'can_create': can_create,
            'current_count': current_agent_count,
            'max_allowed': max_agents,
            'plan_name': current_plan_name,
        }

        if not can_create and max_agents != 999999:
            # Suggest upgrade based on current plan
            plan_hierarchy = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'custom']
            current_index = plan_hierarchy.index(current_plan_name.lower()) if current_plan_name.lower() in plan_hierarchy else -1

            if current_index < len(plan_hierarchy) - 1:
                suggested_plan = plan_hierarchy[current_index + 1].capitalize()
            else:
                suggested_plan = 'Custom'

            response_data.update({
                'suggestion': f'Please upgrade to {suggested_plan} plan to add more agents.',
                'upgrade_needed': True,
                'error': f'Agent limit reached. Your {current_plan_name} plan allows maximum {max_agents} agents.'
            })

        return Response(response_data)

    except Exception as e:
        return Response({
            'error': f'Unable to check agent limits: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_profile_view(request):
    """
    Create user profile
    POST /api/chatbot/create-profile/
    
    Request:
    {
        "name": "John Doe",
        "phone": "+9779841234567",
        "email": "john@example.com",
        "session_id": "session_uuid"
    }
    """
    serializer = ProfileCollectionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
        
        # Create user profile
        persistent_user_id = f"user_{uuid.uuid4().hex[:12]}"
        profile = UserProfile.objects.create(
            session_id=session_id,
            persistent_user_id=persistent_user_id,
            name=serializer.validated_data['name'],
            phone=serializer.validated_data['phone'],
            email=serializer.validated_data.get('email'),
            country_code=serializer.validated_data.get('country_code', '+977')
        )
        
        # Link profile to session
        chat_session.user_profile = profile
        chat_session.save()
        
        return Response({
            'message': 'Profile created successfully',
            'profile': UserProfileSerializer(profile).data,
            'persistent_user_id': profile.persistent_user_id
        })
        
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def load_rag_documents_view(request):
    """
    Load RAG documents from JSON file (Admin only in production)
    GET /api/chatbot/load-rag-documents/
    """
    json_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', 'education_faq.json')
    
    success = rag_system.load_documents_from_json(json_path)
    
    if success:
        count = RAGDocument.objects.filter(is_active=True).count()
        return Response({
            'message': f'Successfully loaded {count} documents',
            'documents_count': count
        })
    else:
        return Response({
            'error': 'Failed to load documents'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@rate_limit(action='upload', limit=10)
def file_upload_view(request):
    """
    Unified file upload endpoint for both chatbot iframe and agent dashboard
    POST /api/chat/upload/

    Request (multipart/form-data):
    {
        "file": <file_object>,
        "company_id": "COMP_123",
        "session_id": "session_uuid",
        "uploader": "user" | "agent",  // Optional, default "user"
        "original_name": "filename.pdf",  // Optional, defaults to file.name
        "mime_type": "application/pdf",  // Optional, defaults to file.content_type
        "size": 12345  // Optional, defaults to file.size
    }

    Response:
    {
        "id": 123,
        "company_id": "COMP_1",
        "session_id": "S_456",
        "uploader": "user",
        "url": "https://cdn.example.com/media/chat/COMP_1/S_456/photo.jpg",
        "name": "photo.jpg",
        "mime_type": "image/jpeg",
        "size": 34567,
        "thumbnail": null,
        "created_at": "2025-09-04T12:34:56Z"
    }
    """
    from .serializers import ChatFileUploadRequestSerializer, ChatFileUploadResponseSerializer
    from .models import ChatFile
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    import mimetypes

    # Validate request data
    serializer = ChatFileUploadRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = serializer.validated_data['file']
    company_id = serializer.validated_data['company_id']
    session_id = serializer.validated_data['session_id']
    uploader = serializer.validated_data.get('uploader', 'user')
    original_name = serializer.validated_data.get('original_name', uploaded_file.name)
    mime_type = serializer.validated_data.get('mime_type', uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0])
    size = serializer.validated_data.get('size', uploaded_file.size)

    try:
        # Validate session exists and belongs to company
        chat_session = ChatSession.objects.get(session_id=session_id, company_id=company_id)

        # Use new storage manager for secure file handling
        from .utils.storage import FileUploadManager
        storage_manager = FileUploadManager()

        # Save file with security checks
        file_info = storage_manager.save_chat_file(uploaded_file, company_id, session_id)

        # Create ChatFile record
        chat_file = ChatFile.objects.create(
            company_id=company_id,
            session_id=session_id,
            uploader=uploader,
            file=file_info['stored_name'],  # Use stored path
            original_name=file_info['original_name'],
            mime_type=file_info['mime_type'],
            size=file_info['file_size'],
            user_profile=chat_session.user_profile,
            chat_session=chat_session
        )

        # Prepare response data with absolute URLs
        file_url = file_info['url']
        if not file_url.startswith('http'):
            # Convert relative URL to absolute URL with consistent localhost
            file_url = request.build_absolute_uri(file_url)
            # Ensure consistent localhost format (not 127.0.0.1)
            file_url = file_url.replace('127.0.0.1', 'localhost')

        response_data = {
            'id': chat_file.id,
            'company_id': chat_file.company_id,
            'session_id': chat_file.session_id,
            'uploader': chat_file.uploader,
            'url': file_url,  # Use absolute URL
            'name': chat_file.original_name,
            'mime_type': chat_file.mime_type,
            'size': chat_file.size,
            'thumbnail': chat_file.thumbnail,
            'created_at': chat_file.created_at.isoformat()
        }

        # Broadcast file_shared event to WebSocket room
        try:
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{company_id}_{session_id}'

            print(f"DEBUG: Broadcasting file_shared to room: {room_group_name}")
            print(f"DEBUG: Channel layer: {channel_layer}")

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'file_shared',
                    'payload': response_data
                }
            )
            print(f"DEBUG: file_shared event broadcasted successfully")
        except Exception as e:
            print(f"ERROR: Failed to broadcast file_shared event: {e}")
            import traceback
            traceback.print_exc()

        return Response(response_data, status=status.HTTP_201_CREATED)

    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Chat session not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'File upload failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def file_list_view(request):
    """
    Get list of files for a session
    GET /api/chat/files/?session_id=...&company_id=...

    Response:
    {
        "files": [
            {
                "id": 123,
                "company_id": "COMP_1",
                "session_id": "S_456",
                "uploader": "user",
                "url": "https://cdn.example.com/media/chat/COMP_1/S_456/photo.jpg",
                "name": "photo.jpg",
                "mime_type": "image/jpeg",
                "size": 34567,
                "thumbnail": null,
                "created_at": "2025-09-04T12:34:56Z"
            }
        ],
        "count": 1
    }
    """
    from .serializers import ChatFileSerializer
    from .models import ChatFile

    session_id = request.GET.get('session_id')
    company_id = request.GET.get('company_id')

    if not session_id or not company_id:
        return Response({
            'error': 'session_id and company_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Validate session exists
        chat_session = ChatSession.objects.get(session_id=session_id, company_id=company_id)

        # Get files for this session
        files = ChatFile.objects.filter(
            company_id=company_id,
            session_id=session_id
        ).order_by('-created_at')

        # Serialize files
        serializer = ChatFileSerializer(files, many=True)

        return Response({
            'files': serializer.data,
            'count': files.count()
        }, status=status.HTTP_200_OK)

    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Chat session not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve files: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def chatbot_configuration_view(request):
    """
    Get chatbot configuration for a company
    GET /api/chatbot/configuration/?company_id=COMP_123

    Response:
    {
        "id": 1,
        "company_id": "COMP_123",
        "primary_color": "#f7941d",
        "secondary_color": "#652d90",
        "position": "bottom-right",
        "iframe_width": 400,
        "iframe_height": 600,
        "welcome_message": "Hello! How can I help you today?",
        "company_name": "Company Name",
        "company_logo_url": null,
        "enable_file_upload": true,
        "enable_voice_messages": false,
        "enable_typing_indicator": true
    }
    """
    company_id = request.GET.get('company_id')

    if not company_id:
        return Response({
            'error': 'company_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get or create configuration for the company
        config = ChatbotConfiguration.get_or_create_for_company(company_id)
        serializer = ChatbotConfigurationSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get configuration: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def update_chatbot_configuration_view(request):
    """
    Update chatbot configuration for a company (Admin only)
    PUT /api/chatbot/configuration/update/

    Request:
    {
        "primary_color": "#ff0000",
        "secondary_color": "#0000ff",
        "position": "bottom-left",
        "iframe_width": 450,
        "iframe_height": 650,
        "welcome_message": "Welcome to our support!",
        "company_name": "My Company",
        "enable_file_upload": true
    }
    """
    from rest_framework.permissions import IsAuthenticated
    from authentication.permissions import IsAdminOrSuperAdmin

    # Get company_id from request data or user or default
    company_id = None

    # Try to get from request data first
    if 'company_id' in request.data:
        company_id = request.data['company_id']
    # Then try from authenticated user
    elif request.user.is_authenticated and hasattr(request.user, 'company_id') and request.user.company_id:
        company_id = request.user.company_id
    # Finally default to TEST001 for testing
    else:
        company_id = 'TEST001'

    print(f"DEBUG: Using company_id: {company_id}")

    if not company_id:
        return Response({
            'error': 'Company ID not found'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get or create configuration for the company
        config = ChatbotConfiguration.get_or_create_for_company(company_id)

        # Update configuration
        serializer = ChatbotConfigurationUpdateSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Get updated configuration data
            response_serializer = ChatbotConfigurationSerializer(config)
            config_data = response_serializer.data

            # Send real-time update via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                try:
                    async_to_sync(channel_layer.group_send)(
                        f'config_{company_id}',
                        {
                            'type': 'config_update',
                            'config': config_data,
                            'company_id': company_id
                        }
                    )
                except Exception as ws_error:
                    print(f"WebSocket update failed: {ws_error}")

            return Response(config_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': f'Failed to update configuration: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_data_view(request):
    """
    Test endpoint to create and verify data
    GET /api/chatbot/test-data/ - Check existing data
    POST /api/chatbot/test-data/ - Create test data
    """
    if request.method == 'POST':
        # Create test data
        from datetime import datetime, timedelta
        import uuid

        # Clear existing data
        UserProfile.objects.filter(company_id="TEST001").delete()

        # Create test users with different activity times
        from datetime import datetime, timedelta
        now = datetime.now()

        users = [
            {"name": "John Doe", "phone": "1234567890", "email": "john@example.com", "address": "123 Main St", "is_favorite": True, "days_ago": 0},
            {"name": "Jane Smith", "phone": "9876543210", "email": "jane@example.com", "address": "456 Oak Ave", "is_favorite": False, "days_ago": 1},
            {"name": "Mike Johnson", "phone": "5555555555", "email": None, "address": "789 Pine Rd", "is_favorite": True, "days_ago": 3},
            {"name": "Sarah Wilson", "phone": "7777777777", "email": "sarah@example.com", "address": None, "is_favorite": False, "days_ago": 10},
            {"name": "Active User", "phone": "1111111111", "email": "active@example.com", "address": "Active St", "is_favorite": False, "days_ago": 0},
        ]

        created_users = []
        for user_data in users:
            # Calculate last_used based on days_ago
            last_used_time = now - timedelta(days=user_data["days_ago"])

            profile = UserProfile.objects.create(
                session_id=str(uuid.uuid4()),
                persistent_user_id=str(uuid.uuid4()),
                name=user_data["name"],
                phone=user_data["phone"],
                email=user_data["email"],
                address=user_data["address"],
                country_code="+977",  # Nepal country code
                company_id="TEST001",
                is_favorite=user_data["is_favorite"],
                last_used=last_used_time
            )
            created_users.append({
                'id': profile.id,
                'name': profile.name,
                'email': profile.email,
                'phone': profile.phone
            })

        return Response({
            'message': f'Created {len(users)} test users',
            'users': created_users
        })

    else:
        # Check existing data
        profiles = UserProfile.objects.filter(company_id="TEST001")
        profile_data = []

        for profile in profiles:
            profile_data.append({
                'id': profile.id,
                'name': profile.name,
                'email': profile.email,
                'phone': profile.phone,
                'address': profile.address,
                'is_favorite': profile.is_favorite,
                'last_used': profile.last_used.isoformat() if profile.last_used else None
            })

        return Response({
            'count': len(profile_data),
            'users': profile_data
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def company_subscription_status_view(request, company_id):
    """
    Check company subscription status for chatbot widget
    GET /api/chatbot/company/{company_id}/status/

    This endpoint is called by chatbot.js to check if the company's subscription is active.

    Response:
    {
        "success": true,
        "is_active": true,
        "company_id": "NHS001",
        "plan_name": "Bronze",
        "message": "Subscription is active"
    }
    """
    try:
        from authentication.models import User, UserPlanAssignment

        try:
            # Get company user
            user = User.objects.get(company_id=company_id, role=User.Role.ADMIN)

            # Check if company has active subscription
            active_assignment = UserPlanAssignment.objects.filter(
                user=user,
                status='active'
            ).first()

            if active_assignment:
                return Response({
                    'success': True,
                    'is_active': True,
                    'company_id': company_id,
                    'plan_name': active_assignment.plan.get_plan_name_display(),
                    'message': 'Subscription is active'
                })
            else:
                return Response({
                    'success': True,
                    'is_active': False,
                    'company_id': company_id,
                    'plan_name': None,
                    'message': 'Subscription is inactive or cancelled'
                })

        except User.DoesNotExist:
            return Response({
                'success': False,
                'is_active': False,
                'company_id': company_id,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'success': False,
            'is_active': False,
            'company_id': company_id,
            'error': f'Failed to check subscription status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_config_view(request, company_id):
    """
    Get company-specific chatbot configuration for embed widget
    GET /api/chatbot/company-config/{company_id}/

    This endpoint is called by the chatbot.js script to get company-specific settings.

    Response:
    {
        "success": true,
        "config": {
            "companyId": "ZIL001",
            "companyName": "Zillion Technologies",
            "apiBaseUrl": "http://localhost:8001/api",
            "primaryColor": "#f7941d",
            "secondaryColor": "#652d90",
            "welcomeMessage": "Hello! How can I help you today?",
            "enableFileUpload": true,
            "chatbotTitle": "Zillion Support",
            "position": "bottom-right",
            "isActive": true
        }
    }
    """
    try:
        # First check subscription status
        from authentication.models import User, UserPlanAssignment

        try:
            user = User.objects.get(company_id=company_id)
            company_name = f"{user.first_name} {user.last_name}".strip() or f"Company {company_id}"

            # Check if company has active plan
            active_assignment = UserPlanAssignment.objects.filter(
                user=user, status='active'
            ).first()

            is_active = active_assignment is not None

            # If subscription is not active, return inactive config
            if not is_active:
                return Response({
                    'success': False,
                    'error': 'Subscription is inactive or cancelled',
                    'is_active': False
                }, status=status.HTTP_403_FORBIDDEN)

        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get company-specific chatbot configuration
        from .models import ChatbotConfiguration

        try:
            config = ChatbotConfiguration.objects.filter(company_id=company_id).first()
            if not config:
                # Create default config for this company
                config = ChatbotConfiguration.objects.create(
                    company_id=company_id,
                    primary_color="#f7941d",
                    secondary_color="#652d90",
                    welcome_message=f"Hello! Welcome to {company_name}. How can I help you today?",
                    enable_file_upload=True,
                    company_name=company_name,
                    position="bottom-right"
                )
                print(f"Created default chatbot config for company {company_id}")
        except Exception as e:
            print(f"Error handling chatbot config for {company_id}: {e}")
            # Fallback to default values
            config = None

        # Determine API base URL based on environment
        request_host = request.get_host()
        if 'localhost' in request_host or '127.0.0.1' in request_host:
            api_base_url = f"http://{request_host}/api"
        else:
            api_base_url = f"https://{request_host}/api"

        # Build response
        response_config = {
            "companyId": company_id,
            "companyName": company_name,
            "apiBaseUrl": api_base_url,
            "primaryColor": config.primary_color if config else "#f7941d",
            "secondaryColor": config.secondary_color if config else "#652d90",
            "welcomeMessage": config.welcome_message if config else "Hello! How can I help you today?",
            "enableFileUpload": config.enable_file_upload if config else True,
            "chatbotTitle": config.company_name if config and config.company_name else f"{company_name} Support",
            "position": config.position if config else "bottom-right",
            "isActive": is_active
        }

        return Response({
            'success': True,
            'config': response_config
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get company config: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # You might want to add authentication here
def update_chatbot_config_view(request):
    """
    Update company-specific chatbot configuration
    POST /api/chatbot/update-chatbot-config/

    Expected data:
    {
        "company_id": "SPE002",
        "primary_color": "#ff0000",
        "secondary_color": "#00ff00",
        "position": "top-left",
        "welcome_message": "Welcome to our support!",
        "iframe_width": 450,
        "iframe_height": 650
    }
    """
    try:
        company_id = request.data.get('company_id')
        if not company_id:
            return Response({
                'success': False,
                'error': 'company_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify company exists
        from authentication.models import User
        try:
            User.objects.get(company_id=company_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get or create chatbot configuration
        from .models import ChatbotConfiguration
        config, created = ChatbotConfiguration.objects.get_or_create(
            company_id=company_id,
            defaults={
                'primary_color': '#f7941d',
                'secondary_color': '#652d90',
                'position': 'bottom-right',
                'welcome_message': 'Hello! How can I help you today?',
                'iframe_width': 400,
                'iframe_height': 600,
                'enable_file_upload': True
            }
        )

        # Update configuration with provided data
        if 'primary_color' in request.data:
            config.primary_color = request.data['primary_color']
        if 'secondary_color' in request.data:
            config.secondary_color = request.data['secondary_color']
        if 'position' in request.data:
            config.position = request.data['position']
        if 'welcome_message' in request.data:
            config.welcome_message = request.data['welcome_message']
        if 'iframe_width' in request.data:
            config.iframe_width = request.data['iframe_width']
        if 'iframe_height' in request.data:
            config.iframe_height = request.data['iframe_height']
        if 'enable_file_upload' in request.data:
            config.enable_file_upload = request.data['enable_file_upload']

        config.save()

        return Response({
            'success': True,
            'message': 'Chatbot configuration updated successfully',
            'config': {
                'company_id': config.company_id,
                'primary_color': config.primary_color,
                'secondary_color': config.secondary_color,
                'position': config.position,
                'welcome_message': config.welcome_message,
                'iframe_width': config.iframe_width,
                'iframe_height': config.iframe_height,
                'enable_file_upload': config.enable_file_upload
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to update chatbot config: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def chatbot_detection_report_view(request):
    """
    Receive chatbot detection reports from embedded scripts
    POST /api/chatbot/detection-report/

    Expected data:
    {
        "company_id": "ZIL001",
        "has_existing_chatbot": true,
        "detected_at": "2024-01-01T12:00:00Z",
        "page_url": "https://client-website.com"
    }
    """
    try:
        company_id = request.data.get('company_id')
        has_existing_chatbot = request.data.get('has_existing_chatbot', False)
        page_url = request.data.get('page_url', 'Unknown')

        if not company_id:
            return Response({
                'success': False,
                'error': 'company_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Store the detection report (you can create a model for this if needed)
        # For now, we'll just log it and store in cache/session
        from django.core.cache import cache

        cache_key = f'chatbot_detection_{company_id}'
        detection_data = {
            'has_existing_chatbot': has_existing_chatbot,
            'page_url': page_url,
            'last_detected': timezone.now().isoformat(),
            'detection_count': cache.get(f'{cache_key}_count', 0) + 1
        }

        # Store for 24 hours
        cache.set(cache_key, detection_data, 86400)
        cache.set(f'{cache_key}_count', detection_data['detection_count'], 86400)

        print(f"📊 Chatbot Detection Report for {company_id}:")
        print(f"   - Has existing chatbot: {has_existing_chatbot}")
        print(f"   - Page URL: {page_url}")
        print(f"   - Detection count: {detection_data['detection_count']}")

        return Response({
            'success': True,
            'message': 'Detection report received',
            'data': detection_data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to process detection report: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # You might want to add authentication here
def chatbot_detection_status_view(request, company_id):
    """
    Get chatbot detection status for admin dashboard
    GET /api/chatbot/detection-status/ZIL001/

    Returns:
    {
        "success": true,
        "has_existing_chatbot": true,
        "page_url": "https://client-website.com",
        "last_detected": "2024-01-01T12:00:00Z",
        "detection_count": 5
    }
    """
    try:
        from django.core.cache import cache

        cache_key = f'chatbot_detection_{company_id}'
        detection_data = cache.get(cache_key)

        if not detection_data:
            return Response({
                'success': True,
                'has_existing_chatbot': False,
                'message': 'No detection reports received yet',
                'page_url': None,
                'last_detected': None,
                'detection_count': 0
            })

        return Response({
            'success': True,
            'has_existing_chatbot': detection_data.get('has_existing_chatbot', False),
            'page_url': detection_data.get('page_url', 'Unknown'),
            'last_detected': detection_data.get('last_detected'),
            'detection_count': detection_data.get('detection_count', 0),
            'message': 'Existing chatbot detected on client website' if detection_data.get('has_existing_chatbot') else 'No conflicts detected'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get detection status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== COMPANY-SPECIFIC FAQ MANAGEMENT (ADMIN) ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_company_faq_list_view(request):
    """
    Get company-specific FAQs for the current admin's company
    GET /api/chatbot/admin/company-faqs/
    """
    # Ensure user is admin
    if request.user.role != User.Role.ADMIN:
        return Response({'error': 'Only admins can access company FAQs'}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.user.company_id
    if not company_id:
        return Response({'error': 'Company ID not found'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get company-specific FAQ file path
        company_faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', f'company_{company_id}_faq.json')

        if not os.path.exists(company_faq_file_path):
            # Create empty company FAQ file
            os.makedirs(os.path.dirname(company_faq_file_path), exist_ok=True)
            with open(company_faq_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "company_info": {
                        "company_id": company_id,
                        "company_name": request.user.name or f"Company {company_id}",
                        "created_at": timezone.now().isoformat(),
                        "last_updated": timezone.now().isoformat()
                    },
                    "company_faqs": {}
                }, f, indent=2, ensure_ascii=False)

        # Read company FAQs
        with open(company_faq_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Count total FAQs
        total_faqs = 0
        faqs_list = []

        for category, questions in data.get('company_faqs', {}).items():
            if isinstance(questions, list):
                total_faqs += len(questions)
                for faq in questions:
                    faqs_list.append({
                        'id': faq.get('chunk_id', ''),
                        'question': faq.get('question', ''),
                        'answer': faq.get('answer', ''),
                        'category': category,
                        'section': faq.get('section', 'Company FAQ'),
                        'document': faq.get('document', f'{company_id} Company FAQ'),
                        'created_at': faq.get('created_at', ''),
                        'updated_at': faq.get('updated_at', '')
                    })

        return Response({
            'count': total_faqs,
            'company_id': company_id,
            'company_name': data.get('company_info', {}).get('company_name', company_id),
            'results': faqs_list
        })

    except Exception as e:
        return Response({'error': f'Failed to load company FAQs: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_company_faq_create_view(request):
    """
    Create a new company-specific FAQ
    POST /api/chatbot/admin/company-faqs/create/
    """
    # Ensure user is admin
    if request.user.role != User.Role.ADMIN:
        return Response({'error': 'Only admins can create company FAQs'}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.user.company_id
    if not company_id:
        return Response({'error': 'Company ID not found'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate input
    question = request.data.get('question', '').strip()
    answer = request.data.get('answer', '').strip()
    category = request.data.get('category', 'General')

    # Handle category if it's a list (from React tags mode)
    if isinstance(category, list):
        category = category[0] if category else 'General'
    category = str(category).strip()

    print(f"DEBUG: Creating FAQ - Question: {question[:50]}..., Category: {category}")

    if not question or not answer:
        return Response({'error': 'Question and answer are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get company-specific FAQ file path
        company_faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', f'company_{company_id}_faq.json')

        # Load existing data or create new
        if os.path.exists(company_faq_file_path):
            with open(company_faq_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            os.makedirs(os.path.dirname(company_faq_file_path), exist_ok=True)
            data = {
                "company_info": {
                    "company_id": company_id,
                    "company_name": request.user.name or f"Company {company_id}",
                    "created_at": timezone.now().isoformat(),
                    "last_updated": timezone.now().isoformat()
                },
                "company_faqs": {}
            }

        # Generate unique chunk ID
        chunk_id = f"company_{company_id}_{uuid.uuid4().hex[:8]}"

        # Create new FAQ entry
        new_faq = {
            "chunk_id": chunk_id,
            "question": question,
            "answer": answer,
            "section": "Company FAQ",
            "document": f"{company_id} Company FAQ",
            "created_at": timezone.now().isoformat(),
            "updated_at": timezone.now().isoformat()
        }

        # Add to category
        if category not in data['company_faqs']:
            data['company_faqs'][category] = []

        data['company_faqs'][category].append(new_faq)
        data['company_info']['last_updated'] = timezone.now().isoformat()

        # Save updated data
        with open(company_faq_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Auto-refresh vectors after creating FAQ
        try:
            from .utils.rag_system import rag_system
            print(f"DEBUG: Auto-refreshing vectors for company {company_id}")
            success = rag_system.refresh_company_vectors(company_id, data)
            if success:
                print(f"DEBUG: ✅ Vectors refreshed successfully for {company_id}")
            else:
                print(f"DEBUG: ❌ Failed to refresh vectors for {company_id}")
        except Exception as e:
            print(f"DEBUG: Error auto-refreshing vectors: {e}")
            # Don't fail the FAQ creation if vector refresh fails

        return Response({
            'message': 'Company FAQ created successfully',
            'faq': {
                'id': chunk_id,
                'question': question,
                'answer': answer,
                'category': category,
                'section': 'Company FAQ',
                'document': f'{company_id} Company FAQ',
                'created_at': new_faq['created_at'],
                'updated_at': new_faq['updated_at']
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        import traceback
        print(f"ERROR: Failed to create company FAQ: {str(e)}")
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return Response({'error': f'Failed to create company FAQ: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_company_faq_detail_view(request, faq_id):
    """
    Get, update, or delete a specific company FAQ
    GET/PUT/DELETE /api/chatbot/admin/company-faqs/{faq_id}/
    """
    # Ensure user is admin
    if request.user.role != User.Role.ADMIN:
        return Response({'error': 'Only admins can manage company FAQs'}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.user.company_id
    if not company_id:
        return Response({'error': 'Company ID not found'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get company-specific FAQ file path
        company_faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', f'company_{company_id}_faq.json')

        if not os.path.exists(company_faq_file_path):
            return Response({'error': 'Company FAQ file not found'}, status=status.HTTP_404_NOT_FOUND)

        # Load existing data
        with open(company_faq_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Find the FAQ
        found_faq = None
        found_category = None
        found_index = None

        for category, questions in data.get('company_faqs', {}).items():
            if isinstance(questions, list):
                for i, faq in enumerate(questions):
                    if faq.get('chunk_id') == faq_id:
                        found_faq = faq
                        found_category = category
                        found_index = i
                        break
                if found_faq:
                    break

        if not found_faq:
            return Response({'error': 'FAQ not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            # Return FAQ details
            return Response({
                'id': found_faq.get('chunk_id', ''),
                'question': found_faq.get('question', ''),
                'answer': found_faq.get('answer', ''),
                'category': found_category,
                'section': found_faq.get('section', 'Company FAQ'),
                'document': found_faq.get('document', f'{company_id} Company FAQ'),
                'created_at': found_faq.get('created_at', ''),
                'updated_at': found_faq.get('updated_at', '')
            })

        elif request.method == 'PUT':
            # Update FAQ
            question = request.data.get('question', found_faq.get('question', '')).strip()
            answer = request.data.get('answer', found_faq.get('answer', '')).strip()
            new_category = request.data.get('category', found_category).strip()

            if not question or not answer:
                return Response({'error': 'Question and answer are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Update FAQ data
            updated_faq = found_faq.copy()
            updated_faq.update({
                'question': question,
                'answer': answer,
                'updated_at': timezone.now().isoformat()
            })

            # Handle category change
            if new_category != found_category:
                # Remove from old category
                data['company_faqs'][found_category].pop(found_index)
                if not data['company_faqs'][found_category]:
                    del data['company_faqs'][found_category]

                # Add to new category
                if new_category not in data['company_faqs']:
                    data['company_faqs'][new_category] = []
                data['company_faqs'][new_category].append(updated_faq)
            else:
                # Update in same category
                data['company_faqs'][found_category][found_index] = updated_faq

            data['company_info']['last_updated'] = timezone.now().isoformat()

            # Save updated data
            with open(company_faq_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Auto-refresh vectors after updating FAQ
            try:
                from .utils.rag_system import rag_system
                print(f"DEBUG: Auto-refreshing vectors after update for company {company_id}")
                success = rag_system.refresh_company_vectors(company_id, data)
                if success:
                    print(f"DEBUG: ✅ Vectors refreshed successfully after update for {company_id}")
                else:
                    print(f"DEBUG: ❌ Failed to refresh vectors after update for {company_id}")
            except Exception as e:
                print(f"DEBUG: Error auto-refreshing vectors after update: {e}")

            return Response({
                'message': 'Company FAQ updated successfully',
                'faq': {
                    'id': updated_faq['chunk_id'],
                    'question': question,
                    'answer': answer,
                    'category': new_category,
                    'section': 'Company FAQ',
                    'document': f'{company_id} Company FAQ',
                    'created_at': updated_faq['created_at'],
                    'updated_at': updated_faq['updated_at']
                }
            })

        elif request.method == 'DELETE':
            # Delete FAQ
            data['company_faqs'][found_category].pop(found_index)
            if not data['company_faqs'][found_category]:
                del data['company_faqs'][found_category]

            data['company_info']['last_updated'] = timezone.now().isoformat()

            # Save updated data
            with open(company_faq_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Auto-refresh vectors after deleting FAQ
            try:
                from .utils.rag_system import rag_system
                print(f"DEBUG: Auto-refreshing vectors after delete for company {company_id}")
                success = rag_system.refresh_company_vectors(company_id, data)
                if success:
                    print(f"DEBUG: ✅ Vectors refreshed successfully after delete for {company_id}")
                else:
                    print(f"DEBUG: ❌ Failed to refresh vectors after delete for {company_id}")
            except Exception as e:
                print(f"DEBUG: Error auto-refreshing vectors after delete: {e}")

            return Response({'message': 'Company FAQ deleted successfully'})

    except Exception as e:
        return Response({'error': f'Failed to manage company FAQ: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_company_refresh_vectors_view(request):
    """
    Refresh vector database with company-specific FAQs
    POST /api/chatbot/admin/company-faqs/refresh-vectors/
    """
    # Ensure user is admin
    if request.user.role != User.Role.ADMIN:
        return Response({'error': 'Only admins can refresh company vectors'}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.user.company_id
    if not company_id:
        return Response({'error': 'Company ID not found'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .utils.vector_refresh_manager import vector_refresh_manager

        # Check if refresh is already in progress for this company
        if vector_refresh_manager.is_refresh_in_progress(company_id):
            return Response({
                'success': False,
                'message': f'Vector refresh already in progress for company {company_id}',
                'status': 'in_progress'
            }, status=status.HTTP_409_CONFLICT)

        # Start the company-specific refresh
        result = vector_refresh_manager.refresh_company_vectors(company_id)

        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'status': result['status'],
                'company_id': result.get('company_id'),
                'timestamp': result.get('timestamp'),
                'details': 'Company FAQ vectors have been safely refreshed using production-safe methods'
            })
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'status': result['status'],
                'details': 'Company vector refresh failed - check server logs for details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({
            'error': f'Failed to refresh company vectors: {str(e)}',
            'details': 'An unexpected error occurred during company vector refresh'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Convenience views for easier access
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_company_faq_update_view(request, faq_id):
    """Convenience endpoint for updating FAQ"""
    return admin_company_faq_detail_view(request, faq_id)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_company_faq_delete_view(request, faq_id):
    """Convenience endpoint for deleting FAQ"""
    return admin_company_faq_detail_view(request, faq_id)

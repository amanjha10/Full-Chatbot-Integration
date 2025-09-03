# chatbot/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
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
from authentication.models import User
from admin_dashboard.models import Agent

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

def get_rag_response(user_input):
    """Query RAG system for document-based answers"""
    try:
        result = rag_system.get_best_answer(user_input, min_score=0.2)  # Lowered minimum score
        if result:
            return result, result['score']
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
        # Try RAG system first
        rag_result, rag_score = get_rag_response(user_message)
        
        if rag_result and rag_score > 0.2:  # Lowered threshold for better matching
            response = {
                'response': rag_result['answer'],
                'suggestions': ['🌍 Choose Country', '🎓 Browse Programs', '🗣️ Talk to Advisor'],
                'type': 'rag_response',
                'session_id': chat_session.session_id
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
def file_upload_view(request):
    """
    Handle file uploads for chat messages
    POST /api/chatbot/upload/
    
    Request:
    {
        "file": <file_object>,
        "session_id": "session_uuid",
        "company_id": "COMP_123",  // Optional, extracted from JWT if available
        "message_context": "Optional context about the file"
    }
    
    Response:
    {
        "file_id": 123,
        "file_url": "/media/uploads/COMP_123/2024/08/file_123_document.pdf",
        "original_name": "document.pdf",
        "file_size": 1024000,
        "file_type": "document",
        "message": "File uploaded successfully"
    }
    """
    serializer = FileUploadRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = serializer.validated_data['file']
    session_id = serializer.validated_data['session_id']
    message_context = serializer.validated_data.get('message_context', '')
    
    # Extract company_id from request
    company_id = get_company_id_from_request(request)
    if not company_id:
        return Response({
            'error': 'company_id is required. Please provide company_id in request data or authenticate with valid JWT token.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get the chat session
        chat_session = ChatSession.objects.get(session_id=session_id, company_id=company_id)
        
        # Initialize file handler
        file_handler = FileUploadHandler()
        
        # Validate and save the file
        file_info = file_handler.save_file(uploaded_file, company_id, session_id)
        
        # Create UploadedFile record
        uploaded_file_obj = UploadedFile.objects.create(
            session=chat_session,
            user_profile=chat_session.user_profile,
            company_id=company_id,
            original_name=file_info['original_name'],
            filename=file_info['filename'],
            filepath=file_info['filepath'],
            file_size=file_info['file_size'],
            file_type=file_info['file_type'],
            message_context=message_context
        )
        
        response_data = {
            'file_id': uploaded_file_obj.id,
            'file_url': uploaded_file_obj.get_file_url(),
            'original_name': uploaded_file_obj.original_name,
            'file_size': uploaded_file_obj.file_size,
            'file_type': uploaded_file_obj.file_type,
            'message': 'File uploaded successfully'
        }
        
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

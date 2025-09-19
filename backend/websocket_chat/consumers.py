# websocket_chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from chatbot.models import ChatSession, ChatMessage
from admin_dashboard.models import Agent
from authentication.models import User


class CompanyChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for company-based chat rooms
    Handles real-time messaging between visitors and agents within the same company
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        
        # Validate company_id and session_id
        if not self.company_id:
            await self.close(code=4000)
            return
        
        # Create room group name
        self.room_group_name = f'chat_{self.company_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': f'Connected to {self.company_id} chat room',
            'timestamp': self.get_current_timestamp()
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'agent_join':
                await self.handle_agent_join(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_chat_message(self, data):
        """Handle chat message"""
        message = data.get('message', '')
        session_id = data.get('session_id', self.session_id)
        sender_type = data.get('sender_type', 'user')  # user, agent, bot
        sender_info = data.get('sender_info', {})
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        
        if not message and not file_url:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message or file is required'
            }))
            return
            
        if not session_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'session_id is required'
            }))
            return
        
        # Validate session belongs to this company
        session_valid = await self.validate_session_company(session_id)
        if not session_valid:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid session or company mismatch'
            }))
            return
        
        # Save message to database
        chat_message = await self.save_chat_message(session_id, message, sender_type, sender_info, file_url, file_name)
        
        if chat_message:
            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': message,
                    'session_id': session_id,
                    'sender_type': sender_type,
                    'sender_info': sender_info,
                    'message_id': chat_message.id,
                    'timestamp': chat_message.timestamp.isoformat(),
                    'file_url': file_url,
                    'file_name': file_name
                }
            )
    
    async def handle_agent_join(self, data):
        """Handle agent joining the chat"""
        agent_token = data.get('token')
        session_id = data.get('session_id')
        
        if not agent_token or not session_id:
            return
        
        # Validate agent token and company
        agent_info = await self.validate_agent_token(agent_token)
        if not agent_info or agent_info['company_id'] != self.company_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid agent token or company mismatch'
            }))
            return
        
        # Broadcast agent join to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'agent_join_broadcast',
                'agent_info': agent_info,
                'session_id': session_id,
                'timestamp': self.get_current_timestamp()
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicators"""
        session_id = data.get('session_id')
        is_typing = data.get('is_typing', False)
        sender_info = data.get('sender_info', {})
        
        # Broadcast typing indicator to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_broadcast',
                'session_id': session_id,
                'is_typing': is_typing,
                'sender_info': sender_info,
                'timestamp': self.get_current_timestamp()
            }
        )
    
    # Broadcast handlers
    async def chat_message_broadcast(self, event):
        """Send chat message to WebSocket"""
        message_data = {
            'type': 'chat_message',
            'message': event['message'],
            'session_id': event['session_id'],
            'sender_type': event['sender_type'],
            'sender_info': event['sender_info'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp']
        }
        
        # Add file information if present
        if event.get('file_url'):
            message_data['file_url'] = event['file_url']
        if event.get('file_name'):
            message_data['file_name'] = event['file_name']
            
        await self.send(text_data=json.dumps(message_data))
    
    async def agent_join_broadcast(self, event):
        """Send agent join notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'agent_joined',
            'agent_info': event['agent_info'],
            'session_id': event['session_id'],
            'timestamp': event['timestamp']
        }))
    
    async def typing_broadcast(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'session_id': event['session_id'],
            'is_typing': event['is_typing'],
            'sender_info': event['sender_info'],
            'timestamp': event['timestamp']
        }))
    
    # Database operations
    @database_sync_to_async
    def validate_session_company(self, session_id):
        """Validate that session belongs to the correct company"""
        try:
            session = ChatSession.objects.get(session_id=session_id)
            return session.company_id == self.company_id
        except ChatSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_chat_message(self, session_id, message, sender_type, sender_info, file_url=None, file_name=None):
        """Save chat message to database"""
        try:
            session = ChatSession.objects.get(session_id=session_id, company_id=self.company_id)
            
            # Create the chat message
            chat_message = ChatMessage.objects.create(
                session=session,
                message_type=sender_type,
                content=message or '',
                metadata=sender_info
            )
            
            # If there's a file attachment, find and link it
            if file_url and file_name:
                try:
                    from chatbot.models import UploadedFile, ChatFile

                    # Extract the filepath from the file_url (remove /media/ prefix)
                    if file_url.startswith('/media/'):
                        filepath = file_url[7:]  # Remove '/media/' prefix
                    elif file_url.startswith('http'):
                        # Extract path from full URL
                        from urllib.parse import urlparse
                        parsed_url = urlparse(file_url)
                        filepath = parsed_url.path[7:] if parsed_url.path.startswith('/media/') else parsed_url.path
                    else:
                        filepath = file_url

                    uploaded_file = None

                    # First try to find UploadedFile (for agent uploads)
                    uploaded_file = UploadedFile.objects.filter(
                        session__session_id=session_id,
                        filepath=filepath
                    ).first()

                    # If not found by filepath, try by original_name
                    if not uploaded_file:
                        uploaded_file = UploadedFile.objects.filter(
                            session__session_id=session_id,
                            original_name=file_name
                        ).order_by('-uploaded_at').first()

                    # If still not found, try ChatFile (for user uploads)
                    if not uploaded_file:
                        chat_file = ChatFile.objects.filter(
                            session_id=session_id,
                            original_name=file_name
                        ).order_by('-created_at').first()

                        if chat_file:
                            # Create an UploadedFile record from ChatFile for consistency
                            uploaded_file = UploadedFile.objects.create(
                                session=chat_file.chat_session,
                                user_profile=chat_file.user_profile,
                                company_id=chat_file.company_id,
                                original_name=chat_file.original_name,
                                filename=chat_file.original_name,
                                filepath=str(chat_file.file),  # Convert FileField to string
                                file_size=chat_file.size,
                                file_type=chat_file.mime_type.split('/')[0] if '/' in chat_file.mime_type else 'file',
                                uploaded_by_agent=chat_file.uploader == 'agent'
                            )
                            print(f"Created UploadedFile from ChatFile: {file_name}")

                    if uploaded_file:
                        chat_message.attachments.add(uploaded_file)
                        chat_message.save()
                        print(f"Successfully linked file {file_name} to message {chat_message.id}")
                    else:
                        print(f"Could not find uploaded file: {file_name} with path: {filepath}")
                except Exception as e:
                    print(f"Error linking file to message: {e}")
            
            return chat_message
        except ChatSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def validate_agent_token(self, token):
        """Validate agent JWT token and return agent info"""
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            from django.contrib.auth import get_user_model
            
            # Validate token
            UntypedToken(token)
            
            # Get user from token
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            
            if user.role == User.Role.AGENT:
                agent = Agent.objects.get(user=user)
                return {
                    'id': agent.id,
                    'name': agent.name,
                    'email': agent.email,
                    'company_id': agent.company_id
                }
            elif user.role in [User.Role.ADMIN, User.Role.SUPERADMIN]:
                return {
                    'id': user.id,
                    'name': user.name or user.username,
                    'email': user.email,
                    'company_id': user.company_id,
                    'role': user.role
                }
            
            return None
            
        except (InvalidToken, TokenError, User.DoesNotExist, Agent.DoesNotExist):
            return None
    
    def get_current_timestamp(self):
        """Get current timestamp in ISO format"""
        from django.utils import timezone
        return timezone.now().isoformat()


class AgentChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer specifically for agents
    Handles agent dashboard real-time updates
    """
    
    async def connect(self):
        """Handle agent WebSocket connection"""
        # Get JWT token from query string
        token = self.scope['query_string'].decode().split('token=')[-1] if 'token=' in self.scope['query_string'].decode() else None
        
        if not token:
            await self.close(code=4001)
            return
        
        # Validate agent
        agent_info = await self.validate_agent_token(token)
        if not agent_info:
            await self.close(code=4002)
            return
        
        self.agent_info = agent_info
        self.company_id = agent_info['company_id']
        
        # Join agent room for this company
        self.agent_room_name = f'agents_{self.company_id}'
        
        await self.channel_layer.group_add(
            self.agent_room_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'agent_connected',
            'agent_info': self.agent_info,
            'message': 'Connected to agent dashboard'
        }))
    
    async def disconnect(self, close_code):
        """Handle agent WebSocket disconnection"""
        if hasattr(self, 'agent_room_name'):
            await self.channel_layer.group_discard(
                self.agent_room_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle message from agent WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'status_update':
                await self.handle_status_update(text_data_json)
            elif message_type == 'session_update':
                await self.handle_session_update(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_status_update(self, data):
        """Handle agent status update"""
        new_status = data.get('status')
        if new_status in ['AVAILABLE', 'BUSY', 'OFFLINE']:
            # Update agent status in database
            await self.update_agent_status(new_status)
            
            # Broadcast to other agents in same company
            await self.channel_layer.group_send(
                self.agent_room_name,
                {
                    'type': 'agent_status_broadcast',
                    'agent_id': self.agent_info['id'],
                    'agent_name': self.agent_info['name'],
                    'status': new_status,
                    'timestamp': self.get_current_timestamp()
                }
            )
    
    async def handle_session_update(self, data):
        """Handle session assignment/update"""
        session_id = data.get('session_id')
        action = data.get('action')  # assign, resolve, transfer
        
        if action and session_id:
            # Broadcast session update to agents
            await self.channel_layer.group_send(
                self.agent_room_name,
                {
                    'type': 'session_update_broadcast',
                    'session_id': session_id,
                    'action': action,
                    'agent_id': self.agent_info['id'],
                    'agent_name': self.agent_info['name'],
                    'timestamp': self.get_current_timestamp()
                }
            )
    
    # Broadcast handlers
    async def agent_status_broadcast(self, event):
        """Send agent status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'agent_status_update',
            'agent_id': event['agent_id'],
            'agent_name': event['agent_name'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    async def session_update_broadcast(self, event):
        """Send session update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'session_update',
            'session_id': event['session_id'],
            'action': event['action'],
            'agent_id': event['agent_id'],
            'agent_name': event['agent_name'],
            'timestamp': event['timestamp']
        }))
    
    # Database operations
    @database_sync_to_async
    def validate_agent_token(self, token):
        """Validate agent JWT token"""
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            
            UntypedToken(token)
            
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            
            if user.role == User.Role.AGENT:
                agent = Agent.objects.get(user=user)
                return {
                    'id': agent.id,
                    'name': agent.name,
                    'email': agent.email,
                    'company_id': agent.company_id
                }
            
            return None
            
        except Exception:
            return None
    
    @database_sync_to_async
    def update_agent_status(self, status):
        """Update agent status in database"""
        try:
            agent = Agent.objects.get(id=self.agent_info['id'])
            agent.update_status(status)
        except Agent.DoesNotExist:
            pass
    
    def get_current_timestamp(self):
        """Get current timestamp in ISO format"""
        from django.utils import timezone
        return timezone.now().isoformat()

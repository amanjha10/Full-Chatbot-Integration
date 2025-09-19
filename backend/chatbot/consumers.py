"""
WebSocket consumers for real-time communication
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from authentication.models import User
from .models import ChatSession, UserProfile, ChatbotConfiguration

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat functionality
    """
    
    async def connect(self):
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.company_id}_{self.session_id}'

        print(f"DEBUG: ChatConsumer connecting - company_id: {self.company_id}, session_id: {self.session_id}")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Chat WebSocket connected: {self.company_id}/{self.session_id}")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connected successfully',
            'session_id': self.session_id,
            'company_id': self.company_id
        }))
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connected successfully',
            'session_id': self.session_id,
            'company_id': self.company_id
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Chat WebSocket disconnected: {self.company_id}/{self.session_id}")

    async def receive(self, text_data):
        """
        Handle WebSocket messages - primarily for human agent escalation
        Regular chatbot messages should use DRF API
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')

            if message_type == 'ping':
                # Simple ping-pong test
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'WebSocket is working!',
                    'timestamp': text_data_json.get('timestamp')
                }))

            elif message_type == 'request_file_list':
                # Handle file list request for reconnection
                await self.handle_file_list_request(text_data_json)

            elif message_type == 'escalate_to_human':
                # Handle escalation request
                await self.handle_escalation(text_data_json)

            elif message_type == 'chat_message':
                # Only handle if this is an escalated session with human agent
                await self.handle_human_chat_message(text_data_json)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in ChatConsumer.receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in ChatConsumer.receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_type': event['sender_type'],
            'session_id': event.get('session_id', self.session_id),  # Use self.session_id as fallback
            'timestamp': event.get('timestamp')
        }))

    async def file_shared(self, event):
        """Send file_shared event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'file_shared',
            **event['payload']
        }))

    async def handle_escalation(self, data):
        """Handle escalation to human agent"""
        try:
            from human_handoff.models import HumanHandoffSession
            from .models import ChatSession

            # Get chat session
            chat_session = await self.get_chat_session()

            # Create handoff session
            handoff_session = await self.create_handoff_session(
                chat_session,
                data.get('reason', 'User requested human assistance')
            )

            # Notify admin dashboard
            await self.notify_admin_dashboard(chat_session, handoff_session)

            # Send confirmation to user
            await self.send(text_data=json.dumps({
                'type': 'escalation_confirmed',
                'message': '🔄 Your conversation has been escalated to a human agent. Please wait for assistance.',
                'session_id': self.session_id,
                'handoff_id': handoff_session.id if handoff_session else None
            }))

        except Exception as e:
            logger.error(f"Error handling escalation: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to escalate to human agent'
            }))

    async def handle_human_chat_message(self, data):
        """Handle chat message in escalated session"""
        try:
            # Check if session is escalated
            is_escalated = await self.check_if_escalated()

            if not is_escalated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Session not escalated. Use DRF API for chatbot messages.'
                }))
                return

            # Broadcast message to agent and user
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data['message'],
                    'sender_type': data.get('sender_type', 'user'),
                    'session_id': self.session_id,
                    'timestamp': data.get('timestamp')
                }
            )

        except Exception as e:
            logger.error(f"Error handling human chat message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to send message'
            }))

    async def handle_file_list_request(self, data):
        """Handle request for file list (for reconnection)"""
        try:
            files = await self.get_session_files()
            await self.send(text_data=json.dumps({
                'type': 'file_list',
                'files': files,
                'session_id': self.session_id,
                'company_id': self.company_id
            }))
        except Exception as e:
            logger.error(f"Error handling file list request: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to retrieve file list'
            }))

    @database_sync_to_async
    def get_session_files(self):
        """Get files for current session"""
        from .models import ChatFile
        files = ChatFile.objects.filter(
            company_id=self.company_id,
            session_id=self.session_id
        ).order_by('-created_at')

        return [
            {
                'id': f.id,
                'company_id': f.company_id,
                'session_id': f.session_id,
                'uploader': f.uploader,
                'url': f.get_file_url(),
                'name': f.original_name,
                'mime_type': f.mime_type,
                'size': f.size,
                'thumbnail': f.thumbnail,
                'created_at': f.created_at.isoformat()
            }
            for f in files
        ]

    @database_sync_to_async
    def get_chat_session(self):
        """Get chat session from database"""
        from .models import ChatSession
        return ChatSession.objects.get(session_id=self.session_id)

    @database_sync_to_async
    def create_handoff_session(self, chat_session, reason):
        """Create handoff session"""
        from human_handoff.models import HumanHandoffSession
        handoff_session, created = HumanHandoffSession.objects.get_or_create(
            chat_session=chat_session,
            defaults={
                'escalation_reason': reason,
                'priority': 'medium'
            }
        )
        # Update chat session status
        chat_session.status = 'escalated'
        chat_session.save()
        return handoff_session

    async def notify_admin_dashboard(self, chat_session, handoff_session):
        """Notify admin dashboard of escalation"""
        try:
            await self.channel_layer.group_send(
                f'handoff_{chat_session.company_id}',
                {
                    'type': 'session_escalated',
                    'data': {
                        'session_id': chat_session.session_id,
                        'company_id': chat_session.company_id,
                        'reason': handoff_session.escalation_reason,
                        'priority': handoff_session.priority,
                        'timestamp': str(handoff_session.created_at)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error notifying admin dashboard: {str(e)}")

    @database_sync_to_async
    def check_if_escalated(self):
        """Check if session is escalated"""
        from .models import ChatSession
        try:
            chat_session = ChatSession.objects.get(session_id=self.session_id)
            return chat_session.status == 'escalated'
        except ChatSession.DoesNotExist:
            return False




class ConfigConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time configuration updates
    """
    
    async def connect(self):
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.room_group_name = f'config_{self.company_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Config WebSocket connected: {self.company_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Config WebSocket disconnected: {self.company_id}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'config_update')
            
            if message_type == 'config_update':
                # Broadcast configuration update to all clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'config_update',
                        'config': text_data_json.get('config', {}),
                        'company_id': self.company_id
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in ConfigConsumer.receive: {str(e)}")

    async def config_update(self, event):
        """Send configuration update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'config_update',
            'config': event['config'],
            'company_id': event['company_id']
        }))


class UserManagementConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time user management updates
    """
    
    async def connect(self):
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.room_group_name = f'users_{self.company_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User Management WebSocket connected: {self.company_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User Management WebSocket disconnected: {self.company_id}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'user_update')
            
            if message_type == 'user_update':
                # Broadcast user update to all admin clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_update',
                        'action': text_data_json.get('action'),  # 'created', 'updated', 'deleted'
                        'user_data': text_data_json.get('user_data', {}),
                        'company_id': self.company_id
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in UserManagementConsumer.receive: {str(e)}")

    async def user_update(self, event):
        """Send user update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_update',
            'action': event['action'],
            'user_data': event['user_data'],
            'company_id': event['company_id']
        }))


# Utility function to send real-time updates
async def send_config_update(company_id, config_data):
    """Send configuration update to all connected clients"""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'config_{company_id}',
        {
            'type': 'config_update',
            'config': config_data,
            'company_id': company_id
        }
    )


async def send_user_update(company_id, action, user_data):
    """Send user management update to all connected admin clients"""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'users_{company_id}',
        {
            'type': 'user_update',
            'action': action,
            'user_data': user_data,
            'company_id': company_id
        }
    )

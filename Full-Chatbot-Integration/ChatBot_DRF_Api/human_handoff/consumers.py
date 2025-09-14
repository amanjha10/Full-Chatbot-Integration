"""
WebSocket consumers for human handoff system
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone


class HumanHandoffConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time human handoff updates
    URL: ws://localhost:8000/ws/handoff/COMPANY_ID/
    """
    
    async def connect(self):
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.room_group_name = f'handoff_{self.company_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to handoff updates for company {self.company_id}'
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    # Receive message from room group
    async def handoff_update(self, event):
        """Send handoff update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'handoff_update',
            'data': event['data']
        }))
    
    async def session_assigned(self, event):
        """Send session assignment update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'session_assigned',
            'data': event['data']
        }))
    
    async def session_escalated(self, event):
        """Send session escalation update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'session_escalated',
            'data': event['data']
        }))


class AgentDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for agent dashboard updates and real-time chat
    URL: ws://localhost:8000/ws/agent/AGENT_ID/
    """

    async def connect(self):
        self.agent_id = self.scope['url_route']['kwargs']['agent_id']
        self.room_group_name = f'agent_{self.agent_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update agent status to AVAILABLE when connected
        await self.update_agent_status('AVAILABLE')

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to agent dashboard for agent {self.agent_id}',
            'agent_id': self.agent_id
        }))
    
    async def disconnect(self, close_code):
        # Update agent status to OFFLINE when disconnected
        await self.update_agent_status('OFFLINE')

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    # Receive message from room group
    async def session_assigned(self, event):
        """Send session assignment to agent"""
        await self.send(text_data=json.dumps({
            'type': 'session_assigned',
            'data': event['data']
        }))
    
    async def session_update(self, event):
        """Send session update to agent"""
        await self.send(text_data=json.dumps({
            'type': 'session_update',
            'data': event['data']
        }))

    async def chat_message(self, event):
        """Send chat message to agent"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['data']
        }))

    @database_sync_to_async
    def update_agent_status(self, status):
        """Update agent status in database"""
        try:
            from admin_dashboard.models import Agent
            agent = Agent.objects.get(id=self.agent_id)
            if status == 'AVAILABLE':
                agent.set_online()
            elif status == 'BUSY':
                agent.set_busy()
            elif status == 'OFFLINE':
                agent.set_offline()
            print(f"DEBUG: Updated agent {self.agent_id} status to {status}")
        except Exception as e:
            print(f"DEBUG: Error updating agent status: {e}")


class ChatbotUserConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chatbot users during human handoff
    URL: ws://localhost:8000/ws/chat/COMPANY_ID/SESSION_ID/
    """

    async def connect(self):
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.company_id}_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to chat session {self.session_id}',
            'session_id': self.session_id,
            'company_id': self.company_id
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle messages from chatbot user"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'chat_message':
                message = text_data_json.get('message', '')

                # Save message to database
                await self.save_chat_message(message, 'user')

                # Forward message to assigned agent
                await self.forward_to_agent(message)

            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def agent_message(self, event):
        """Receive message from agent and send to user"""
        await self.send(text_data=json.dumps({
            'type': 'agent_message',
            'data': event['data']
        }))
    
    async def chat_message(self, event):
        """Handle chat messages from both users and agents"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event.get('message_id'),
            'sender_type': event.get('sender_type'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp'),
            'sender_name': event.get('sender_name')
        }))

    @database_sync_to_async
    def save_chat_message(self, message, sender_type):
        """Save chat message to database"""
        try:
            from chatbot.models import ChatSession, ChatMessage
            chat_session = ChatSession.objects.get(session_id=self.session_id)
            ChatMessage.objects.create(
                session=chat_session,
                message_type=sender_type,
                content=message
            )
        except Exception as e:
            print(f"DEBUG: Error saving chat message: {e}")

    @database_sync_to_async
    def forward_to_agent(self, message):
        """Forward user message to assigned agent"""
        try:
            from chatbot.models import ChatSession
            from human_handoff.models import HumanHandoffSession

            chat_session = ChatSession.objects.get(session_id=self.session_id)
            handoff_session = HumanHandoffSession.objects.get(chat_session=chat_session)

            if handoff_session.agent:
                # Send message to agent via WebSocket
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'agent_{handoff_session.agent.id}',
                    {
                        'type': 'chat_message',
                        'data': {
                            'session_id': self.session_id,
                            'message': message,
                            'sender': 'user',
                            'timestamp': str(timezone.now())
                        }
                    }
                )
        except Exception as e:
            print(f"DEBUG: Error forwarding to agent: {e}")

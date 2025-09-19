import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from authentication.models import User, UserPlanAssignment


class SubscriptionStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time subscription status updates.
    
    This consumer allows the chatbot.js script to receive real-time notifications
    when a company's subscription is cancelled or reactivated.
    """

    async def connect(self):
        """Accept WebSocket connection and join company-specific group"""
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.group_name = f"company_{self.company_id}"

        # Join company-specific group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send initial subscription status
        subscription_status = await self.get_subscription_status()
        await self.send(text_data=json.dumps({
            'type': 'subscription_status',
            'company_id': self.company_id,
            'is_active': subscription_status['is_active'],
            'plan_name': subscription_status.get('plan_name'),
            'message': 'Connected to subscription status updates'
        }))

    async def disconnect(self, close_code):
        """Leave company-specific group when disconnecting"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle messages from WebSocket (not used in this implementation)"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'check_status':
                # Client requesting current subscription status
                subscription_status = await self.get_subscription_status()
                await self.send(text_data=json.dumps({
                    'type': 'subscription_status',
                    'company_id': self.company_id,
                    'is_active': subscription_status['is_active'],
                    'plan_name': subscription_status.get('plan_name'),
                    'message': 'Current subscription status'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def subscription_cancelled(self, event):
        """Handle subscription cancellation event"""
        await self.send(text_data=json.dumps({
            'type': 'subscription_cancelled',
            'company_id': event['company_id'],
            'message': event['message']
        }))

    async def subscription_reactivated(self, event):
        """Handle subscription reactivation event"""
        await self.send(text_data=json.dumps({
            'type': 'subscription_reactivated',
            'company_id': event['company_id'],
            'plan_name': event.get('plan_name'),
            'message': event['message']
        }))

    @database_sync_to_async
    def get_subscription_status(self):
        """Get current subscription status for the company"""
        try:
            user = User.objects.get(company_id=self.company_id, role=User.Role.ADMIN)
            active_assignment = UserPlanAssignment.objects.filter(
                user=user, 
                status='active'
            ).first()

            if active_assignment:
                return {
                    'is_active': True,
                    'plan_name': active_assignment.plan.get_plan_name_display()
                }
            else:
                return {
                    'is_active': False,
                    'plan_name': None
                }
        except User.DoesNotExist:
            return {
                'is_active': False,
                'plan_name': None
            }

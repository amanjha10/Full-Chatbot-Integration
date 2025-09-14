# human_handoff/serializers.py
from rest_framework import serializers
from .models import HumanHandoffSession, AgentActivity, SessionTransfer
from chatbot.models import ChatSession, UserProfile
from admin_dashboard.models import Agent

class HumanHandoffSessionSerializer(serializers.ModelSerializer):
    chat_session_id = serializers.CharField(source='chat_session.session_id', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    user_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = HumanHandoffSession
        fields = [
            'id', 'chat_session_id', 'agent', 'agent_name', 'escalated_at', 
            'resolved_at', 'escalation_reason', 'notes', 'priority', 'user_profile'
        ]
    
    def get_user_profile(self, obj):
        if obj.chat_session.user_profile:
            return {
                'name': obj.chat_session.user_profile.name,
                'phone': obj.chat_session.user_profile.phone,
                'email': obj.chat_session.user_profile.email
            }
        return None

class AgentActivitySerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    class Meta:
        model = AgentActivity
        fields = [
            'id', 'agent', 'agent_name', 'activity_type', 'description', 
            'metadata', 'timestamp', 'ip_address'
        ]

class SessionTransferSerializer(serializers.ModelSerializer):
    from_agent_name = serializers.CharField(source='from_agent.name', read_only=True)
    to_agent_name = serializers.CharField(source='to_agent.name', read_only=True)
    transferred_by_username = serializers.CharField(source='transferred_by.username', read_only=True)
    
    class Meta:
        model = SessionTransfer
        fields = [
            'id', 'handoff_session', 'from_agent', 'from_agent_name', 
            'to_agent', 'to_agent_name', 'reason', 'transferred_at', 
            'transferred_by', 'transferred_by_username'
        ]

# Request Serializers
class EscalateSessionSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=100)
    reason = serializers.CharField(max_length=500)
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
        default='medium'
    )

class AssignSessionSerializer(serializers.Serializer):
    handoff_session_id = serializers.IntegerField()
    agent_id = serializers.IntegerField()

class ResolveSessionSerializer(serializers.Serializer):
    handoff_session_id = serializers.IntegerField()
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)

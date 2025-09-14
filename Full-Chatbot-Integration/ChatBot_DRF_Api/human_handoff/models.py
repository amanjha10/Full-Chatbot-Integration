# human_handoff/models.py
from django.db import models
from django.conf import settings
from admin_dashboard.models import Agent
from chatbot.models import ChatSession, UserProfile
import uuid

class HandoffSession(models.Model):
    """
    Model for managing handoff sessions between chatbot and human agents
    This is the main model used by the agent dashboard
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    session_id = models.CharField(max_length=100, unique=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='handoff_sessions')
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='handoff_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    initial_message = models.TextField(blank=True, null=True)
    escalation_reason = models.TextField(blank=True, null=True)
    company_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['created_at']  # FIFO order for pending sessions

    def __str__(self):
        return f"Handoff {self.session_id} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.session_id:
            self.session_id = f"handoff_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

class HumanHandoffSession(models.Model):
    """Tracks when a chat session is escalated to human agents"""
    chat_session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='handoff')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_sessions')
    escalated_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    escalation_reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    
    @property
    def company_id(self):
        """Get company_id from the associated chat session"""
        return self.chat_session.company_id

    @property
    def status(self):
        """Determine status based on existing fields"""
        if self.resolved_at:
            return 'resolved'
        elif self.agent:
            return 'assigned'
        else:
            return 'pending'

    def __str__(self):
        return f"Handoff {self.chat_session.session_id} -> {self.agent.name if self.agent else 'Unassigned'}"

class AgentActivity(models.Model):
    """Track agent activities and status changes"""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=[
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('status_change', 'Status Change'),
        ('session_assign', 'Session Assigned'),
        ('session_resolve', 'Session Resolved'),
        ('message_sent', 'Message Sent')
    ])
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.agent.name} - {self.activity_type} at {self.timestamp}"

class SessionTransfer(models.Model):
    """Track session transfers between agents"""
    handoff_session = models.ForeignKey(HumanHandoffSession, on_delete=models.CASCADE, related_name='transfers')
    from_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name='transfers_from')
    to_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name='transfers_to')
    reason = models.TextField()
    transferred_at = models.DateTimeField(auto_now_add=True)
    transferred_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Transfer: {self.from_agent} -> {self.to_agent}"

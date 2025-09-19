from django.contrib import admin
from .models import HumanHandoffSession, AgentActivity, SessionTransfer


@admin.register(HumanHandoffSession)
class HumanHandoffSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_session', 'agent', 'priority', 'escalated_at']
    list_filter = ['priority', 'escalated_at', 'resolved_at']
    search_fields = [
        'chat_session__session_id', 
        'agent__name',
        'escalation_reason'
    ]
    readonly_fields = ['escalated_at', 'resolved_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'chat_session', 'agent'
        )


@admin.register(AgentActivity)
class AgentActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = [
        'agent__name',
        'description'
    ]
    readonly_fields = ['timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'agent'
        )


@admin.register(SessionTransfer)
class SessionTransferAdmin(admin.ModelAdmin):
    list_display = ['id', 'handoff_session', 'from_agent', 'to_agent', 'transferred_at']
    list_filter = ['transferred_at']
    search_fields = [
        'handoff_session__chat_session__session_id',
        'from_agent__name',
        'to_agent__name',
        'reason'
    ]
    readonly_fields = ['transferred_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'handoff_session__chat_session',
            'from_agent',
            'to_agent',
            'transferred_by'
        )

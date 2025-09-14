from django.contrib import admin
from .models import Agent, AgentSession


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Agent admin interface."""

    list_display = ('name', 'email', 'phone', 'specialization', 'status', 'formatted_last_active', 'created_by', 'is_active', 'created_at')
    list_filter = ('status', 'is_active', 'is_first_login', 'created_at', 'specialization')
    search_fields = ('name', 'email', 'phone', 'specialization')
    readonly_fields = ('created_at', 'updated_at', 'formatted_last_active')
    raw_id_fields = ('user', 'created_by')

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'email', 'phone', 'specialization')
        }),
        ('Status & Activity', {
            'fields': ('status', 'last_active', 'formatted_last_active', 'is_first_login')
        }),
        ('Management', {
            'fields': ('created_by', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'created_by')


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    """Agent session admin interface."""

    list_display = ('agent', 'login_time', 'logout_time', 'session_duration', 'ip_address')
    list_filter = ('login_time', 'logout_time')
    search_fields = ('agent__name', 'agent__email', 'ip_address')
    readonly_fields = ('login_time', 'logout_time', 'session_duration')
    raw_id_fields = ('agent',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agent')

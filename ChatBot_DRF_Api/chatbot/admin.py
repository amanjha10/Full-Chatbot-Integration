from django.contrib import admin
from .models import ChatSession, UserProfile, ChatMessage, UploadedFile, RAGDocument, ChatbotConfiguration


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['persistent_user_id', 'name', 'phone', 'email', 'created_at']
    list_filter = ['created_at', 'last_used']
    search_fields = ['persistent_user_id', 'name', 'phone', 'email']
    readonly_fields = ['persistent_user_id', 'created_at', 'last_used']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user_profile', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['session_id', 'user_profile__name', 'user_profile__phone']
    readonly_fields = ['session_id', 'created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content', 'session__session_id']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'original_name', 'file_type', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['original_name', 'session__session_id']
    readonly_fields = ['uploaded_at']


@admin.register(RAGDocument)
class RAGDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'section', 'question_preview', 'document', 'is_active', 'created_at']
    list_filter = ['section', 'document', 'is_active', 'created_at']
    search_fields = ['question', 'answer', 'section']
    readonly_fields = ['created_at']
    
    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question Preview'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger vector embedding update if needed
        # This could be expanded to update embeddings when content changes


@admin.register(ChatbotConfiguration)
class ChatbotConfigurationAdmin(admin.ModelAdmin):
    list_display = ['company_id', 'company_name', 'position', 'primary_color', 'secondary_color', 'updated_at']
    list_filter = ['position', 'enable_file_upload', 'enable_voice_messages', 'created_at']
    search_fields = ['company_id', 'company_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Company Information', {
            'fields': ('company_id', 'company_name', 'company_logo_url')
        }),
        ('Appearance', {
            'fields': ('primary_color', 'secondary_color', 'position')
        }),
        ('Iframe Settings', {
            'fields': ('iframe_width', 'iframe_height')
        }),
        ('Messages', {
            'fields': ('welcome_message',)
        }),
        ('Features', {
            'fields': ('enable_file_upload', 'enable_voice_messages', 'enable_typing_indicator')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

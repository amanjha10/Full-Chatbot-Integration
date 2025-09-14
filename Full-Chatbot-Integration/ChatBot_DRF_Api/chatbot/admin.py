from django.contrib import admin
from django.utils import timezone
from .models import (
    ChatSession, UserProfile, ChatMessage, UploadedFile, RAGDocument,
    ChatbotConfiguration, Plan, PlanFeature, CompanyPlan, PlanUpgradeRequest
)


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


# Plan Management Admin Classes

class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1
    fields = ['text', 'included', 'sort_order']
    ordering = ['sort_order']


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'max_agents', 'subtitle', 'sort_order', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subtitle']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['sort_order']
    inlines = [PlanFeatureInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'icon', 'subtitle', 'price', 'max_agents', 'sort_order', 'is_active')
        }),
        ('Styling', {
            'fields': ('gradient', 'text_color', 'border_color', 'button_color', 'shine_color')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CompanyPlan)
class CompanyPlanAdmin(admin.ModelAdmin):
    list_display = ['company_id', 'current_plan', 'requested_plan', 'is_active', 'updated_at']
    list_filter = ['current_plan', 'is_active', 'created_at']
    search_fields = ['company_id']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Company Information', {
            'fields': ('company_id', 'is_active')
        }),
        ('Plan Information', {
            'fields': ('current_plan', 'requested_plan', 'plan_start_date', 'plan_end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PlanUpgradeRequest)
class PlanUpgradeRequestAdmin(admin.ModelAdmin):
    list_display = ['company_id', 'current_plan', 'requested_plan', 'status', 'requested_by', 'request_date']
    list_filter = ['status', 'current_plan', 'requested_plan', 'request_date']
    search_fields = ['company_id', 'requested_by', 'reason']
    readonly_fields = ['request_date', 'response_date']
    ordering = ['-request_date']

    fieldsets = (
        ('Request Information', {
            'fields': ('company_id', 'requested_by', 'reason')
        }),
        ('Plan Details', {
            'fields': ('current_plan', 'requested_plan', 'status')
        }),
        ('Admin Actions', {
            'fields': ('approved_by', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('request_date', 'response_date'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        """Approve selected upgrade requests"""
        from .models import CompanyPlan

        approved_count = 0
        for upgrade_request in queryset.filter(status='pending'):
            try:
                # Update the company plan
                company_plan = CompanyPlan.objects.get(company_id=upgrade_request.company_id)
                company_plan.current_plan = upgrade_request.requested_plan
                company_plan.requested_plan = None
                company_plan.save()

                # Update the request
                upgrade_request.status = 'approved'
                upgrade_request.approved_by = request.user.username
                upgrade_request.response_date = timezone.now()
                upgrade_request.save()

                approved_count += 1
            except Exception as e:
                self.message_user(request, f"Error approving request for {upgrade_request.company_id}: {str(e)}", level='ERROR')

        if approved_count > 0:
            self.message_user(request, f"Successfully approved {approved_count} upgrade request(s).")

    approve_requests.short_description = "Approve selected upgrade requests"

    def reject_requests(self, request, queryset):
        """Reject selected upgrade requests"""
        from .models import CompanyPlan

        rejected_count = 0
        for upgrade_request in queryset.filter(status='pending'):
            try:
                # Update the company plan
                company_plan = CompanyPlan.objects.get(company_id=upgrade_request.company_id)
                company_plan.requested_plan = None
                company_plan.save()

                # Update the request
                upgrade_request.status = 'rejected'
                upgrade_request.approved_by = request.user.username
                upgrade_request.response_date = timezone.now()
                upgrade_request.save()

                rejected_count += 1
            except Exception as e:
                self.message_user(request, f"Error rejecting request for {upgrade_request.company_id}: {str(e)}", level='ERROR')

        if rejected_count > 0:
            self.message_user(request, f"Successfully rejected {rejected_count} upgrade request(s).")

    reject_requests.short_description = "Reject selected upgrade requests"

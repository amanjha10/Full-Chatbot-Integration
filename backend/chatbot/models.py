# chatbot/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class ChatSession(models.Model):
    SESSION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('escalated', 'Escalated to Human'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PROFILE_COLLECTION_STATES = [
        ('name', 'Collecting Name'),
        ('country_code', 'Collecting Country Code'),
        ('phone', 'Collecting Phone'),
        ('email', 'Collecting Email'),
        ('address', 'Collecting Address'),
        ('complete', 'Profile Complete'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    company_id = models.CharField(max_length=20, default='DEFAULT_COMPANY', help_text="Company ID for multi-tenant isolation")
    user_profile = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='active')
    profile_completed = models.BooleanField(default=False)
    profile_collection_state = models.CharField(max_length=20, choices=PROFILE_COLLECTION_STATES, default='name')
    temp_profile_data = models.JSONField(default=dict, blank=True)  # Store temporary profile data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.session_id} - {self.status}"

class UserProfile(models.Model):
    session_id = models.CharField(max_length=100)
    company_id = models.CharField(max_length=20, default='DEFAULT_COMPANY', help_text="Company ID for multi-tenant isolation")
    persistent_user_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)  # Added address field
    country_code = models.CharField(max_length=10, default='+977')
    is_favorite = models.BooleanField(default=False, help_text="Mark as favorite to prevent deletion during clear operations")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"

    def update_last_used(self):
        """Update last_used timestamp manually"""
        from django.utils import timezone
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])

class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('agent', 'Agent'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField(blank=True, null=True)  # Allow empty content for file-only messages
    attachments = models.ManyToManyField('UploadedFile', blank=True, related_name='chat_messages')
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        attachment_count = self.attachments.count()
        content_preview = self.content[:50] if self.content else f"[{attachment_count} attachments]"
        return f"{self.message_type}: {content_preview}"

class UploadedFile(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    company_id = models.CharField(max_length=20, default='DEFAULT_COMPANY', help_text="Company ID for multi-tenant isolation")
    original_name = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    filepath = models.CharField(max_length=500)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=10)
    message_context = models.TextField(blank=True, null=True)
    uploaded_by_agent = models.BooleanField(default=False, help_text="True if uploaded by agent, False if uploaded by user")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def get_file_url(self):
        """Get the URL to access the uploaded file"""
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.filepath}"
    
    def __str__(self):
        return f"{self.original_name} - {self.file_type}"

def chat_upload_path(instance, filename):
    """Generate upload path for chat files"""
    from .utils.storage import generate_secure_filename

    # Use secure filename generation
    return generate_secure_filename(filename, instance.company_id, instance.session_id)


class ChatFile(models.Model):
    """Model for file sharing between chatbot and agent"""
    UPLOADER_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
    ]

    company_id = models.CharField(max_length=64, db_index=True)
    session_id = models.CharField(max_length=64, db_index=True)
    uploader = models.CharField(max_length=16, choices=UPLOADER_CHOICES, default='user')
    file = models.FileField(upload_to=chat_upload_path)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=127)
    size = models.BigIntegerField()
    thumbnail = models.URLField(blank=True, null=True)  # Optional for images
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional fields for additional context
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_id', 'session_id']),
            models.Index(fields=['created_at']),
        ]

    def get_file_url(self):
        """Get the URL to access the uploaded file"""
        from django.conf import settings
        if self.file:
            return f"{settings.MEDIA_URL}{self.file.name}"
        return None

    def __str__(self):
        return f"{self.original_name} ({self.uploader}) - {self.session_id[:8]}"


class RAGDocument(models.Model):
    """Model to store RAG documents and FAQ data"""
    chunk_id = models.CharField(max_length=100, unique=True)
    question = models.TextField()
    answer = models.TextField()
    section = models.CharField(max_length=100)
    document = models.CharField(max_length=200)
    page = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.section}: {self.question[:50]}"


class ChatbotConfiguration(models.Model):
    """Model to store chatbot customization settings for each company"""

    POSITION_CHOICES = [
        ('bottom-right', 'Bottom Right'),
        ('bottom-left', 'Bottom Left'),
        ('top-right', 'Top Right'),
        ('top-left', 'Top Left'),
    ]

    company_id = models.CharField(max_length=20, unique=True, help_text="Company ID for chatbot configuration")

    # Appearance settings
    primary_color = models.CharField(max_length=7, default='#f7941d', help_text="Primary color for chatbot (hex format)")
    secondary_color = models.CharField(max_length=7, default='#652d90', help_text="Secondary color for chatbot (hex format)")

    # Position settings
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='bottom-right')

    # Iframe settings
    iframe_width = models.IntegerField(default=400, help_text="Width of chatbot iframe in pixels")
    iframe_height = models.IntegerField(default=600, help_text="Height of chatbot iframe in pixels")

    # Welcome message
    welcome_message = models.TextField(default="Hello! How can I help you today?", help_text="Initial welcome message")

    # Company branding
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_logo_url = models.URLField(blank=True, null=True)

    # Feature toggles
    enable_file_upload = models.BooleanField(default=True)
    enable_voice_messages = models.BooleanField(default=False)
    enable_typing_indicator = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chatbot Config for {self.company_id}"

    @classmethod
    def get_or_create_for_company(cls, company_id):
        """Get or create configuration for a company"""
        config, created = cls.objects.get_or_create(
            company_id=company_id,
            defaults={
                'primary_color': '#f7941d',
                'secondary_color': '#652d90',
                'position': 'bottom-right',
                'welcome_message': 'Hello! How can I help you today?'
            }
        )
        return config


class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=10, default="📦")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtitle = models.CharField(max_length=100)  # This is "for_whom"
    max_agents = models.CharField(max_length=20)  # Can be number or "Unlimited"
    features_line = models.CharField(max_length=200, default="AI-powered Chatbot")  # One-line features description
    gradient = models.CharField(max_length=100)
    text_color = models.CharField(max_length=50)
    border_color = models.CharField(max_length=50)
    button_color = models.CharField(max_length=50)
    shine_color = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} Plan"


class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='features')
    text = models.CharField(max_length=200)
    included = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'text']

    def __str__(self):
        return f"{self.plan.name}: {self.text}"


class CompanyPlan(models.Model):
    company_id = models.CharField(max_length=20, unique=True)
    current_plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='current_companies')
    requested_plan = models.ForeignKey(Plan, on_delete=models.CASCADE, null=True, blank=True, related_name='requested_companies')
    plan_start_date = models.DateTimeField(auto_now_add=True)
    plan_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Custom plan fields
    custom_max_agents = models.IntegerField(null=True, blank=True, help_text="Custom max agents for Custom plan")
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Custom price for Custom plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_id} - {self.current_plan.name}"


class PlanUpgradeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    company_id = models.CharField(max_length=20)
    current_plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='upgrade_requests_from')
    requested_plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='upgrade_requests_to')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.CharField(max_length=100, blank=True)  # User who requested
    approved_by = models.CharField(max_length=100, blank=True)  # Admin who approved/rejected
    request_date = models.DateTimeField(auto_now_add=True)
    response_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.company_id}: {self.current_plan.name} → {self.requested_plan.name} ({self.status})"

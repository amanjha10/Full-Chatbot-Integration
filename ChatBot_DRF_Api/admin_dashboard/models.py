from django.db import models
from django.utils import timezone
from authentication.models import User


class Agent(models.Model):
    """Agent model for managing agents in admin dashboard."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),  # Not completed first login
        ('AVAILABLE', 'Available'),  # Online and ready
        ('BUSY', 'Busy'),  # Handling chat sessions
        ('OFFLINE', 'Offline'),  # Not connected
    ]

    # Basic Information
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        limit_choices_to={'role': User.Role.AGENT}
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    specialization = models.CharField(max_length=200)
    company_id = models.CharField(max_length=20, null=True, blank=True, help_text="Company ID of the admin who created this agent")

    # Status and Activity Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    last_active = models.DateTimeField(null=True, blank=True)
    is_first_login = models.BooleanField(default=True)

    # Admin who created this agent
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_agents',
        limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.SUPERADMIN]}
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.status}"

    def get_current_status(self):
        """Get the current status based on first login completion."""
        if self.is_first_login:
            return 'PENDING'
        return self.status

    def update_status(self, new_status):
        """Update agent status and last_active timestamp."""
        if not self.is_first_login:  # Only update status if first login is complete
            self.status = new_status
        if new_status == 'OFFLINE':
            self.last_active = timezone.now()
        self.save()

    def set_online(self):
        """Set agent status to AVAILABLE when they login."""
        if not self.is_first_login:
            self.update_status('AVAILABLE')

    def set_busy(self):
        """Set agent status to BUSY when they start chatting."""
        if not self.is_first_login:
            self.update_status('BUSY')

    def set_offline(self):
        """Set agent status to OFFLINE when they logout."""
        if not self.is_first_login:
            self.update_status('OFFLINE')

    def complete_first_login(self):
        """Mark first login as complete and set status to OFFLINE."""
        self.is_first_login = False
        self.status = 'OFFLINE'
        self.save()

    @property
    def formatted_last_active(self):
        """Return formatted last active time."""
        if self.last_active:
            return self.last_active.strftime("%d/%m/%Y %H:%M")
        return "Never"

    @property
    def formatted_created_at(self):
        """Return formatted created time."""
        if self.created_at:
            return self.created_at.strftime("%d/%m/%Y %H:%M")
        return "Unknown"


class AgentSession(models.Model):
    """Track agent login/logout sessions for analytics."""

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='sessions')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.agent.name} - {self.login_time.strftime('%d/%m/%Y %H:%M')}"

    def end_session(self):
        """End the session and calculate duration."""
        if not self.logout_time:
            self.logout_time = timezone.now()
            self.session_duration = self.logout_time - self.login_time
            self.save()

            # Update agent's last active time
            self.agent.set_offline()


class PlanUpgradeRequest(models.Model):
    """Model for tracking plan upgrade requests from admin to superadmin."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DECLINED', 'Declined'),
    ]
    
    company_id = models.CharField(max_length=20, help_text="Company ID requesting the upgrade")
    company_name = models.CharField(max_length=200, help_text="Company name for display")
    current_plan = models.CharField(max_length=50, help_text="Current plan name")
    requested_plan = models.CharField(max_length=50, help_text="Requested plan name")
    reason = models.TextField(blank=True, null=True, help_text="Reason for upgrade request")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Request tracking
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='upgrade_requests_made',
        help_text="Admin user who made the request"
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    
    # Approval tracking
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='upgrade_requests_reviewed',
        help_text="Superadmin user who reviewed the request"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True, help_text="Notes from reviewer")
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = "Plan Upgrade Request"
        verbose_name_plural = "Plan Upgrade Requests"
    
    def __str__(self):
        return f"{self.company_name} - {self.current_plan} to {self.requested_plan} ({self.status})"

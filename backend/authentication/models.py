from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Custom User model with role-based access control."""

    class Role(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', 'Super Admin'
        ADMIN = 'ADMIN', 'Admin'
        AGENT = 'AGENT', 'Agent'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AGENT,
        help_text="User role for access control"
    )

    # Additional profile fields
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Full name for company ID generation")
    address = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    generated_password = models.CharField(max_length=50, blank=True, null=True)  # Store generated password
    company_id = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Unique company identifier for chatbot integration")
    is_first_login = models.BooleanField(default=True, help_text="True if admin needs to set their own password on first login")

    @property
    def current_plan_assignment(self):
        """Get the current active plan assignment."""
        return self.plan_assignments.filter(status='active').first()

    @property
    def agent_limit(self):
        """Get the current agent limit based on active plan."""
        assignment = self.current_plan_assignment
        return assignment.plan.max_agents if assignment else 0
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    def complete_first_login(self):
        """Mark first login as complete for admin users."""
        if self.role == self.Role.ADMIN:
            self.is_first_login = False
            self.save()


class Plan(models.Model):
    """Plan model for subscription plans."""

    PLAN_TYPES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
        ('custom', 'Custom'),
        ('basic', 'Basic'),  # Legacy support
        ('pro', 'Pro'),      # Legacy support
        ('premium', 'Premium'),  # Legacy support
    ]

    plan_name = models.CharField(max_length=50, choices=PLAN_TYPES)
    max_agents = models.PositiveIntegerField(help_text="Maximum number of agents allowed")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    company_name = models.CharField(max_length=100, default="Default Company", help_text="Company this plan is assigned to")
    expiry_date = models.DateField(null=True, blank=True, help_text="Plan expiry date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # For custom plans
    is_custom = models.BooleanField(default=False, help_text="Whether this is a custom plan")
    custom_features = models.JSONField(null=True, blank=True, help_text="Additional features for custom plans")

    class Meta:
        ordering = ['plan_name', 'price']

    def __str__(self):
        return f"{self.get_plan_name_display()} - {self.max_agents} agents (${self.price}) - {self.company_name}"

    @property
    def plan_name_display(self):
        """Get display name for the plan."""
        return self.get_plan_name_display()

    @classmethod
    def get_predefined_plans(cls):
        """Get the predefined plan configurations."""
        return {
            'bronze': {'price': 2000, 'max_agents': 2},
            'silver': {'price': 4000, 'max_agents': 4},
            'gold': {'price': 6000, 'max_agents': 6},
            'platinum': {'price': 8000, 'max_agents': 8},
            'diamond': {'price': 10000, 'max_agents': 10},
        }

    def get_max_agents_for_plan(self):
        """Get the maximum number of agents allowed for this plan."""
        if self.is_custom:
            return self.max_agents
        
        predefined = self.get_predefined_plans()
        plan_config = predefined.get(self.plan_name, {})
        return plan_config.get('max_agents', self.max_agents)


class UserPlanAssignment(models.Model):
    """Combined table for tracking user plan assignments with subscription management."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('upgraded', 'Upgraded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_assignments')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='user_assignments')
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Track subscription changes
    previous_assignment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Reason for status change")

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-set expiry date (1 year from start date if not provided)
        if not self.expiry_date:
            self.expiry_date = self.start_date + timedelta(days=365)

        # Auto-update status based on expiry
        if self.status == 'active' and timezone.now() > self.expiry_date:
            self.status = 'expired'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan.get_plan_name_display()} ({self.status})"

    @property
    def is_expired(self):
        return timezone.now() > self.expiry_date or self.status in ['expired', 'cancelled']

    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        return (self.expiry_date - timezone.now()).days

    def cancel_subscription(self, reason=""):
        """Cancel the current subscription."""
        self.status = 'cancelled'
        self.notes = reason
        self.save()

    def renew_subscription(self, new_expiry_date=None):
        """Renew the subscription."""
        if not new_expiry_date:
            new_expiry_date = timezone.now() + timedelta(days=365)

        # Create new assignment for renewal
        new_assignment = UserPlanAssignment.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            expiry_date=new_expiry_date,
            previous_assignment=self,
            notes="Subscription renewed"
        )

        # Mark current as upgraded (to maintain history)
        self.status = 'upgraded'
        self.notes = f"Renewed with assignment ID: {new_assignment.id}"
        self.save()

        return new_assignment

    def upgrade_plan(self, new_plan, reason=""):
        """Upgrade to a different plan."""
        # Create new assignment with new plan
        new_assignment = UserPlanAssignment.objects.create(
            user=self.user,
            plan=new_plan,
            start_date=timezone.now(),
            expiry_date=self.expiry_date,  # Keep same expiry date
            previous_assignment=self,
            notes=f"Upgraded from {self.plan.get_plan_name_display()} to {new_plan.get_plan_name_display()}. {reason}"
        )

        # Mark current as upgraded
        self.status = 'upgraded'
        self.notes = f"Upgraded to assignment ID: {new_assignment.id}"
        self.save()

        return new_assignment




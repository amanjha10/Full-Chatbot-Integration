from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Plan, UserPlanAssignment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role field and additional profile fields."""

    list_display = ('username', 'email', 'role', 'phone_number', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
        ('Profile Information', {'fields': ('address', 'contact_person', 'contact_number', 'phone_number', 'generated_password')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
        ('Profile Information', {'fields': ('address', 'contact_person', 'contact_number', 'phone_number')}),
    )





@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Plan admin interface."""

    list_display = ('plan_name', 'max_agents', 'price', 'is_active', 'created_at')
    list_filter = ('plan_name', 'is_active', 'created_at')
    search_fields = ('plan_name',)
    list_editable = ('is_active',)

    fieldsets = (
        (None, {'fields': ('plan_name', 'max_agents', 'price')}),
        ('Status', {'fields': ('is_active',)}),
    )


@admin.register(UserPlanAssignment)
class UserPlanAssignmentAdmin(admin.ModelAdmin):
    """UserPlanAssignment admin interface."""

    list_display = ('user', 'plan', 'start_date', 'expiry_date', 'status', 'days_remaining', 'is_expired')
    list_filter = ('status', 'start_date', 'expiry_date', 'plan__plan_name')
    search_fields = ('user__username', 'user__email', 'plan__plan_name')
    raw_id_fields = ('user', 'plan')
    date_hierarchy = 'start_date'

    fieldsets = (
        (None, {'fields': ('user', 'plan')}),
        ('Dates', {'fields': ('start_date', 'expiry_date')}),
        ('Status', {'fields': ('status', 'notes')}),
    )

    readonly_fields = ('days_remaining', 'is_expired')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')

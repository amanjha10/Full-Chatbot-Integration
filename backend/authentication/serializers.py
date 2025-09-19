import string
import secrets
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, Plan, UserPlanAssignment


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with email/username and password."""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Try to authenticate with username first, then email
            user = authenticate(username=username, password=password)
            if not user:
                # Try with email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user and user.is_active:
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Invalid credentials or inactive account.')
        else:
            raise serializers.ValidationError('Must include username/email and password.')


class AdminCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new Admin users by SuperAdmin."""

    plan_id = serializers.IntegerField(write_only=True, help_text="Plan ID to assign")

    class Meta:
        model = User
        fields = ('name', 'email', 'address', 'contact_person', 'contact_number', 'phone_number', 'plan_id')
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'address': {'required': False},
            'contact_person': {'required': False},
            'contact_number': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_plan_id(self, value):
        """Validate that the plan exists and is active."""
        try:
            plan = Plan.objects.get(id=value, is_active=True)
            return plan
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan ID or plan is not active.")

    def generate_password(self):
        """Generate a random 8-character alphanumeric password."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    def generate_company_id(self, name):
        """Generate unique company ID from name."""
        # Extract first 3 characters from name and convert to uppercase
        # Remove spaces and take first 3 alphabetic characters
        clean_name = ''.join(char for char in name if char.isalpha())
        prefix = clean_name[:3].upper() if len(clean_name) >= 3 else clean_name.upper().ljust(3, 'X')
        
        # Find the next available number
        counter = 1
        while True:
            company_id = f"{prefix}{counter:03d}"
            if not User.objects.filter(company_id=company_id).exists():
                return company_id
            counter += 1

    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create new Admin user with generated password and plan assignment."""
        # Generate random password
        password = self.generate_password()

        # Get plan from validated plan_id
        plan = validated_data.pop('plan_id')

        # Get name and email
        name = validated_data['name']
        email = validated_data['email']
        
        # Create username from email (before @ symbol)
        username = email.split('@')[0]

        # Generate unique company ID from name
        company_id = self.generate_company_id(name)

        # Extract first and last name from full name
        name_parts = name.strip().split()
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Admin'

        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user without plan reference
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.ADMIN,
            name=name,  # Store full name
            address=validated_data.get('address', ''),
            contact_person=validated_data.get('contact_person', ''),
            contact_number=validated_data.get('contact_number', ''),
            phone_number=validated_data.get('phone_number', ''),
            generated_password=password,  # Store generated password
            company_id=company_id,  # Store unique company ID
            is_first_login=True  # Ensure first login flag is set
        )

        # Create plan assignment
        UserPlanAssignment.objects.create(
            user=user,
            plan=plan,
            notes="Initial plan assignment"
        )

        # Store password for response
        user._generated_password = password
        user._assigned_plan = plan
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""

    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'name', 'role', 'address', 'contact_person', 'contact_number', 'phone_number', 'company_id', 'current_plan', 'generated_password', 'date_joined')
        read_only_fields = ('id', 'company_id', 'date_joined')

    def get_current_plan(self, obj):
        # First try to get active assignment
        assignment = obj.current_plan_assignment

        # If no active assignment (e.g., cancelled subscription), get the most recent one
        if not assignment:
            assignment = obj.plan_assignments.order_by('-created_at').first()

        if assignment:
            return {
                'id': assignment.plan.id,
                'name': assignment.plan.get_plan_name_display(),
                'max_agents': assignment.plan.max_agents,
                'price': str(assignment.plan.price),
                'status': assignment.status  # Include status to know if it's cancelled
            }
        return None


class AdminListSerializer(serializers.ModelSerializer):
    """Serializer for listing admin users with complete information."""

    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'address', 'contact_person', 'contact_number', 'phone_number', 'company_id', 'current_plan', 'generated_password', 'date_joined', 'is_active')
        read_only_fields = ('id', 'company_id', 'generated_password', 'date_joined')

    def get_current_plan(self, obj):
        assignment = obj.current_plan_assignment
        if assignment:
            return {
                'assignment_id': assignment.id,
                'plan_id': assignment.plan.id,
                'plan_name': assignment.plan.get_plan_name_display(),
                'max_agents': assignment.plan.max_agents,
                'price': str(assignment.plan.price),
                'start_date': assignment.start_date,
                'expiry_date': assignment.expiry_date,
                'status': assignment.status,
                'days_remaining': assignment.days_remaining
            }
        return None


class AdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating admin user information."""

    class Meta:
        model = User
        fields = ('name', 'email', 'first_name', 'last_name', 'address', 'contact_person', 'contact_number', 'phone_number')
        extra_kwargs = {
            'name': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'address': {'required': False},
            'contact_person': {'required': False},
            'contact_number': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_email(self, value):
        # Check if email is already taken by another user
        if value and User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class AdminPlanChangeSerializer(serializers.Serializer):
    """Serializer for changing admin's plan."""

    new_plan_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=500, required=False, default="Plan changed by SuperAdmin")

    def validate_new_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
            return plan
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan ID or plan is not active.")


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model."""

    plan_name_display = serializers.CharField(source='get_plan_name_display', read_only=True)

    class Meta:
        model = Plan
        fields = ('id', 'plan_name', 'plan_name_display', 'max_agents', 'price', 'company_name', 'expiry_date', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value


class PlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new plans."""

    class Meta:
        model = Plan
        fields = ('plan_name', 'max_agents', 'price', 'company_name', 'expiry_date')
        extra_kwargs = {
            'plan_name': {'required': True},
            'max_agents': {'required': True},
            'price': {'required': True},
            'company_name': {'required': True},
            'expiry_date': {'required': False},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_max_agents(self, value):
        if value <= 0:
            raise serializers.ValidationError("Max agents must be greater than 0.")
        return value


class UserPlanAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for UserPlanAssignment model."""

    user_details = serializers.SerializerMethodField()
    plan_details = serializers.SerializerMethodField()
    days_remaining = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserPlanAssignment
        fields = ('id', 'user', 'user_details', 'plan', 'plan_details', 'start_date', 'expiry_date', 'status', 'status_display', 'days_remaining', 'is_expired', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'role': obj.user.role
        }

    def get_plan_details(self, obj):
        return {
            'id': obj.plan.id,
            'plan_name': obj.plan.get_plan_name_display(),
            'max_agents': obj.plan.max_agents,
            'price': str(obj.plan.price)
        }





class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response with user role."""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    
    @classmethod
    def get_token_response(cls, user):
        """Generate token response for authenticated user."""
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }


class CompanySubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for company subscription reports."""

    company_name = serializers.CharField(source='user.name')
    company_id = serializers.CharField(source='user.company_id')
    user_id = serializers.IntegerField(source='user.id')  # Add user ID for cancellation
    plan_name = serializers.CharField(source='plan.plan_name_display')
    price = serializers.DecimalField(source='plan.price', max_digits=10, decimal_places=2)
    max_agents = serializers.IntegerField(source='plan.max_agents')
    plan_history = serializers.SerializerMethodField()

    class Meta:
        model = UserPlanAssignment
        fields = [
            'id', 'company_name', 'company_id', 'user_id', 'plan_name', 'price', 'max_agents',
            'created_at', 'expiry_date', 'status', 'plan_history'
        ]
    
    def get_plan_history(self, obj):
        """Get plan history for the company."""
        # Get all assignments for this user (including previous ones)
        assignments = UserPlanAssignment.objects.filter(
            user=obj.user
        ).exclude(id=obj.id).order_by('-created_at')
        
        history = []
        for assignment in assignments:
            history.append({
                'plan_name': assignment.plan.plan_name_display,
                'price': float(assignment.plan.price),
                'start_date': assignment.start_date.isoformat(),
                'end_date': assignment.expiry_date.isoformat(),
                'status': assignment.status
            })
        
        return history


class EnhancedAdminCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating companies with new plan system."""

    plan_id = serializers.CharField(write_only=True, help_text="Plan ID or plan type")
    custom_max_agents = serializers.IntegerField(required=False, allow_null=True)
    custom_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, help_text="Plan expiry date")

    class Meta:
        model = User
        fields = (
            'name', 'email', 'address', 'contact_person', 
            'contact_number', 'phone_number', 'plan_id',
            'custom_max_agents', 'custom_price', 'expiry_date'
        )
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'address': {'required': False},
            'contact_person': {'required': False},
            'contact_number': {'required': False},
            'phone_number': {'required': False},
        }

    def validate(self, attrs):
        """Validate plan selection and custom fields."""
        plan_id = attrs.get('plan_id')
        custom_max_agents = attrs.get('custom_max_agents')
        custom_price = attrs.get('custom_price')
        
        # If custom plan is selected, require custom fields
        if plan_id == 'custom':
            if not custom_max_agents or not custom_price:
                raise serializers.ValidationError(
                    "Custom max agents and price are required for custom plans."
                )
        else:
            # For predefined plans, check if it's a valid plan type or ID
            predefined_plans = Plan.get_predefined_plans()
            if plan_id not in predefined_plans:
                # Try to get by ID for legacy support
                try:
                    Plan.objects.get(id=int(plan_id), is_active=True)
                except (ValueError, Plan.DoesNotExist):
                    raise serializers.ValidationError("Invalid plan selection.")
        
        return attrs

    def generate_password(self):
        """Generate a random 8-character alphanumeric password."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    def generate_company_id(self, name):
        """Generate unique company ID from name."""
        # Extract first 3 characters from name and convert to uppercase
        clean_name = ''.join(char for char in name if char.isalpha())
        prefix = clean_name[:3].upper() if len(clean_name) >= 3 else clean_name.upper().ljust(3, 'X')
        
        # Find the next available number
        counter = 1
        while True:
            company_id = f"{prefix}{counter:03d}"
            if not User.objects.filter(company_id=company_id).exists():
                return company_id
            counter += 1

    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create new company with plan assignment."""
        from django.db import transaction
        from datetime import datetime, timedelta
        
        # Extract plan-related data
        plan_id = validated_data.pop('plan_id')
        custom_max_agents = validated_data.pop('custom_max_agents', None)
        custom_price = validated_data.pop('custom_price', None)
        
        # Generate password and company ID
        password = self.generate_password()
        name = validated_data['name']
        company_id = self.generate_company_id(name)
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=company_id.lower(),
                email=validated_data['email'],
                password=password,
                role=User.Role.ADMIN,
                name=name,
                address=validated_data.get('address', ''),
                contact_person=validated_data.get('contact_person', ''),
                contact_number=validated_data.get('contact_number', ''),
                phone_number=validated_data.get('phone_number', ''),
                company_id=company_id,
                generated_password=password
            )
            
            # Create or get plan
            if plan_id == 'custom':
                # Create custom plan
                plan = Plan.objects.create(
                    plan_name='custom',
                    max_agents=custom_max_agents,
                    price=custom_price,
                    company_name=name,
                    is_custom=True,
                    expiry_date=datetime.now().date() + timedelta(days=365)
                )
            else:
                # Handle predefined plans
                predefined_plans = Plan.get_predefined_plans()
                if plan_id in predefined_plans:
                    plan_config = predefined_plans[plan_id]
                    plan = Plan.objects.create(
                        plan_name=plan_id,
                        max_agents=plan_config['max_agents'],
                        price=plan_config['price'],
                        company_name=name,
                        expiry_date=datetime.now().date() + timedelta(days=365)
                    )
                else:
                    # Legacy: get existing plan by ID
                    plan = Plan.objects.get(id=int(plan_id), is_active=True)
            
            # Create plan assignment
            UserPlanAssignment.objects.create(
                user=user,
                plan=plan,
                start_date=timezone.now(),
                expiry_date=timezone.now() + timedelta(days=365),
                status='active'
            )
        
        return user


class AdminPasswordResetSerializer(serializers.Serializer):
    """Serializer for resetting admin password by SuperAdmin."""

    admin_id = serializers.IntegerField()

    def validate_admin_id(self, value):
        try:
            admin = User.objects.get(id=value, role=User.Role.ADMIN, is_active=True)
            self.context['admin'] = admin
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Admin not found or inactive.")


class AdminFirstLoginSerializer(serializers.Serializer):
    """Serializer for admin's first login password setup."""

    email = serializers.EmailField()
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")

        # Authenticate with current password
        try:
            user = User.objects.get(email=attrs['email'], role=User.Role.ADMIN)
            if not authenticate(username=user.username, password=attrs['current_password']):
                raise serializers.ValidationError("Current password is incorrect.")

            # Check if it's first login
            if not user.is_first_login:
                raise serializers.ValidationError("Password has already been set.")

            attrs['user'] = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError("Admin not found.")

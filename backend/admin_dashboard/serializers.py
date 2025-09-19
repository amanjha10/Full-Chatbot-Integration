import string
import secrets
from rest_framework import serializers
from django.contrib.auth import authenticate
from authentication.models import User
from .models import Agent, AgentSession, PlanUpgradeRequest


class AgentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating agents from admin dashboard."""
    
    class Meta:
        model = Agent
        fields = ('name', 'phone', 'email', 'specialization')
    
    def validate(self, attrs):
        # Ensure the admin has a company_id
        admin_user = self.context['request'].user
        if not admin_user.company_id:
            raise serializers.ValidationError("Admin user must have a company_id to create agents.")
        return attrs
    
    def validate_email(self, value):
        # Check if email is already taken
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        if Agent.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use by another agent.")
        return value
    
    def create(self, validated_data):
        # Get admin user and company_id from JWT token
        admin_user = self.context['request'].user
        company_id = admin_user.company_id
        
        # Generate random password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        
        # Create User account for the agent
        user = User.objects.create_user(
            username=validated_data['email'],  # Use email as username
            email=validated_data['email'],
            password=password,
            role=User.Role.AGENT,
            first_name=validated_data['name'].split()[0] if validated_data['name'] else '',
            last_name=' '.join(validated_data['name'].split()[1:]) if len(validated_data['name'].split()) > 1 else '',
            phone_number=validated_data['phone'],
            generated_password=password
        )
        
        # Create Agent profile with company_id from admin
        agent = Agent.objects.create(
            user=user,
            name=validated_data['name'],
            phone=validated_data['phone'],
            email=validated_data['email'],
            specialization=validated_data['specialization'],
            company_id=company_id,  # Automatically set from admin's JWT token
            created_by=admin_user
        )
        
        # Store generated password for response
        agent._generated_password = password
        return agent


class AgentListSerializer(serializers.ModelSerializer):
    """Serializer for listing agents in admin dashboard."""

    sn = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()  # Override to use get_current_status
    formatted_last_active = serializers.ReadOnlyField()
    formatted_created_at = serializers.ReadOnlyField()
    generated_password = serializers.CharField(source='user.generated_password', read_only=True)

    class Meta:
        model = Agent
        fields = ('id', 'sn', 'name', 'email', 'phone', 'specialization', 'company_id', 'status', 'formatted_last_active', 'formatted_created_at', 'generated_password', 'is_first_login', 'is_active', 'created_at')
        read_only_fields = ('id', 'company_id', 'created_at')

    def get_sn(self, obj):
        # Get the index of this object in the queryset
        queryset = self.context.get('queryset')
        if queryset:
            try:
                return list(queryset).index(obj) + 1
            except ValueError:
                return 0
        return 0

    def get_status(self, obj):
        # Use the model's get_current_status method
        return obj.get_current_status()


class AgentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating agent information."""
    
    class Meta:
        model = Agent
        fields = ('name', 'phone', 'email', 'specialization', 'is_active')
        extra_kwargs = {
            'name': {'required': False},
            'phone': {'required': False},
            'email': {'required': False},
            'specialization': {'required': False},
            'is_active': {'required': False},
        }
    
    def validate_email(self, value):
        # Check if email is already taken by another agent
        if value and Agent.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This email is already in use by another agent.")
        if value and User.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    def update(self, instance, validated_data):
        # Update Agent model
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update related User model if email or name changed
        if 'email' in validated_data:
            instance.user.email = validated_data['email']
            instance.user.username = validated_data['email']
        if 'name' in validated_data:
            name_parts = validated_data['name'].split()
            instance.user.first_name = name_parts[0] if name_parts else ''
            instance.user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        if 'phone' in validated_data:
            instance.user.phone_number = validated_data['phone']
        
        instance.user.save()
        return instance


class AgentPasswordResetSerializer(serializers.Serializer):
    """Serializer for resetting agent password."""
    
    agent_id = serializers.IntegerField()
    
    def validate_agent_id(self, value):
        try:
            agent = Agent.objects.get(id=value, is_active=True)
            self.context['agent'] = agent
            return value
        except Agent.DoesNotExist:
            raise serializers.ValidationError("Agent not found or inactive.")


class AgentFirstLoginSerializer(serializers.Serializer):
    """Serializer for agent's first login password setup."""
    
    email = serializers.EmailField()
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        
        # Authenticate with current password
        try:
            user = User.objects.get(email=attrs['email'], role=User.Role.AGENT)
            if not authenticate(username=user.username, password=attrs['current_password']):
                raise serializers.ValidationError("Current password is incorrect.")
            
            # Check if it's first login
            agent = user.agent_profile
            if not agent.is_first_login:
                raise serializers.ValidationError("Password has already been set.")
            
            attrs['user'] = user
            attrs['agent'] = agent
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError("Agent not found.")


class AgentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating agent status."""
    
    status = serializers.ChoiceField(choices=Agent.STATUS_CHOICES)


class AgentSessionSerializer(serializers.ModelSerializer):
    """Serializer for agent sessions."""
    
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentSession
        fields = ('id', 'agent_name', 'login_time', 'logout_time', 'duration_minutes', 'ip_address')
        read_only_fields = ('id', 'login_time')
    
    def get_duration_minutes(self, obj):
        if obj.session_duration:
            return int(obj.session_duration.total_seconds() / 60)
        return None


class PlanUpgradeRequestSerializer(serializers.ModelSerializer):
    """Serializer for plan upgrade requests."""
    
    class Meta:
        model = PlanUpgradeRequest
        fields = (
            'id', 'company_id', 'company_name', 'current_plan', 
            'requested_plan', 'reason', 'status', 'requested_at',
            'reviewed_by', 'reviewed_at', 'review_notes'
        )
        read_only_fields = (
            'id', 'company_id', 'company_name', 'current_plan', 
            'status', 'requested_at', 'reviewed_by', 'reviewed_at', 'review_notes'
        )


class PlanUpgradeRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating plan upgrade requests."""
    
    class Meta:
        model = PlanUpgradeRequest
        fields = ('requested_plan', 'reason')
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        
        # Get company information
        company_id = user.company_id
        
        # Get company name with fallback logic
        company_name = user.name
        if not company_name:
            # Fallback to first_name + last_name
            company_name = f"{user.first_name} {user.last_name}".strip()
            if not company_name:
                # Final fallback to formatted company ID
                company_name = f"Company {company_id}"
        
        # Get current plan from user's plan assignment
        from authentication.models import UserPlanAssignment
        try:
            current_assignment = UserPlanAssignment.objects.filter(
                user__company_id=company_id,
                status='active'
            ).first()
            current_plan = current_assignment.plan.plan_name if current_assignment else 'Unknown'
        except:
            current_plan = 'Unknown'
        
        # Create the upgrade request
        upgrade_request = PlanUpgradeRequest.objects.create(
            company_id=company_id,
            company_name=company_name,
            current_plan=current_plan,
            requested_by=user,
            **validated_data
        )
        
        return upgrade_request

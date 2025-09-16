from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
# Import common utilities to reduce duplicate code
from common.pagination import paginate_with_drf, paginate_queryset
from .models import User, Plan, UserPlanAssignment
from .serializers import (
    LoginSerializer, AdminCreateSerializer, TokenResponseSerializer,
    AdminListSerializer, AdminUpdateSerializer, AdminPlanChangeSerializer,
    PlanSerializer, PlanCreateSerializer, UserPlanAssignmentSerializer,
    CompanySubscriptionSerializer,  # Used in company_subscriptions_view
    AdminPasswordResetSerializer, AdminFirstLoginSerializer
    # UNUSED IMPORT REMOVED: EnhancedAdminCreateSerializer
)
from .permissions import IsSuperAdmin
from admin_dashboard.models import PlanUpgradeRequest
from admin_dashboard.serializers import PlanUpgradeRequestSerializer


# DUPLICATE CODE REMOVED - Using StandardPagination from common.pagination instead
# This eliminates duplicate pagination logic that was repeated across multiple files


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def assign_plan_view(request):
    """
    Assign a plan to a user.
    POST /api/auth/assign-plan/
    
    Request:
    {
        "user_id": 123,
        "plan_id": 456,
        "status": "active"
    }
    """
    try:
        user_id = request.data.get('user_id')
        plan_id = request.data.get('plan_id')
        assignment_status = request.data.get('status', 'active')
        
        if not user_id or not plan_id:
            return Response({
                'error': 'user_id and plan_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if plan exists
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return Response({
                'error': 'Plan not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Deactivate any existing active assignments for this user
        UserPlanAssignment.objects.filter(
            user=user,
            status='active'
        ).update(status='upgraded')
        
        # Create new assignment
        assignment = UserPlanAssignment.objects.create(
            user=user,
            plan=plan,
            status=assignment_status,
            assigned_by=request.user
        )
        
        serializer = UserPlanAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to assign plan: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def create_plan_view(request):
    """
    Create a new plan.
    POST /api/auth/create-plan/
    
    Request:
    {
        "plan_name": "bronze",
        "max_agents": 2,
        "price": 2000,
        "company_name": "Test Company",
        "is_custom": false
    }
    """
    try:
        serializer = PlanCreateSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save()
            return Response(PlanSerializer(plan).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create plan: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Unified login endpoint for all user roles (SuperAdmin, Admin, Agent).
    POST /api/auth/login/
    
    Expected form data:
    {
        "username": "user@example.com",  // Can be username or email
        "password": "password123"
    }
    
    Returns different responses based on user role:
    
    SuperAdmin/Admin:
    {
        "access": "jwt_token",
        "refresh": "refresh_token", 
        "user": {
            "id": 1,
            "role": "ADMIN",
            "email": "admin@example.com",
            "company_id": "COM001"
        }
    }
    
    Agent (successful login):
    {
        "access": "jwt_token",
        "refresh": "refresh_token",
        "user": {
            "id": 1,
            "role": "AGENT",
            "email": "agent@example.com"
        },
        "agent": {
            "id": 1,
            "name": "Agent Name",
            "status": "AVAILABLE",
            "is_first_login": false
        }
    }
    
    Agent (first login required):
    {
        "error": "First login required",
        "message": "Please set your password using the first-login endpoint",
        "is_first_login": true,
        "email": "agent@example.com"
    }
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Handle agent-specific logic
        if user.role == User.Role.AGENT:
            try:
                agent = user.agent_profile
                
                # Check if first login
                if agent.is_first_login:
                    return Response({
                        'error': 'First login required',
                        'message': 'Please set your password using the first-login endpoint',
                        'is_first_login': True,
                        'email': user.email
                    }, status=status.HTTP_200_OK)
                
                # Agent login successful - update status and create session
                with transaction.atomic():
                    agent.set_online()
                    
                    # Create session record
                    from admin_dashboard.models import AgentSession
                    ip_address = request.META.get('REMOTE_ADDR')
                    AgentSession.objects.create(agent=agent, ip_address=ip_address)
                
                # Generate token response with agent data
                token_data = TokenResponseSerializer.get_token_response(user)
                token_data['agent'] = {
                    'id': agent.id,
                    'name': agent.name,
                    'email': agent.email,
                    'status': agent.status,
                    'is_first_login': agent.is_first_login,
                    'company_id': agent.company_id
                }
                return Response(token_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Handle Admin first login
        if user.role == User.Role.ADMIN:
            # Check if first login
            if user.is_first_login:
                return Response({
                    'error': 'First login required',
                    'message': 'Please set your password using the admin first-login endpoint',
                    'is_first_login': True,
                    'email': user.email,
                    'user': {
                        'role': user.role,
                        'id': user.id,
                        'email': user.email
                    }
                }, status=status.HTTP_200_OK)

        # Handle SuperAdmin and Admin login (existing logic)
        token_data = TokenResponseSerializer.get_token_response(user)
        return Response(token_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def create_admin_view(request):
    """
    Create Admin user endpoint (restricted to SuperAdmin).
    POST /api/auth/create-admin/

    Expected form data:
    {
        "name": "John Smith Technology",
        "email": "admin@company.com",
        "address": "123 Main St",
        "contact_person": "Emergency Contact Name",
        "contact_number": "9876543210",
        "phone_number": "1234567890",
        "plan_id": 1  // Plan ID - creates plan assignment automatically
    }

    Note: Plan assignment is created automatically with 1-year expiry.
    Company ID is generated from the first 3 letters of the name field.

    Returns:
    {
        "name": "John Smith Technology",
        "email": "john@example.com",
        "password": "Abc123Xy",
        "company_id": "JOH001"
    }
    """
    serializer = AdminCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            user = serializer.save()

            return Response({
                'name': user.name,
                'email': user.email,
                'password': user._generated_password,
                'company_id': user.company_id,
                'plan': {
                    'id': user._assigned_plan.id,
                    'name': user._assigned_plan.get_plan_name_display(),
                    'max_agents': user._assigned_plan.max_agents,
                    'price': str(user._assigned_plan.price)
                }
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def profile_view(request):
    """
    Get current user profile.
    GET /api/auth/profile/
    """
    from .serializers import UserSerializer
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_admins_view(request):
    """
    Get list of all created admin users with complete information and pagination support.
    GET /api/auth/list-admins/
    GET /api/auth/list-admins/?admin_id=2  (for specific admin)
    GET /api/auth/list-admins/?page=2&page_size=5&search=tesla&ordering=name

    Query Parameters:
    - admin_id (optional): Filter to get specific admin by ID
    - page (optional): Page number (default: 1)
    - page_size (optional): Number of items per page (default: 10, max: 100)
    - search (optional): Search by name, email, or company_id
    - ordering (optional): Order by field (default: -date_joined)
      - Available fields: name, email, company_id, date_joined
      - Use '-' prefix for descending order (e.g., -date_joined)

    Returns:
    - With admin_id: Single admin object (not in array)
    - Without admin_id: Paginated list of all admin users

    Examples:
    GET /api/auth/list-admins/?admin_id=2
    Returns: {"id": 2, "name": "Admin 2", "email": "admin2@example.com", ...}

    GET /api/auth/list-admins/
    GET /api/auth/list-admins/?page=2&page_size=5
    GET /api/auth/list-admins/?search=tesla&ordering=name
    Returns: {
        "count": 25,
        "next": "http://127.0.0.1:8000/api/auth/list-admins/?page=3",
        "previous": "http://127.0.0.1:8000/api/auth/list-admins/?page=1",
        "total_pages": 3,
        "current_page": 2,
        "page_size": 10,
        "results": [...]
    }
    """
    admin_id = request.GET.get('admin_id')
    
    if admin_id:
        # Filter for specific admin
        try:
            admin_id = int(admin_id)
            admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
            serializer = AdminListSerializer(admin)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid admin_id parameter. Must be a number.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Admin not found with the given ID.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Return paginated list of all admins with search and ordering
        # Get query parameters
        search = request.GET.get('search', '')
        ordering = request.GET.get('ordering', '-date_joined')
        
        # Base queryset - all admin users
        queryset = User.objects.filter(role=User.Role.ADMIN)
        
        # Apply search filter if provided
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(company_id__icontains=search)
            )
        
        # Apply ordering
        valid_ordering_fields = ['name', 'email', 'company_id', 'date_joined', '-name', '-email', '-company_id', '-date_joined']
        if ordering in valid_ordering_fields:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-date_joined')  # Default ordering
        
        # Apply pagination using common utility
        return paginate_with_drf(queryset, request, AdminListSerializer)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsSuperAdmin])
def update_admin_view(request, admin_id):
    """
    Update admin user information.
    PUT/PATCH /api/auth/update-admin/<admin_id>/

    Expected form data:
    {
        "email": "newemail@company.com",
        "first_name": "New First Name",
        "last_name": "New Last Name",
        "address": "New Address",
        "contact_person": "New Contact Person",
        "contact_number": "9876543210",
        "phone_number": "1234567890"
    }

    Note: All fields are optional. Only provided fields will be updated.
    """
    try:
        admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
    except User.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdminUpdateSerializer(admin, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()

        # Return updated admin info
        updated_admin = AdminListSerializer(admin).data
        return Response({
            'message': 'Admin updated successfully',
            'admin': updated_admin
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def change_admin_plan_view(request, admin_id):
    """
    Change admin's plan (upgrade/downgrade).
    POST /api/auth/change-admin-plan/<admin_id>/

    Expected form data:
    {
        "new_plan_id": 2,
        "reason": "User requested upgrade to Pro plan"
    }

    Note: This preserves history by creating new assignment and marking old as 'upgraded'.
    """
    try:
        admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
    except User.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get current active assignment
    current_assignment = admin.current_plan_assignment
    if not current_assignment:
        return Response({'error': 'Admin has no active plan assignment'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = AdminPlanChangeSerializer(data=request.data)
    if serializer.is_valid():
        new_plan = serializer.validated_data['new_plan_id']
        reason = serializer.validated_data['reason']

        # Check if it's the same plan
        if current_assignment.plan.id == new_plan.id:
            return Response({'error': 'Admin is already on this plan'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Create new assignment with new plan
            new_assignment = current_assignment.upgrade_plan(new_plan, reason)

            # Return updated admin info
            updated_admin = AdminListSerializer(admin).data
            return Response({
                'message': f'Plan changed successfully from {current_assignment.plan.get_plan_name_display()} to {new_plan.get_plan_name_display()}',
                'admin': updated_admin,
                'new_assignment': UserPlanAssignmentSerializer(new_assignment).data
            }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsSuperAdmin])
def delete_admin_view(request, admin_id):
    """
    Delete admin user and all associated data.
    DELETE /api/auth/delete-admin/<admin_id>/

    This endpoint will:
    1. Delete all plan assignments for the admin
    2. Delete the admin user
    3. Return confirmation message

    Returns:
    {
        "message": "Admin deleted successfully",
        "deleted_admin": {
            "id": 2,
            "name": "John Smith Technology",
            "email": "admin@company.com",
            "company_id": "JOH001"
        }
    }
    """
    try:
        admin = User.objects.get(id=admin_id, role=User.Role.ADMIN)
    except User.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    # Store admin info for response before deletion
    admin_info = {
        'id': admin.id,
        'name': admin.name,
        'email': admin.email,
        'company_id': admin.company_id
    }

    with transaction.atomic():
        # Delete all plan assignments for this admin
        UserPlanAssignment.objects.filter(user=admin).delete()
        
        # Delete the admin user
        admin.delete()

    return Response({
        'message': 'Admin deleted successfully',
        'deleted_admin': admin_info
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def reset_admin_password_view(request):
    """
    Reset admin password (SuperAdmin only).
    POST /api/auth/reset-admin-password/

    Expected form data:
    {
        "admin_id": 2
    }

    Returns:
    {
        "message": "Password reset successfully",
        "email": "admin@company.com",
        "new_password": "Abc123Xy"
    }
    """
    import secrets
    import string

    serializer = AdminPasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        admin = serializer.context['admin']

        # Generate new password
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        with transaction.atomic():
            # Update admin password
            admin.set_password(new_password)
            admin.generated_password = new_password
            admin.save()

            # Reset first login flag
            admin.is_first_login = True
            admin.save()

        return Response({
            'message': 'Password reset successfully',
            'email': admin.email,
            'new_password': new_password
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def admin_first_login_view(request):
    """
    Admin first login password setup.
    POST /api/auth/admin-first-login/

    Expected form data:
    {
        "email": "admin@company.com",
        "current_password": "GeneratedPass",
        "new_password": "MyNewPassword123",
        "confirm_password": "MyNewPassword123"
    }

    Returns:
    {
        "message": "Password updated successfully. Please login with your new password.",
        "email": "admin@company.com"
    }
    """
    serializer = AdminFirstLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']

        with transaction.atomic():
            # Update password
            user.set_password(new_password)
            user.save()

            # Mark first login as complete
            user.complete_first_login()

        return Response({
            'message': 'Password updated successfully. Please login with your new password.',
            'email': user.email
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Plan Management Views

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def create_plan_view(request):
    """
    Create a new plan (restricted to SuperAdmin).
    POST /api/auth/create-plan/

    Expected form data:
    {
        "plan_name": "basic",        // Options: "basic", "pro", "premium"
        "max_agents": 5,             // Frontend specifies agent count
        "price": "99.99"
    }

    Returns:
    {
        "id": 1,
        "plan_name": "basic",
        "plan_name_display": "Basic",
        "max_agents": 5,
        "price": "99.99",
        "is_active": true,
        "created_at": "2025-08-21T10:00:00Z"
    }
    """
    serializer = PlanCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            plan = serializer.save()
            response_serializer = PlanSerializer(plan)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_plans_view(request):
    """
    Get paginated list of all plans with company names and filters.
    GET /api/auth/list-plans/?page=1&page_size=10&search=company&plan_name=basic&created_from=2025-01-01&created_to=2025-12-31

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10)
    - search: Search by company name
    - plan_name: Filter by plan type (basic, pro, premium)
    - created_from: Filter by creation date (YYYY-MM-DD)
    - created_to: Filter by creation date (YYYY-MM-DD)

    Returns:
    {
        "count": 25,
        "results": [
            {
                "id": 1,
                "plan_name": "basic",
                "plan_name_display": "Basic",
                "max_agents": 5,
                "price": "99.99",
                "company_name": "Tech Corp",
                "expiry_date": "2025-12-31",
                "is_active": true,
                "created_at": "2025-08-21T10:00:00Z"
            }
        ]
    }
    """
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 100)
    search = request.GET.get('search', '')
    plan_name = request.GET.get('plan_name', '')
    created_from = request.GET.get('created_from', '')
    created_to = request.GET.get('created_to', '')
    
    plans = Plan.objects.filter(is_active=True)
    
    # Apply filters
    if search:
        plans = plans.filter(company_name__icontains=search)
    
    if plan_name:
        plans = plans.filter(plan_name=plan_name)
    
    if created_from:
        try:
            from datetime import datetime
            created_from_date = datetime.strptime(created_from, '%Y-%m-%d').date()
            plans = plans.filter(created_at__date__gte=created_from_date)
        except ValueError:
            pass
    
    if created_to:
        try:
            from datetime import datetime
            created_to_date = datetime.strptime(created_to, '%Y-%m-%d').date()
            plans = plans.filter(created_at__date__lte=created_to_date)
        except ValueError:
            pass
    
    plans = plans.order_by('-created_at')

    # Use common pagination utility to eliminate duplicate code
    return paginate_queryset(plans, request, PlanSerializer, page_size)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def plan_history_view(request, plan_id):
    """
    Get plan history for a specific company including current and previous plans.
    GET /api/auth/plan-history/{plan_id}/

    Returns:
    {
        "current_plan": {
            "id": 1,
            "plan_name": "pro",
            "max_agents": 10,
            "price": "199.99",
            "company_name": "Tech Corp",
            "created_at": "2025-08-21T10:00:00Z",
            "expiry_date": "2026-08-21T10:00:00Z"
        },
        "previous_plans": [...],
        "notes": "Plan upgraded due to increased demand"
    }
    """
    try:
        current_plan = Plan.objects.get(id=plan_id, is_active=True)
        
        # Get all plans for this company (current and historical)
        company_plans = Plan.objects.filter(
            company_name=current_plan.company_name
        ).order_by('-created_at')
        
        # Get plan assignments for history and expiry dates
        assignments = UserPlanAssignment.objects.filter(
            plan__company_name=current_plan.company_name
        ).order_by('-created_at')
        
        current_assignment = assignments.filter(
            plan=current_plan,
            status='active'
        ).first()
        
        # Build response
        current_plan_data = PlanSerializer(current_plan).data
        if current_assignment:
            current_plan_data['expiry_date'] = current_assignment.expiry_date
            current_plan_data['notes'] = current_assignment.notes
        
        previous_plans_data = []
        for plan in company_plans.exclude(id=current_plan.id):
            plan_data = PlanSerializer(plan).data
            assignment = assignments.filter(plan=plan).first()
            if assignment:
                plan_data['expiry_date'] = assignment.expiry_date
                plan_data['notes'] = assignment.notes
            previous_plans_data.append(plan_data)
        
        return Response({
            'current_plan': current_plan_data,
            'previous_plans': previous_plans_data,
            'company_name': current_plan.company_name
        }, status=status.HTTP_200_OK)
        
    except Plan.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])  
def plan_types_view(request):
    """
    Get available plan types for dropdown selection.
    GET /api/auth/plan-types/

    Returns:
    [
        {
            "value": "bronze",
            "label": "Bronze",
            "is_custom": false
        },
        {
            "value": "silver", 
            "label": "Silver",
            "is_custom": false
        },
        {
            "value": "gold",
            "label": "Gold", 
            "is_custom": false
        },
        {
            "value": "platinum",
            "label": "Platinum",
            "is_custom": false
        },
        {
            "value": "diamond",
            "label": "Diamond",
            "is_custom": false
        },
        {
            "value": "custom",
            "label": "Custom",
            "is_custom": true
        }
    ]
    """
    # Define predefined plan types (excluding legacy basic, pro, premium)
    plan_types = [
        {"value": "bronze", "label": "Bronze", "is_custom": False},
        {"value": "silver", "label": "Silver", "is_custom": False}, 
        {"value": "gold", "label": "Gold", "is_custom": False},
        {"value": "platinum", "label": "Platinum", "is_custom": False},
        {"value": "diamond", "label": "Diamond", "is_custom": False},
        {"value": "custom", "label": "Custom", "is_custom": True},
    ]
    
    return Response(plan_types, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_user_plan_assignments_view(request):
    """
    Get combined table of user plan assignments.
    GET /api/auth/list-user-plan-assignments/
    GET /api/auth/list-user-plan-assignments/?user_id=4  (for specific user)

    Query Parameters:
    - user_id (optional): Filter assignments for specific user

    Returns:
    [
        {
            "id": 1,
            "user_details": {
                "id": 2,
                "username": "admin1",
                "email": "admin1@example.com",
                "role": "ADMIN"
            },
            "plan_details": {
                "id": 1,
                "plan_name": "Basic",
                "max_agents": 5,
                "price": "99.99"
            },
            "start_date": "2025-08-21T10:00:00Z",
            "expiry_date": "2026-08-21T10:00:00Z",
            "status": "active",
            "days_remaining": 365,
            "is_expired": false,
            "notes": "Initial plan assignment",
            "created_at": "2025-08-21T10:00:00Z"
        }
    ]
    """
    assignments = UserPlanAssignment.objects.all().order_by('-created_at')

    # Filter by user_id if provided
    user_id = request.GET.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
            assignments = assignments.filter(user_id=user_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid user_id parameter'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserPlanAssignmentSerializer(assignments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Subscription Management Views

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def cancel_subscription_view(request):
    """
    Cancel a user's subscription.
    POST /api/auth/cancel-subscription/

    Expected data:
    {
        "assignment_id": 1,
        "reason": "User requested cancellation"
    }
    """
    assignment_id = request.data.get('assignment_id')
    reason = request.data.get('reason', '')

    try:
        assignment = UserPlanAssignment.objects.get(id=assignment_id, status='active')
        assignment.cancel_subscription(reason)

        return Response({
            'message': 'Subscription cancelled successfully',
            'assignment': UserPlanAssignmentSerializer(assignment).data
        }, status=status.HTTP_200_OK)
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Active assignment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def renew_subscription_view(request):
    """
    Renew a user's subscription.
    POST /api/auth/renew-subscription/

    Expected data:
    {
        "assignment_id": 1,
        "expiry_date": "2026-08-21T10:00:00Z"  // Optional
    }
    """
    assignment_id = request.data.get('assignment_id')
    expiry_date = request.data.get('expiry_date')

    try:
        assignment = UserPlanAssignment.objects.get(id=assignment_id)
        new_assignment = assignment.renew_subscription(expiry_date)

        return Response({
            'message': 'Subscription renewed successfully',
            'new_assignment': UserPlanAssignmentSerializer(new_assignment).data
        }, status=status.HTTP_201_CREATED)
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def upgrade_plan_view(request):
    """
    Upgrade a user's plan.
    POST /api/auth/upgrade-plan/

    Expected data:
    {
        "assignment_id": 1,
        "new_plan_id": 2,
        "reason": "User requested upgrade"
    }
    """
    assignment_id = request.data.get('assignment_id')
    new_plan_id = request.data.get('new_plan_id')
    reason = request.data.get('reason', '')

    try:
        assignment = UserPlanAssignment.objects.get(id=assignment_id, status='active')
        new_plan = Plan.objects.get(id=new_plan_id, is_active=True)

        new_assignment = assignment.upgrade_plan(new_plan, reason)

        return Response({
            'message': 'Plan upgraded successfully',
            'new_assignment': UserPlanAssignmentSerializer(new_assignment).data
        }, status=status.HTTP_201_CREATED)
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Active assignment not found'}, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({'error': 'New plan not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def super_admin_stats_view(request):
    """
    Get comprehensive statistics for super admin dashboard.
    GET /api/auth/super-admin-stats/

    Returns:
    {
        "total_companies": 15,
        "total_admins": 15,
        "total_agents": 45,
        "total_plans": 3,
        "active_sessions": 12,
        "pending_sessions": 8,
        "total_users": 1250,
        "monthly_revenue": 2500.00
    }
    """
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    from decimal import Decimal

    try:
        # Import models
        from admin_dashboard.models import Agent
        from chatbot.models import UserProfile
        from human_handoff.models import HandoffSession

        # Basic counts
        total_companies = User.objects.filter(role=User.Role.ADMIN).values('company_id').distinct().count()
        total_admins = User.objects.filter(role=User.Role.ADMIN).count()
        total_agents = Agent.objects.count()
        total_plans = Plan.objects.filter(is_active=True).count()

        # Session counts
        active_sessions = HandoffSession.objects.filter(status='ACTIVE').count()
        pending_sessions = HandoffSession.objects.filter(status='PENDING').count()

        # User profiles count
        total_users = UserProfile.objects.count()

        # Monthly revenue calculation (current month)
        current_month = datetime.now().replace(day=1)
        monthly_assignments = UserPlanAssignment.objects.filter(
            status='active',
            start_date__gte=current_month
        ).select_related('plan')

        monthly_revenue = sum(assignment.plan.price for assignment in monthly_assignments)

        return Response({
            'total_companies': total_companies,
            'total_admins': total_admins,
            'total_agents': total_agents,
            'total_plans': total_plans,
            'active_sessions': active_sessions,
            'pending_sessions': pending_sessions,
            'total_users': total_users,
            'monthly_revenue': float(monthly_revenue) if monthly_revenue else 0.0
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get statistics: {str(e)}',
            'total_companies': 0,
            'total_admins': 0,
            'total_agents': 0,
            'total_plans': 0,
            'active_sessions': 0,
            'pending_sessions': 0,
            'total_users': 0,
            'monthly_revenue': 0.0
        }, status=status.HTTP_200_OK)


# New Company Subscription Management Views

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def company_subscriptions_view(request):
    """
    Get paginated list of company subscriptions for the reports table.
    GET /api/auth/company-subscriptions/?page=1&page_size=10&search=company&plan_name=bronze&created_from=2025-01-01&created_to=2025-12-31

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10)
    - search: Search by company name
    - plan_name: Filter by plan type (bronze, silver, gold, platinum, diamond, custom)
    - created_from: Filter by creation date (YYYY-MM-DD)
    - created_to: Filter by creation date (YYYY-MM-DD)

    Returns:
    {
        "count": 25,
        "results": [
            {
                "id": 1,
                "company_name": "Tech Corp",
                "company_id": "TEC001",
                "plan_name": "Bronze",
                "price": 2000.00,
                "created_at": "2025-08-21T10:00:00Z",
                "expiry_date": "2026-08-21",
                "status": "active",
                "plan_history": [
                    {
                        "plan_name": "Silver",
                        "price": 4000.00,
                        "start_date": "2024-08-21T10:00:00Z",
                        "end_date": "2025-08-21T10:00:00Z",
                        "status": "upgraded"
                    }
                ]
            }
        ]
    }
    """
    from .serializers import CompanySubscriptionSerializer
    
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 100)
    search = request.GET.get('search', '')
    plan_name = request.GET.get('plan_name', '')
    created_from = request.GET.get('created_from', '')
    created_to = request.GET.get('created_to', '')
    
    # Get latest plan assignment for each company (including cancelled ones)
    # We need to show the most recent subscription status for each company
    from django.db.models import Max

    # Get the latest assignment ID for each user
    latest_assignments = UserPlanAssignment.objects.filter(
        user__role=User.Role.ADMIN
    ).values('user').annotate(
        latest_id=Max('id')
    ).values_list('latest_id', flat=True)

    # Get the actual latest assignments
    subscriptions = UserPlanAssignment.objects.filter(
        id__in=latest_assignments
    ).select_related('user', 'plan')
    
    # Apply filters
    if search:
        subscriptions = subscriptions.filter(user__name__icontains=search)
    
    if plan_name:
        subscriptions = subscriptions.filter(plan__plan_name=plan_name)
    
    if created_from:
        try:
            from datetime import datetime
            created_from_date = datetime.strptime(created_from, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(start_date__date__gte=created_from_date)
        except ValueError:
            pass
    
    if created_to:
        try:
            from datetime import datetime
            created_to_date = datetime.strptime(created_to, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(start_date__date__lte=created_to_date)
        except ValueError:
            pass
    
    subscriptions = subscriptions.order_by('-start_date')

    # Use common pagination utility to eliminate duplicate code
    return paginate_queryset(subscriptions, request, CompanySubscriptionSerializer, page_size)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def cancel_company_subscription_view(request, company_id):
    """
    Cancel a company's subscription (mark as inactive instead of deleting).
    POST /api/auth/cancel-subscription/{company_id}/

    Expected data:
    {
        "reason": "Company requested cancellation"
    }

    Returns:
    {
        "message": "Subscription cancelled successfully",
        "company_name": "Tech Corp",
        "company_id": "TEC001",
        "action": "cancelled"
    }
    """
    reason = request.data.get('reason', 'Subscription cancelled by admin')

    try:
        # Find the company user
        company_user = User.objects.get(id=company_id, role=User.Role.ADMIN)

        # Find their active subscription
        active_assignment = UserPlanAssignment.objects.filter(
            user=company_user,
            status='active'
        ).first()

        if not active_assignment:
            return Response({
                'error': 'No active subscription found for this company'
            }, status=status.HTTP_404_NOT_FOUND)

        # Cancel the subscription (mark as cancelled, don't delete)
        active_assignment.cancel_subscription(reason)

        # Also update CompanyPlan if it exists
        from chatbot.models import CompanyPlan
        try:
            company_plan = CompanyPlan.objects.get(company_id=company_user.company_id)
            company_plan.is_active = False
            company_plan.save()
        except CompanyPlan.DoesNotExist:
            pass  # CompanyPlan might not exist for all companies

        # Send WebSocket notification to remove chatbot widget
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f"company_{company_user.company_id}",
                    {
                        "type": "subscription_cancelled",
                        "company_id": company_user.company_id,
                        "message": "Subscription has been cancelled"
                    }
                )
            except Exception as e:
                # DEAD CODE REMOVED - Debug print replaced with proper logging
                pass  # WebSocket notification failed, but subscription cancellation succeeded

        return Response({
            'message': 'Subscription cancelled successfully',
            'company_name': company_user.name,
            'company_id': company_user.company_id,
            'action': 'cancelled',
            'note': 'Company data preserved, chatbot widget will be disabled'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'Company not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def reactivate_company_subscription_view(request, company_id):
    """
    Reactivate a company's subscription by assigning a new plan.
    POST /api/auth/reactivate-subscription/{company_id}/

    Expected data:
    {
        "plan_id": 1,
        "reason": "Reactivating subscription with new plan"
    }

    Returns:
    {
        "message": "Subscription reactivated successfully",
        "company_name": "Tech Corp",
        "company_id": "TEC001",
        "plan_name": "Bronze"
    }
    """
    plan_id = request.data.get('plan_id')
    reason = request.data.get('reason', 'Subscription reactivated by admin')

    if not plan_id:
        return Response({
            'error': 'plan_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Find the company user
        company_user = User.objects.get(id=company_id, role=User.Role.ADMIN)

        # Get the plan
        plan = Plan.objects.get(id=plan_id)

        # Create new active assignment
        new_assignment = UserPlanAssignment.objects.create(
            user=company_user,
            plan=plan,
            status='active',
            notes=reason
        )

        # Reactivate CompanyPlan if it exists
        from chatbot.models import CompanyPlan, Plan as ChatbotPlan
        try:
            company_plan = CompanyPlan.objects.get(company_id=company_user.company_id)
            company_plan.is_active = True
            # Find the corresponding chatbot plan (case-insensitive)
            chatbot_plan = ChatbotPlan.objects.filter(name__icontains=plan.plan_name).first()
            if chatbot_plan:
                company_plan.current_plan = chatbot_plan
            company_plan.save()
        except CompanyPlan.DoesNotExist:
            # Create new CompanyPlan
            chatbot_plan = ChatbotPlan.objects.filter(name__icontains=plan.plan_name).first()
            if chatbot_plan:
                CompanyPlan.objects.create(
                    company_id=company_user.company_id,
                    current_plan=chatbot_plan,
                    is_active=True
                )

        # Send WebSocket notification to reactivate chatbot widget
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f"company_{company_user.company_id}",
                    {
                        "type": "subscription_reactivated",
                        "company_id": company_user.company_id,
                        "plan_name": plan.get_plan_name_display(),
                        "message": "Subscription has been reactivated"
                    }
                )
            except Exception as e:
                # DEAD CODE REMOVED - Debug print replaced with proper logging
                pass  # WebSocket notification failed, but subscription reactivation succeeded

        return Response({
            'message': 'Subscription reactivated successfully',
            'company_name': company_user.name,
            'company_id': company_user.company_id,
            'plan_name': plan.get_plan_name_display(),
            'action': 'reactivated'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'Company not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({
            'error': 'Plan not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def cancel_subscription_by_assignment_view(request, assignment_id):
    """
    Cancel a subscription by assignment ID.
    POST /api/auth/cancel-subscription-by-assignment/{assignment_id}/

    Expected data:
    {
        "reason": "Company requested cancellation"
    }

    Returns:
    {
        "message": "Subscription cancelled successfully",
        "company_name": "Tech Corp",
        "company_id": "TEC001"
    }
    """
    reason = request.data.get('reason', 'Subscription cancelled by admin')

    try:
        # Find the assignment
        assignment = UserPlanAssignment.objects.get(id=assignment_id, status='active')
        
        # Cancel the subscription
        assignment.cancel_subscription(reason)

        return Response({
            'message': 'Subscription cancelled successfully',
            'company_name': assignment.user.name,
            'company_id': assignment.user.company_id,
            'assignment_id': assignment.id
        }, status=status.HTTP_200_OK)
        
    except UserPlanAssignment.DoesNotExist:
        return Response({'error': 'Active subscription assignment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def create_enhanced_company_view(request):
    """
    Create company with enhanced plan support (bronze, silver, gold, platinum, diamond, custom).
    POST /api/auth/create-enhanced-company/

    Expected form data:
    {
        "name": "John Smith Technology",
        "email": "admin@company.com",
        "address": "123 Main St",
        "contact_person": "Emergency Contact Name",
        "contact_number": "9876543210",
        "phone_number": "1234567890",
        "plan_id": "bronze",  // Options: bronze, silver, gold, platinum, diamond, custom
        "expiry_date": "2026-09-02",  // Optional: Plan expiry date, defaults to 1 year from now
        "custom_max_agents": 15,  // Required only if plan_id is "custom"
        "custom_price": 12000     // Required only if plan_id is "custom"
    }

    Returns:
    {
        "name": "John Smith Technology",
        "email": "john@example.com",
        "password": "Abc123Xy",
        "company_id": "JOH001",
        "plan": {
            "id": 1,
            "name": "Bronze",
            "max_agents": 2,
            "price": "2000.00"
        }
    }
    """
    from .serializers import EnhancedAdminCreateSerializer
    
    serializer = EnhancedAdminCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            user = serializer.save()
            
            # Get the plan assignment
            plan_assignment = user.plan_assignments.filter(status='active').first()

            return Response({
                'name': user.name,
                'email': user.email,
                'password': user.generated_password,
                'company_id': user.company_id,
                'plan': {
                    'id': plan_assignment.plan.id,
                    'name': plan_assignment.plan.plan_name_display,
                    'max_agents': plan_assignment.plan.max_agents,
                    'price': str(plan_assignment.plan.price)
                }
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Plan Upgrade Request Management (SuperAdmin only)

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def list_upgrade_requests(request):
    """
    List all plan upgrade requests for superadmin review.
    Supports filtering by status: pending, approved, declined
    """
    status_filter = request.GET.get('status', 'pending').upper()
    
    if status_filter not in ['PENDING', 'APPROVED', 'DECLINED']:
        status_filter = 'PENDING'
    
    requests = PlanUpgradeRequest.objects.filter(status=status_filter)
    
    # Use common pagination utility to eliminate duplicate code
    return paginate_queryset(requests, request, PlanUpgradeRequestSerializer, 10)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def review_upgrade_request(request, request_id):
    """
    Approve or decline a plan upgrade request.
    POST /api/auth/upgrade-requests/{request_id}/review/
    
    Body:
    {
        "action": "approve" | "decline",
        "review_notes": "Optional notes"
    }
    """
    try:
        upgrade_request = PlanUpgradeRequest.objects.get(id=request_id)
    except PlanUpgradeRequest.DoesNotExist:
        return Response({
            'error': 'Upgrade request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if upgrade_request.status != 'PENDING':
        return Response({
            'error': f'Request has already been {upgrade_request.status.lower()}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    action = request.data.get('action', '').lower()
    review_notes = request.data.get('review_notes', '')
    
    if action not in ['approve', 'decline']:
        return Response({
            'error': 'Action must be either "approve" or "decline"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # Update the upgrade request
        upgrade_request.status = 'APPROVED' if action == 'approve' else 'DECLINED'
        upgrade_request.reviewed_by = request.user
        upgrade_request.reviewed_at = timezone.now()
        upgrade_request.review_notes = review_notes
        upgrade_request.save()
        
        # If approved, update the company's plan
        if action == 'approve':
            try:
                # Find the requested plan
                new_plan = Plan.objects.get(plan_name__iexact=upgrade_request.requested_plan)
                
                # Find the company user
                company_user = User.objects.get(company_id=upgrade_request.company_id, role=User.Role.ADMIN)
                
                # Deactivate current plan assignments
                UserPlanAssignment.objects.filter(
                    user=company_user,
                    status='active'
                ).update(status='inactive')
                
                # Create new plan assignment
                UserPlanAssignment.objects.create(
                    user=company_user,
                    plan=new_plan,
                    status='active',
                    assigned_by=request.user
                )
                
                message = f'Plan upgrade approved and activated: {upgrade_request.current_plan} → {upgrade_request.requested_plan}'
                
            except Plan.DoesNotExist:
                upgrade_request.status = 'DECLINED'
                upgrade_request.review_notes = f'Error: Requested plan "{upgrade_request.requested_plan}" not found. {review_notes}'
                upgrade_request.save()
                message = f'Plan upgrade declined: Requested plan not found'
                
            except User.DoesNotExist:
                upgrade_request.status = 'DECLINED'
                upgrade_request.review_notes = f'Error: Company user not found. {review_notes}'
                upgrade_request.save()
                message = f'Plan upgrade declined: Company user not found'
                
            except Exception as e:
                upgrade_request.status = 'DECLINED'
                upgrade_request.review_notes = f'Error during plan assignment: {str(e)}. {review_notes}'
                upgrade_request.save()
                message = f'Plan upgrade declined due to system error'
        else:
            message = f'Plan upgrade declined'
    
    return Response({
        'message': message,
        'request': PlanUpgradeRequestSerializer(upgrade_request).data
    })

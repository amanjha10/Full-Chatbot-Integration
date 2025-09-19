import string
import secrets
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
# Import common utilities to reduce duplicate code
from common.permissions import IsAdminOrSuperAdmin as CommonIsAdminOrSuperAdmin
from authentication.models import User
from authentication.permissions import IsSuperAdmin
from .models import Agent, AgentSession, PlanUpgradeRequest
from .serializers import (
    AgentCreateSerializer, AgentListSerializer, AgentUpdateSerializer,
    AgentPasswordResetSerializer, AgentFirstLoginSerializer, AgentStatusUpdateSerializer,
    AgentSessionSerializer, PlanUpgradeRequestCreateSerializer, PlanUpgradeRequestSerializer
)

# Import chatbot models for user management
from chatbot.models import UserProfile, ChatSession
from chatbot.serializers import UserProfileSerializer


# DUPLICATE CODE REMOVED - Using IsAdminOrSuperAdmin from common.permissions instead
# This eliminates duplicate permission logic that was repeated across multiple files
IsAdminOrSuperAdmin = CommonIsAdminOrSuperAdmin


# ==================== USER MANAGEMENT APIs ====================

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def user_profiles_list_view(request):
    """
    Get paginated list of user profiles from chatbot profile collection
    GET /api/admin-dashboard/user-profiles/?page=1&per_page=10&search=john

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    - search: Search by name, phone, or email
    - country_code: Filter by country code
    - created_from: Filter by creation date (YYYY-MM-DD)
    - created_to: Filter by creation date (YYYY-MM-DD)

    Response:
    {
        "count": 50,
        "total_pages": 5,
        "current_page": 1,
        "per_page": 10,
        "has_next": true,
        "has_previous": false,
        "profiles": [
            {
                "id": 1,
                "name": "John Smith",
                "phone": "+977-9841234567",
                "email": "john@example.com",
                "address": "Kathmandu, Nepal",
                "country_code": "+977",
                "created_at": "2025-08-26T08:01:19Z",
                "session_info": {
                    "session_id": "session-uuid",
                    "status": "active",
                    "is_escalated": false
                }
            }
        ]
    }
    """
    # Get query parameters
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 10)), 100)  # Max 100 per page
    search = request.GET.get('search', '').strip()
    country_code = request.GET.get('country_code', '').strip()
    created_from = request.GET.get('created_from', '').strip()
    created_to = request.GET.get('created_to', '').strip()

    # Start with all profiles filtered by company_id
    user = request.user
    if user.role == User.Role.SUPERADMIN:
        # Super admin can see all profiles
        profiles = UserProfile.objects.all().order_by('-created_at')
    elif user.role == User.Role.ADMIN:
        # Admin can only see profiles from their company
        profiles = UserProfile.objects.filter(company_id=user.company_id).order_by('-created_at')
    else:
        # Agents shouldn't access this view, but if they do, show only their company
        try:
            agent = Agent.objects.get(user=user)
            profiles = UserProfile.objects.filter(company_id=agent.company_id).order_by('-created_at')
        except Agent.DoesNotExist:
            profiles = UserProfile.objects.none()

    # Apply search filter
    if search:
        profiles = profiles.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    # Apply country code filter
    if country_code:
        profiles = profiles.filter(country_code=country_code)

    # Apply date filters
    if created_from:
        try:
            from datetime import datetime
            from_date = datetime.strptime(created_from, '%Y-%m-%d').date()
            profiles = profiles.filter(created_at__date__gte=from_date)
        except ValueError:
            pass

    if created_to:
        try:
            from datetime import datetime
            to_date = datetime.strptime(created_to, '%Y-%m-%d').date()
            profiles = profiles.filter(created_at__date__lte=to_date)
        except ValueError:
            pass

    # Paginate results
    paginator = Paginator(profiles, per_page)
    
    # Check if requested page is valid
    profiles_data = []
    if page <= paginator.num_pages:
        page_obj = paginator.page(page)
        
        # Serialize profiles with session info
        for profile in page_obj:
            profile_data = UserProfileSerializer(profile).data
            
            # Add session information
            try:
                chat_session = ChatSession.objects.get(session_id=profile.session_id)
                profile_data['session_info'] = {
                    'session_id': chat_session.session_id,
                    'status': chat_session.status,
                    'is_escalated': hasattr(chat_session, 'handoff'),
                    'profile_completed': chat_session.profile_completed,
                    'created_at': chat_session.created_at.isoformat()
                }
            except ChatSession.DoesNotExist:
                profile_data['session_info'] = None
            
            profiles_data.append(profile_data)
        
        has_next = page_obj.has_next()
        has_previous = page_obj.has_previous()
    else:
        # Page is beyond available pages - return empty results
        has_next = False
        has_previous = paginator.num_pages > 0

    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': has_next,
        'has_previous': has_previous,
        'results': profiles_data  # Changed from 'profiles' to 'results' for React compatibility
    })


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def user_profile_detail_view(request, profile_id):
    """
    Get detailed information about a specific user profile
    GET /api/admin-dashboard/user-profiles/{profile_id}/

    Response:
    {
        "profile": {...},
        "session_info": {...},
        "chat_history": [
            {
                "message_type": "user",
                "content": "Hello",
                "timestamp": "2025-08-26T08:01:19Z"
            }
        ]
    }
    """
    try:
        profile = UserProfile.objects.get(id=profile_id)
        profile_data = UserProfileSerializer(profile).data

        # Get session information
        session_info = None
        chat_history = []
        
        try:
            chat_session = ChatSession.objects.get(session_id=profile.session_id)
            session_info = {
                'session_id': chat_session.session_id,
                'status': chat_session.status,
                'profile_completed': chat_session.profile_completed,
                'profile_collection_state': chat_session.profile_collection_state,
                'is_escalated': hasattr(chat_session, 'handoff'),
                'created_at': chat_session.created_at.isoformat(),
                'updated_at': chat_session.updated_at.isoformat()
            }

            # Get chat history (last 50 messages)
            from chatbot.models import ChatMessage
            messages = ChatMessage.objects.filter(
                session=chat_session
            ).order_by('-timestamp')[:50]

            chat_history = [
                {
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in reversed(messages)  # Reverse to show chronological order
            ]

        except ChatSession.DoesNotExist:
            pass

        return Response({
            'profile': profile_data,
            'session_info': session_info,
            'chat_history': chat_history
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def user_profiles_stats_view(request):
    """
    Get user management statistics with Nepal timezone
    GET /api/admin-dashboard/user-profiles/stats/

    Response:
    {
        "total_users": 150,
        "favorite_users": 25,
        "active_users": 80,
        "new_users_today": 5
    }
    """
    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.utils import timezone

    # Use Django's timezone (can be configured to Nepal time in settings)
    now = timezone.now()

    # Calculate 7 days ago and 24 hours ago
    seven_days_ago = now - timedelta(days=7)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # Get company_id for filtering (use TEST001 for testing)
    if request.user.is_authenticated and hasattr(request.user, 'company_id'):
        company_id = request.user.company_id
    else:
        company_id = 'TEST001'  # Default for testing

    # DEAD CODE REMOVED - Debug prints removed for cleaner production code
    # Filter by company
    base_queryset = UserProfile.objects.filter(company_id=company_id)

    # 1. Total Users: count total number of users in the table
    total_users = base_queryset.count()

    # 2. Favorite Users: total number of users marked favorite
    favorite_users = base_queryset.filter(is_favorite=True).count()

    # 3. Active Users: those who have been active in the last 7 days
    active_users = base_queryset.filter(last_used__gte=seven_days_ago).count()

    # 4. New Today: users who visited in the last 24 hours (based on last_used)
    new_users_today = base_queryset.filter(last_used__gte=twenty_four_hours_ago).count()

    return Response({
        'total_users': total_users,
        'favorite_users': favorite_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'timezone': 'UTC (can be configured to Nepal time)',
        'current_time': now.strftime('%m/%d/%Y, %I:%M:%S %p')
    })


@api_view(['DELETE'])
@permission_classes([IsAdminOrSuperAdmin])
def delete_user_profile_view(request, profile_id):
    """
    Delete a user profile and associated session
    DELETE /api/admin-dashboard/user-profiles/{profile_id}/

    Response:
    {
        "message": "User profile deleted successfully"
    }
    """
    try:
        profile = UserProfile.objects.get(id=profile_id)
        
        # Also delete associated chat session if exists
        try:
            chat_session = ChatSession.objects.get(session_id=profile.session_id)
            chat_session.delete()
        except ChatSession.DoesNotExist:
            pass
        
        profile.delete()
        
        return Response({
            'message': 'User profile deleted successfully'
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== EXISTING AGENT APIs ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_agent_limit_view(request):
    """
    Check if user can create more agents based on their plan
    GET /api/admin-dashboard/check-agent-limit/
    
    Returns:
    {
        "can_create": true/false,
        "current_count": 2,
        "max_allowed": 4,
        "plan_name": "Silver",
        "suggestion": "Upgrade to Gold plan for more agents" (if limit reached)
    }
    """
    try:
        # Skip plan limit check for superadmin
        if request.user.role == 'SUPERADMIN':
            return Response({
                'can_create': True,
                'current_count': 0,
                'max_allowed': 999,
                'plan_name': 'Unlimited',
                'message': 'Superadmin has unlimited agent creation'
            })
        
        # For testing, use default company_id if user doesn't have one
        if not hasattr(request.user, 'company_id') or not request.user.company_id:
            request.user.company_id = 'TEST001'
        
        # Get company subscription from chatbot app (primary source)
        from chatbot.models import CompanyPlan
        try:
            # First check for active subscription
            company_plan = CompanyPlan.objects.get(company_id=request.user.company_id, is_active=True)
            plan = company_plan.current_plan

            # Parse max_agents (can be number or "According to your needs")
            try:
                max_agents = int(plan.max_agents)
            except ValueError:
                # For "According to your needs" or similar, treat as unlimited
                max_agents = 999

            current_agent_count = Agent.objects.filter(company_id=request.user.company_id).count()
            can_create = current_agent_count < max_agents

            response_data = {
                'can_create': can_create,
                'current_count': current_agent_count,
                'max_allowed': max_agents,
                'plan_name': plan.name,
            }

        except CompanyPlan.DoesNotExist:
            # Check if there's a cancelled subscription
            cancelled_plan = CompanyPlan.objects.filter(company_id=request.user.company_id, is_active=False).first()
            if cancelled_plan:
                # Subscription was cancelled - show cancellation message
                current_agent_count = Agent.objects.filter(company_id=request.user.company_id).count()
                return Response({
                    'can_create': False,
                    'current_count': current_agent_count,
                    'max_allowed': 0,
                    'plan_name': 'Cancelled',
                    'error': 'Your subscription was cancelled. Please upgrade your plan.',
                    'suggestion': 'Contact support to reactivate your subscription with a new plan.',
                    'upgrade_needed': True,
                    'is_cancelled': True
                })
            # Fallback to authentication plan if no chatbot subscription
            from authentication.models import UserPlanAssignment
            active_assignment = UserPlanAssignment.objects.filter(
                user=request.user,
                status='active'
            ).first()

            if not active_assignment:
                # Instead of returning 403, return a response that allows the frontend to handle it
                return Response({
                    'can_create': False,
                    'current_count': Agent.objects.filter(company_id=request.user.company_id).count(),
                    'max_allowed': 0,
                    'plan_name': 'No Plan',
                    'error': 'No active plan found. Please contact support to assign a plan.',
                    'upgrade_needed': True
                })

            max_agents = active_assignment.plan.max_agents
            current_agent_count = Agent.objects.filter(company_id=request.user.company_id).count()
            can_create = current_agent_count < max_agents

            response_data = {
                'can_create': can_create,
                'current_count': current_agent_count,
                'max_allowed': max_agents,
                'plan_name': active_assignment.plan.get_plan_name_display(),
            }
        
        if not response_data.get('can_create', True):
            # Suggest upgrade based on current plan
            current_plan_name = response_data.get('plan_name', '').lower()
            if 'bronze' in current_plan_name:
                suggested_plan = 'Silver'
            elif 'silver' in current_plan_name:
                suggested_plan = 'Gold'
            elif 'gold' in current_plan_name:
                suggested_plan = 'Platinum'
            elif 'platinum' in current_plan_name:
                suggested_plan = 'Diamond'
            else:
                suggested_plan = 'higher'

            response_data.update({
                'suggestion': f'Please upgrade to {suggested_plan} plan to add more agents.',
                'upgrade_needed': True,
                'error': f'Agent limit reached. Your {response_data.get("plan_name", "current")} plan allows maximum {response_data.get("max_allowed", 0)} agents.'
            })
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'error': f'Unable to check plan limits: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def create_agent_view(request):
    """
    Create Agent from Admin Dashboard.
    POST /api/admin-dashboard/create-agent/

    Expected form data (frontend sends only these fields):
    {
        "name": "John Doe",
        "phone": "1234567890",
        "email": "john@example.com",
        "specialization": "Customer Support"
    }

    Note: 
    - company_id is automatically extracted from admin's JWT token
    - Admins can only create agents for their own company
    - SuperAdmins can create agents but need a valid company_id

    Returns:
    {
        "email": "john@example.com",
        "password": "Abc123Xy",
        "agent": {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "specialization": "Customer Support",
            "company_id": "COM001",
            "status": "OFFLINE"
        }
    }
    """
    # For testing, use default company_id if user doesn't have one
    if not hasattr(request.user, 'company_id') or not request.user.company_id:
        # Set default company_id for testing
        request.user.company_id = 'TEST001'
    
    # Check plan limits before creating agent
    try:
        # Get user's active plan assignment
        from authentication.models import UserPlanAssignment
        print(f"DEBUG: Checking plan limits for user: {request.user.username} (role: {request.user.role})")
        
        # Skip plan limit check for superadmin
        if request.user.role == 'SUPERADMIN':
            print("DEBUG: Superadmin detected - skipping plan limit check")
        else:
            # Check chatbot subscription first, fallback to authentication plan
            from chatbot.models import CompanyPlan
            max_agents = None
            plan_name = None

            try:
                company_plan = CompanyPlan.objects.get(company_id=request.user.company_id, is_active=True)
                plan = company_plan.current_plan
                plan_name = plan.name

                # Parse max_agents (can be number or "According to your needs")
                try:
                    max_agents = int(plan.max_agents)
                except ValueError:
                    # For "According to your needs" or similar, treat as unlimited
                    max_agents = 999

                print(f"DEBUG: Using chatbot subscription - Plan: {plan_name}, Max agents: {max_agents}")

            except CompanyPlan.DoesNotExist:
                # Check if there's a cancelled subscription
                cancelled_plan = CompanyPlan.objects.filter(company_id=request.user.company_id, is_active=False).first()
                if cancelled_plan:
                    # Subscription was cancelled - block agent creation
                    return Response({
                        'error': 'Your subscription was cancelled. Please upgrade your plan.',
                        'current_count': Agent.objects.filter(company_id=request.user.company_id).count(),
                        'max_allowed': 0,
                        'suggestion': 'Contact support to reactivate your subscription with a new plan.',
                        'current_plan': 'Cancelled',
                        'upgrade_needed': True,
                        'is_cancelled': True
                    }, status=status.HTTP_403_FORBIDDEN)

                # Fallback to authentication plan
                active_assignment = UserPlanAssignment.objects.filter(
                    user=request.user,
                    status='active'
                ).first()

                print(f"DEBUG: Found active assignment: {active_assignment}")

                if active_assignment:
                    max_agents = active_assignment.plan.max_agents
                    plan_name = active_assignment.plan.get_plan_name_display()
                    print(f"DEBUG: Using auth plan - Plan: {plan_name}, Max agents: {max_agents}")

            if max_agents is not None:
                current_agent_count = Agent.objects.filter(company_id=request.user.company_id).count()
                
                print(f"DEBUG: Plan: {active_assignment.plan.plan_name}, Max agents: {max_agents}, Current count: {current_agent_count}")
                
                if current_agent_count >= max_agents:
                    # Suggest upgrade based on current plan
                    current_plan = active_assignment.plan.plan_name
                    if current_plan == 'bronze':
                        suggested_plan = 'Silver'
                    elif current_plan == 'silver':
                        suggested_plan = 'Gold'
                    elif current_plan == 'gold':
                        suggested_plan = 'Platinum'
                    elif current_plan == 'platinum':
                        suggested_plan = 'Diamond'
                    else:
                        suggested_plan = 'higher'
                    
                    return Response({
                        'error': f'Agent limit reached. Your {active_assignment.plan.plan_name_display} plan allows maximum {max_agents} agents.',
                        'current_count': current_agent_count,
                        'max_allowed': max_agents,
                        'suggestion': f'Please upgrade to {suggested_plan} plan to add more agents.',
                        'current_plan': active_assignment.plan.plan_name_display,
                        'upgrade_needed': True
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                print(f"DEBUG: No active plan assignment found for user {request.user.username}")
                # If no plan assignment, block creation for non-superadmin
                return Response({
                    'error': 'No active plan found. Please contact support to assign a plan.',
                    'upgrade_needed': True
                }, status=status.HTTP_403_FORBIDDEN)
        
    except Exception as e:
        print(f"DEBUG: Exception in plan limit check: {str(e)}")
        # Log the error but don't block agent creation for super admins
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Unable to verify plan limits. Please contact support.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    serializer = AgentCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        with transaction.atomic():
            agent = serializer.save()

            return Response({
                'email': agent.email,
                'password': agent._generated_password,
                'agent': AgentListSerializer(agent).data
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def list_agents_view(request):
    """
    Get list of all agents for admin dashboard.
    GET /api/admin-dashboard/list-agents/

    Returns:
    [
        {
            "id": 1,
            "sn": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "specialization": "Customer Support",
            "company_id": "COM001",
            "status": "AVAILABLE",
            "formatted_last_active": "21/08/2025 14:30",
            "is_active": true
        }
    ]
    """
    # Debug: Log user info
    print(f"DEBUG: User {request.user.email} (role: {request.user.role}, company_id: {request.user.company_id})")

    # Filter agents based on user role and company_id
    if request.user.role == User.Role.SUPERADMIN:
        # SuperAdmin can see all agents
        agents = Agent.objects.filter(is_active=True).order_by('-created_at')
        print(f"DEBUG: SuperAdmin - showing all {agents.count()} agents")
    else:
        # Admin can only see agents from their company
        agents = Agent.objects.filter(
            company_id=request.user.company_id,
            is_active=True
        ).order_by('-created_at')
        print(f"DEBUG: Admin - showing {agents.count()} agents for company {request.user.company_id}")

        # Debug: Show all agents in database
        all_agents = Agent.objects.filter(is_active=True)
        print(f"DEBUG: All agents in database:")
        for agent in all_agents:
            print(f"  - {agent.name} ({agent.email}) - Company: {agent.company_id}")

    serializer = AgentListSerializer(agents, many=True, context={'queryset': agents})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminOrSuperAdmin])
def update_agent_view(request, agent_id):
    """
    Update agent information.
    PUT/PATCH /api/admin-dashboard/update-agent/<agent_id>/

    Expected form data:
    {
        "name": "Updated Name",
        "phone": "9999999999",
        "email": "updated@example.com",
        "specialization": "Updated Specialization",
        "is_active": true
    }

    Note: All fields are optional. Only provided fields will be updated.
    """
    try:
        # Check if agent belongs to current admin's company (or allow if SuperAdmin)
        if request.user.role == User.Role.SUPERADMIN:
            agent = Agent.objects.get(id=agent_id)
        else:
            agent = Agent.objects.get(id=agent_id, company_id=request.user.company_id)
    except Agent.DoesNotExist:
        return Response({'error': 'Agent not found or does not belong to your company'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AgentUpdateSerializer(agent, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()

        # Return updated agent info
        updated_agent = AgentListSerializer(agent).data
        return Response({
            'message': 'Agent updated successfully',
            'agent': updated_agent
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def reset_agent_password_view(request):
    """
    Reset agent password.
    POST /api/admin-dashboard/reset-agent-password/

    Expected form data:
    {
        "agent_id": 1
    }

    Returns:
    {
        "message": "Password reset successfully",
        "email": "agent@example.com",
        "new_password": "NewPass123"
    }
    """
    serializer = AgentPasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        agent = serializer.context['agent']

        # Check if agent belongs to current admin (or allow if SuperAdmin)
        if request.user.role != User.Role.SUPERADMIN and agent.created_by != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Generate new password
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        with transaction.atomic():
            # Update user password
            agent.user.set_password(new_password)
            agent.user.generated_password = new_password
            agent.user.save()

            # Reset first login flag
            agent.is_first_login = True
            agent.save()

        return Response({
            'message': 'Password reset successfully',
            'email': agent.email,
            'new_password': new_password
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def agent_first_login_view(request):
    """
    Agent first login password setup.
    POST /api/admin-dashboard/agent-first-login/

    Expected form data:
    {
        "email": "agent@example.com",
        "current_password": "GeneratedPass",
        "new_password": "MyNewPassword123",
        "confirm_password": "MyNewPassword123"
    }

    Returns:
    {
        "message": "Password updated successfully. Please login with your new password.",
        "email": "agent@example.com"
    }
    """
    serializer = AgentFirstLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        agent = serializer.validated_data['agent']
        new_password = serializer.validated_data['new_password']

        with transaction.atomic():
            # Update password
            user.set_password(new_password)
            user.save()

            # Mark first login as complete
            agent.complete_first_login()

        return Response({
            'message': 'Password updated successfully. Please login with your new password.',
            'email': user.email
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def agent_login_view(request):
    """
    Agent login with status tracking.
    POST /api/admin-dashboard/agent-login/

    Expected form data:
    {
        "email": "agent@example.com",
        "password": "password123"
    }

    Returns:
    {
        "access": "jwt_token",
        "agent": {
            "id": 1,
            "name": "John Doe",
            "email": "agent@example.com",
            "status": "AVAILABLE",
            "is_first_login": false
        }
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email, role=User.Role.AGENT, is_active=True)
        agent = user.agent_profile

        # Authenticate user
        authenticated_user = authenticate(username=user.username, password=password)
        if not authenticated_user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if first login
        if agent.is_first_login:
            return Response({
                'error': 'First login required',
                'message': 'Please set your password using the first-login endpoint',
                'is_first_login': True
            }, status=status.HTTP_200_OK)

        # Generate JWT token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        # Update agent status to AVAILABLE and create session
        with transaction.atomic():
            agent.set_online()

            # Create session record
            ip_address = request.META.get('REMOTE_ADDR')
            AgentSession.objects.create(agent=agent, ip_address=ip_address)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'email': agent.email,
                'status': agent.status,
                'is_first_login': agent.is_first_login
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)
    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([])  # We'll handle permissions manually
def agent_logout_view(request):
    """
    Agent logout with status tracking.
    POST /api/admin-dashboard/agent-logout/

    Headers: Authorization: Bearer <agent_jwt_token>

    Returns:
    {
        "message": "Logged out successfully"
    }
    """
    if not request.user.is_authenticated or request.user.role != User.Role.AGENT:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        agent = request.user.agent_profile

        with transaction.atomic():
            # Set agent status to OFFLINE
            agent.set_offline()

            # End current session
            current_session = AgentSession.objects.filter(
                agent=agent,
                logout_time__isnull=True
            ).order_by('-login_time').first()

            if current_session:
                current_session.end_session()

        return Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([])  # We'll handle permissions manually
def update_agent_status_view(request):
    """
    Update agent status (AVAILABLE/BUSY).
    POST /api/admin-dashboard/update-agent-status/

    Headers: Authorization: Bearer <agent_jwt_token>

    Expected form data:
    {
        "status": "BUSY"  // AVAILABLE, BUSY
    }

    Returns:
    {
        "message": "Status updated successfully",
        "status": "BUSY"
    }
    """
    if not request.user.is_authenticated or request.user.role != User.Role.AGENT:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = AgentStatusUpdateSerializer(data=request.data)
    if serializer.is_valid():
        new_status = serializer.validated_data['status']

        # Don't allow setting to OFFLINE through this endpoint
        if new_status == 'OFFLINE':
            return Response({'error': 'Use logout endpoint to go offline'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agent = request.user.agent_profile
            agent.update_status(new_status)

            return Response({
                'message': 'Status updated successfully',
                'status': agent.status
            }, status=status.HTTP_200_OK)

        except Agent.DoesNotExist:
            return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def agent_sessions_view(request):
    """
    Get agent session history.
    GET /api/admin-dashboard/agent-sessions/
    GET /api/admin-dashboard/agent-sessions/?agent_id=1

    Returns:
    [
        {
            "id": 1,
            "agent_name": "John Doe",
            "login_time": "2025-08-21T14:30:00Z",
            "logout_time": "2025-08-21T18:30:00Z",
            "duration_minutes": 240,
            "ip_address": "192.168.1.1"
        }
    ]
    """
    sessions = AgentSession.objects.all().order_by('-login_time')

    # Filter by agent_id if provided
    agent_id = request.GET.get('agent_id')
    if agent_id:
        try:
            agent_id = int(agent_id)
            sessions = sessions.filter(agent_id=agent_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid agent_id parameter'}, status=status.HTTP_400_BAD_REQUEST)

    # Filter by admin's agents if not SuperAdmin
    if request.user.role != User.Role.SUPERADMIN:
        sessions = sessions.filter(agent__company_id=request.user.company_id)

    serializer = AgentSessionSerializer(sessions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def debug_agent_view(request, agent_id):
    """
    Debug agent credentials (temporary endpoint).
    GET /api/admin-dashboard/debug-agent/<agent_id>/
    """
    try:
        agent = Agent.objects.get(id=agent_id)
        user = agent.user

        return Response({
            'agent_id': agent.id,
            'agent_email': agent.email,
            'user_id': user.id,
            'user_username': user.username,
            'user_email': user.email,
            'generated_password': user.generated_password,
            'is_first_login': agent.is_first_login,
            'user_is_active': user.is_active,
            'agent_is_active': agent.is_active
        }, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_favorite_view(request):
    """
    Toggle favorite status for a user profile
    POST /api/admin-dashboard/user-profiles/toggle-favorite/

    Request:
    {
        "profile_id": 123
    }
    """
    # Check permissions
    if request.user.role not in [User.Role.ADMIN, User.Role.SUPERADMIN]:
        return Response({'error': 'Admin or SuperAdmin access required'}, status=status.HTTP_403_FORBIDDEN)

    profile_id = request.data.get('profile_id')
    if not profile_id:
        return Response({'error': 'profile_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get profile with company filtering
        if request.user.role == User.Role.SUPERADMIN:
            profile = UserProfile.objects.get(id=profile_id)
        else:
            profile = UserProfile.objects.get(id=profile_id, company_id=request.user.company_id)

        # Toggle favorite status
        profile.is_favorite = not profile.is_favorite
        profile.save()

        return Response({
            'message': f'Profile {"added to" if profile.is_favorite else "removed from"} favorites',
            'is_favorite': profile.is_favorite
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found or access denied'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_user_profiles_view(request):
    """
    Clear all non-favorite user profiles for the company
    POST /api/admin-dashboard/user-profiles/clear-non-favorites/

    Response:
    {
        "message": "Cleared 25 non-favorite profiles",
        "deleted_count": 25,
        "remaining_count": 5
    }
    """
    # Check permissions
    if request.user.role not in [User.Role.ADMIN, User.Role.SUPERADMIN]:
        return Response({'error': 'Admin or SuperAdmin access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        # Get profiles to delete (non-favorites only)
        if request.user.role == User.Role.SUPERADMIN:
            profiles_to_delete = UserProfile.objects.filter(is_favorite=False)
            remaining_profiles = UserProfile.objects.filter(is_favorite=True)
        else:
            profiles_to_delete = UserProfile.objects.filter(
                company_id=request.user.company_id,
                is_favorite=False
            )
            remaining_profiles = UserProfile.objects.filter(
                company_id=request.user.company_id,
                is_favorite=True
            )

        deleted_count = profiles_to_delete.count()
        remaining_count = remaining_profiles.count()

        # Delete non-favorite profiles
        profiles_to_delete.delete()

        return Response({
            'message': f'Cleared {deleted_count} non-favorite profiles',
            'deleted_count': deleted_count,
            'remaining_count': remaining_count
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to clear profiles: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def dashboard_stats_view(request):
    """
    Get admin dashboard statistics
    GET /api/admin-dashboard/dashboard-stats/

    Returns:
    {
        "pending_sessions": 5,
        "active_sessions": 12,
        "total_agents": 8,
        "online_agents": 6,
        "total_users": 150,
        "today_conversations": 25
    }
    """
    try:
        from django.db.models import Count
        from datetime import datetime, timedelta
        from human_handoff.models import HumanHandoffSession
        from chatbot.models import UserProfile, ChatSession

        # Get company filter (use TEST001 for testing)
        if request.user.is_authenticated and hasattr(request.user, 'company_id'):
            company_id = request.user.company_id
        else:
            company_id = 'TEST001'  # Default for testing

        # Session counts
        pending_sessions = HumanHandoffSession.objects.filter(
            agent__isnull=True,  # Not assigned yet
            resolved_at__isnull=True,  # Not resolved yet
            chat_session__company_id=company_id
        ).count()

        active_sessions = HumanHandoffSession.objects.filter(
            agent__isnull=False,  # Assigned to an agent
            resolved_at__isnull=True,  # Not resolved yet
            chat_session__company_id=company_id
        ).count()

        # Agent counts
        total_agents = Agent.objects.filter(company_id=company_id).count()
        online_agents = Agent.objects.filter(
            status__in=['AVAILABLE', 'BUSY'],
            company_id=company_id
        ).count()

        # User counts
        total_users = UserProfile.objects.filter(company_id=company_id).count()

        # Today's conversations
        today = datetime.now().date()
        today_conversations = ChatSession.objects.filter(
            created_at__date=today,
            company_id=company_id
        ).count()

        return Response({
            'pending_sessions': pending_sessions,
            'active_sessions': active_sessions,
            'total_agents': total_agents,
            'online_agents': online_agents,
            'total_users': total_users,
            'today_conversations': today_conversations
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get dashboard stats: {str(e)}',
            'pending_sessions': 0,
            'active_sessions': 0,
            'total_agents': 0,
            'online_agents': 0,
            'total_users': 0,
            'today_conversations': 0
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_agents_view(request):
    """
    Get list of available agents for assignment
    GET /api/admin-dashboard/available-agents/

    Returns:
    [
        {
            "id": 1,
            "name": "Agent Name",
            "email": "agent@company.com",
            "status": "AVAILABLE"
        }
    ]
    """
    # Check permissions
    if request.user.role not in [User.Role.ADMIN, User.Role.SUPERADMIN]:
        return Response({'error': 'Admin or SuperAdmin access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        # Get company filter
        company_filter = {}
        if request.user.role == User.Role.ADMIN:
            company_filter['company_id'] = request.user.company_id

        # Get available agents
        agents = Agent.objects.filter(
            status__in=['AVAILABLE', 'BUSY'],
            **company_filter
        ).values('id', 'name', 'email', 'status')

        return Response(list(agents), status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get available agents: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def assign_session_view(request):
    """
    Assign a pending session to an agent
    POST /api/admin-dashboard/assign-session/

    Request:
    {
        "session_id": 123,
        "agent_id": 456
    }
    """
    try:
        session_id = request.data.get('session_id')
        agent_id = request.data.get('agent_id')

        if not session_id or not agent_id:
            return Response({
                'error': 'session_id and agent_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the handoff session
        from human_handoff.models import HumanHandoffSession
        handoff_session = HumanHandoffSession.objects.filter(
            id=session_id,
            agent__isnull=True,  # Not assigned yet
            resolved_at__isnull=True  # Not resolved yet
        ).first()

        if not handoff_session:
            return Response({
                'error': 'Pending session not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get the agent
        agent = Agent.objects.filter(id=agent_id, status='AVAILABLE').first()
        if not agent:
            return Response({
                'error': 'Available agent not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Assign the session
        with transaction.atomic():
            handoff_session.agent = agent
            handoff_session.save()

            # Update agent status to BUSY
            agent.set_busy()

        return Response({
            'message': 'Session assigned successfully',
            'session_id': session_id,
            'agent_name': agent.name
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to assign session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def pending_sessions_view(request):
    """
    Get list of pending sessions for admin dashboard
    GET /api/admin-dashboard/pending-sessions/
    """
    try:
        # Get company filter
        if request.user.is_authenticated and hasattr(request.user, 'company_id'):
            company_id = request.user.company_id
        else:
            company_id = 'TEST001'  # Default for testing

        from human_handoff.models import HumanHandoffSession
        from chatbot.models import UserProfile

        # Get pending sessions for the company (unassigned sessions)
        pending_sessions = HumanHandoffSession.objects.filter(
            agent__isnull=True,  # Not assigned to any agent yet
            resolved_at__isnull=True,  # Not resolved yet
            chat_session__company_id=company_id
        ).select_related('chat_session').order_by('escalated_at')

        sessions_data = []
        for session in pending_sessions:
            # Get user profile for this session
            profile = UserProfile.objects.filter(
                session_id=session.chat_session.session_id
            ).first()

            sessions_data.append({
                'id': session.id,
                'session_id': session.chat_session.session_id,
                'user_name': profile.name if profile else 'Unknown User',
                'user_phone': profile.phone if profile else 'N/A',
                'message': session.escalation_reason or 'Human assistance requested',
                'priority': session.priority,
                'created_at': session.escalated_at.isoformat(),
                'waiting_time': str(timezone.now() - session.escalated_at)
            })

        return Response(sessions_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get pending sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def delete_agent_view(request, agent_id):
    """
    Delete an agent
    DELETE /api/admin-dashboard/delete-agent/{agent_id}/
    """
    # DEAD CODE REMOVED - Debug prints removed for cleaner production code

    try:
        agent = Agent.objects.get(id=agent_id)
        # Delete the associated user as well
        user = agent.user

        # Use transaction to ensure both are deleted together
        with transaction.atomic():
            agent.delete()
            user.delete()

        return Response({
            'message': 'Agent deleted successfully'
        }, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        # DEAD CODE REMOVED - Debug print removed
        return Response({
            'error': 'Agent not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # DEAD CODE REMOVED - Debug print removed
        return Response({
        'error': f'Failed to delete agent: {str(e)}'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== AGENT DASHBOARD APIs ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_dashboard_stats_view(request):
    """
    Get agent dashboard statistics
    GET /api/agent-dashboard/stats/
    """
    try:
        agent = Agent.objects.get(user=request.user)

        from human_handoff.models import HumanHandoffSession

        # Get sessions assigned to this agent
        assigned_sessions = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=True
        )

        # Get today's handled sessions
        from datetime import datetime
        today = datetime.now().date()
        today_handled = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__date=today
        ).count()

        # Get all time handled sessions
        all_time_handled = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=False
        ).count()

        return Response({
            'pending_sessions': 0,  # Agents don't see pending sessions
            'my_active_sessions': assigned_sessions.count(),
            'total_handled_today': today_handled,
            'total_handled_all_time': all_time_handled,
            'agent_status': agent.status
        })

    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_pending_sessions_view(request):
    """
    Get sessions assigned to this agent (pending sessions for agent)
    GET /api/agent-dashboard/pending-sessions/
    """
    try:
        agent = Agent.objects.get(user=request.user)

        from human_handoff.models import HumanHandoffSession
        from chatbot.models import UserProfile

        # Get sessions assigned to this agent but not resolved
        assigned_sessions = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=True
        ).select_related('chat_session').order_by('escalated_at')

        sessions_data = []
        for session in assigned_sessions:
            # Get user profile for this session
            profile = UserProfile.objects.filter(
                session_id=session.chat_session.session_id
            ).first()

            sessions_data.append({
                'id': session.id,
                'session_id': session.chat_session.session_id,
                'user_name': profile.name if profile else 'Unknown User',
                'user_phone': profile.phone if profile else 'N/A',
                'message': session.escalation_reason or 'Human assistance requested',
                'priority': session.priority.upper(),
                'created_at': session.escalated_at.isoformat(),
                'waiting_time': str(timezone.now() - session.escalated_at)
            })

        return Response(sessions_data, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily for debugging
def debug_company_isolation_view(request):
    """
    Debug endpoint to check company isolation
    GET /api/admin-dashboard/debug-company-isolation/
    """
    from authentication.models import User

    # Get all users and their company_ids
    users_data = []
    for user in User.objects.all():
        users_data.append({
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'company_id': user.company_id,
            'is_active': user.is_active
        })

    # Get all agents and their company_ids
    agents_data = []
    for agent in Agent.objects.all():
        agents_data.append({
            'id': agent.id,
            'name': agent.name,
            'email': agent.email,
            'company_id': agent.company_id,
            'user_company_id': agent.user.company_id if agent.user else None,
            'is_active': agent.is_active
        })

    return Response({
        'users': users_data,
        'agents': agents_data,
        'message': 'Company isolation debug data'
    })


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily for debugging
def fix_agent_status_view(request):
    """
    Fix agent status for existing agents
    POST /api/admin-dashboard/fix-agent-status/
    """
    try:
        # Update all agents who have is_first_login=True to PENDING status
        agents_updated = Agent.objects.filter(is_first_login=True).update(status='PENDING')

        # Update all agents who have is_first_login=False but status=AVAILABLE to OFFLINE
        agents_offline = Agent.objects.filter(is_first_login=False, status='AVAILABLE').update(status='OFFLINE')

        return Response({
            'message': 'Agent status fixed successfully',
            'agents_set_to_pending': agents_updated,
            'agents_set_to_offline': agents_offline
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_send_message_view(request):
    """
    Agent sends message to chatbot user
    POST /api/admin-dashboard/agent-send-message/

    Request:
    {
        "session_id": "session_uuid",
        "message": "Hello, how can I help you?"
    }
    """
    try:
        agent = Agent.objects.get(user=request.user)
        session_id = request.data.get('session_id')
        message = request.data.get('message')

        if not session_id or not message:
            return Response({'error': 'session_id and message are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify agent has access to this session
        from human_handoff.models import HumanHandoffSession
        from chatbot.models import ChatSession, ChatMessage

        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
            handoff_session = HumanHandoffSession.objects.get(
                chat_session=chat_session,
                agent=agent
            )
        except (ChatSession.DoesNotExist, HumanHandoffSession.DoesNotExist):
            return Response({'error': 'Session not found or not assigned to you'}, status=status.HTTP_404_NOT_FOUND)

        # Save message to database
        ChatMessage.objects.create(
            session=chat_session,
            message_type='agent',
            content=message,
            metadata={'agent_id': agent.id, 'agent_name': agent.name}
        )

        # Send message to chatbot user via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{chat_session.company_id}_{session_id}',
                    {
                        'type': 'agent_message',
                        'data': {
                            'message': message,
                            'agent_name': agent.name,
                            'timestamp': str(timezone.now()),
                            'session_id': session_id
                        }
                    }
                )
                print(f"DEBUG: Sent agent message to user in session {session_id}")
            except Exception as e:
                print(f"DEBUG: Error sending message via WebSocket: {e}")

        return Response({
            'message': 'Message sent successfully',
            'session_id': session_id
        })

    except Agent.DoesNotExist:
        return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrSuperAdmin])
def request_plan_upgrade(request):
    """
    Allow admin users to request a plan upgrade.
    The request will be sent to superadmin for approval.
    """
    # Only Admin users can request upgrades (SuperAdmin doesn't need to)
    if request.user.role == User.Role.SUPERADMIN:
        return Response({
            'error': 'Superadmin users have unlimited access and do not need plan upgrades'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.role != User.Role.ADMIN:
        return Response({
            'error': 'Only admin users can request plan upgrades'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if there's already a pending request for this company
    existing_request = PlanUpgradeRequest.objects.filter(
        company_id=request.user.company_id,
        status='PENDING'
    ).first()
    
    if existing_request:
        return Response({
            'error': f'You already have a pending upgrade request to {existing_request.requested_plan} plan. Please wait for approval or contact support.',
            'existing_request': PlanUpgradeRequestSerializer(existing_request).data
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = PlanUpgradeRequestCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        upgrade_request = serializer.save()
        
        # TODO: Send notification to superadmin users
        # This could be email, websocket notification, etc.
        
        return Response({
            'message': 'Plan upgrade request submitted successfully',
            'request': PlanUpgradeRequestSerializer(upgrade_request).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrSuperAdmin])
def cancel_plan_upgrade(request):
    """
    Allow admin users to cancel their pending plan upgrade request.
    POST /api/admin-dashboard/cancel-plan-upgrade/
    """
    # Only Admin users can cancel their own requests
    if request.user.role != User.Role.ADMIN:
        return Response({
            'error': 'Only admin users can cancel plan upgrade requests'
        }, status=status.HTTP_403_FORBIDDEN)

    # Find the pending request for this company
    pending_request = PlanUpgradeRequest.objects.filter(
        company_id=request.user.company_id,
        status='PENDING'
    ).first()

    if not pending_request:
        return Response({
            'error': 'No pending upgrade request found for your company'
        }, status=status.HTTP_404_NOT_FOUND)

    # Cancel the request
    pending_request.status = 'CANCELLED'
    pending_request.review_notes = 'Cancelled by admin user'
    pending_request.reviewed_at = timezone.now()
    pending_request.reviewed_by = request.user
    pending_request.save()

    return Response({
        'message': 'Plan upgrade request cancelled successfully',
        'cancelled_request': PlanUpgradeRequestSerializer(pending_request).data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminOrSuperAdmin])
def get_my_plan_upgrade_status(request):
    """
    Get the current user's pending plan upgrade request status.
    GET /api/admin-dashboard/my-plan-upgrade-status/
    """
    # Only Admin users need to check their status
    if request.user.role != User.Role.ADMIN:
        return Response({
            'has_pending_request': False,
            'requested_plan': None
        }, status=status.HTTP_200_OK)

    # Find the pending request for this company
    pending_request = PlanUpgradeRequest.objects.filter(
        company_id=request.user.company_id,
        status='PENDING'
    ).first()

    if pending_request:
        return Response({
            'has_pending_request': True,
            'requested_plan': pending_request.requested_plan,
            'request_details': PlanUpgradeRequestSerializer(pending_request).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'has_pending_request': False,
            'requested_plan': None
        }, status=status.HTTP_200_OK)


# ==================== PLAN UPGRADE MANAGEMENT APIs (SuperAdmin Only) ====================

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def get_plan_upgrade_requests(request):
    """
    Get all plan upgrade requests for SuperAdmin review
    GET /api/admin-dashboard/plan-upgrade-requests/
    """
    try:
        requests_queryset = PlanUpgradeRequest.objects.select_related(
            'requested_by'
        ).all().order_by('-requested_at')
        
        serializer = PlanUpgradeRequestSerializer(requests_queryset, many=True)
        return Response({
            'requests': serializer.data,
            'total': requests_queryset.count(),
            'pending': requests_queryset.filter(status='PENDING').count(),
            'approved': requests_queryset.filter(status='APPROVED').count(),
            'declined': requests_queryset.filter(status='DECLINED').count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch upgrade requests: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def review_plan_upgrade_request(request, request_id):
    """
    Approve or decline a plan upgrade request
    POST /api/admin-dashboard/plan-upgrade-requests/{request_id}/review/
    
    Body:
    {
        "action": "approve" | "decline",
        "notes": "Optional review notes"
    }
    """
    try:
        upgrade_request = PlanUpgradeRequest.objects.select_related('requested_by').get(
            id=request_id,
            status='PENDING'
        )
    except PlanUpgradeRequest.DoesNotExist:
        return Response({
            'error': 'Plan upgrade request not found or already processed'
        }, status=status.HTTP_404_NOT_FOUND)
    
    action = request.data.get('action')
    notes = request.data.get('notes', '')
    
    if action not in ['approve', 'decline']:
        return Response({
            'error': 'Action must be either "approve" or "decline"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Update the request status
            upgrade_request.status = 'APPROVED' if action == 'approve' else 'DECLINED'
            upgrade_request.reviewed_by = request.user
            upgrade_request.reviewed_at = timezone.now()
            upgrade_request.review_notes = notes
            upgrade_request.save()
            
            if action == 'approve':
                # Update the user's plan assignment
                success = update_user_plan(upgrade_request)
                if not success:
                    # Rollback the request status if plan update failed
                    upgrade_request.status = 'PENDING'
                    upgrade_request.reviewed_by = None
                    upgrade_request.reviewed_at = None
                    upgrade_request.review_notes = ''
                    upgrade_request.save()
                    
                    return Response({
                        'error': 'Failed to update user plan. Request remains pending.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                message = f'Plan upgrade request approved successfully. Company {upgrade_request.company_id} has been upgraded to {upgrade_request.requested_plan} plan.'
            else:
                message = f'Plan upgrade request declined. Reason: {notes}'
            
            # Return updated request data
            serializer = PlanUpgradeRequestSerializer(upgrade_request)
            return Response({
                'message': message,
                'request': serializer.data
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': f'Failed to process request: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def update_user_plan(upgrade_request):
    """
    Helper function to update user's plan assignment when upgrade is approved
    """
    try:
        from authentication.models import Plan, UserPlanAssignment
        from chatbot.models import Plan as ChatbotPlan

        # Get the requested plan from chatbot.Plan (the source of truth)
        try:
            chatbot_plan = ChatbotPlan.objects.get(name=upgrade_request.requested_plan, is_active=True)
        except ChatbotPlan.DoesNotExist:
            print(f"Chatbot plan not found: {upgrade_request.requested_plan}")
            return False

        # Map plan name to authentication model format
        plan_name_mapping = {
            'Bronze': 'bronze',
            'Silver': 'silver',
            'Gold': 'gold',
            'Platinum': 'platinum',
            'Diamond': 'diamond',
            'Custom': 'custom'
        }

        plan_name_db = plan_name_mapping.get(upgrade_request.requested_plan)
        if not plan_name_db:
            print(f"Unknown plan name: {upgrade_request.requested_plan}")
            return False

        # Get or create the plan for this company using chatbot plan data
        plan, created = Plan.objects.get_or_create(
            plan_name=plan_name_db,
            company_name=upgrade_request.company_id,
            defaults={
                'max_agents': int(chatbot_plan.max_agents) if chatbot_plan.max_agents.isdigit() else 2,
                'price': chatbot_plan.price if chatbot_plan.price else 0,
                'is_active': True
            }
        )
        
        # Update existing active assignment to 'upgraded' status
        UserPlanAssignment.objects.filter(
            user=upgrade_request.requested_by,
            status='active'
        ).update(
            status='upgraded',
            notes=f'Upgraded to {upgrade_request.requested_plan} plan on {timezone.now().date()}'
        )
        
        # Create new plan assignment
        new_assignment = UserPlanAssignment.objects.create(
            user=upgrade_request.requested_by,
            plan=plan,
            status='active',
            notes=f'Plan upgraded from admin request ID: {upgrade_request.id}'
        )

        # Update CompanyPlan to sync with the new assignment
        from chatbot.models import CompanyPlan, Plan as ChatbotPlan
        try:
            company_plan = CompanyPlan.objects.get(company_id=upgrade_request.company_id)
            # Find corresponding chatbot plan (case-insensitive)
            chatbot_plan_updated = ChatbotPlan.objects.filter(name__icontains=upgrade_request.requested_plan).first()
            if chatbot_plan_updated:
                company_plan.current_plan = chatbot_plan_updated
                company_plan.is_active = True
                company_plan.save()
                print(f"Updated CompanyPlan for {upgrade_request.company_id} to {chatbot_plan_updated.name}")
        except CompanyPlan.DoesNotExist:
            # Create new CompanyPlan if it doesn't exist
            chatbot_plan_updated = ChatbotPlan.objects.filter(name__icontains=upgrade_request.requested_plan).first()
            if chatbot_plan_updated:
                CompanyPlan.objects.create(
                    company_id=upgrade_request.company_id,
                    current_plan=chatbot_plan_updated,
                    is_active=True
                )
                print(f"Created new CompanyPlan for {upgrade_request.company_id} with {chatbot_plan_updated.name}")

        print(f"Successfully updated plan for user {upgrade_request.requested_by.username} to {upgrade_request.requested_plan}")
        return True
        
    except Exception as e:
        print(f"Error updating user plan: {str(e)}")
        return False


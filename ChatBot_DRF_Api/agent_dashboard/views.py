from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from datetime import datetime, timedelta
from admin_dashboard.models import Agent
from human_handoff.models import HumanHandoffSession
from chatbot.models import ChatSession, UserProfile
from authentication.models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_profile_view(request):
    """
    Get current agent's profile information
    GET /api/agent-dashboard/profile/

    Returns:
    {
        "id": 46,
        "name": "Agent Name",
        "email": "agent@example.com",
        "status": "AVAILABLE",
        "company_id": "COMP_123"
    }
    """
    # Check if user is an agent
    if request.user.role != User.Role.AGENT:
        return Response({'error': 'Agent access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        agent = request.user.agent_profile
        return Response({
            'id': agent.id,
            'name': agent.name,
            'email': agent.email,
            'status': agent.status,
            'company_id': agent.company_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get agent profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_stats_view(request):
    """
    Get agent dashboard statistics
    GET /api/agent-dashboard/stats/

    Returns:
    {
        "pending_sessions": 3,
        "my_active_sessions": 2,
        "total_handled_today": 5,
        "total_handled_all_time": 25,
        "agent_status": "AVAILABLE"
    }
    """
    # Check if user is an agent
    if request.user.role != User.Role.AGENT:
        return Response({'error': 'Agent access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        agent = request.user.agent_profile

        # Pending sessions assigned to this agent
        pending_sessions = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=True  # Not resolved yet
        ).count()

        # Active sessions for this agent
        my_active_sessions = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=True  # Not resolved yet
        ).count()

        # Today's completed sessions
        today = datetime.now().date()
        total_handled_today = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__date=today
        ).count()

        # All time completed sessions
        total_handled_all_time = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=False  # Resolved sessions
        ).count()

        return Response({
            'pending_sessions': pending_sessions,
            'my_active_sessions': my_active_sessions,
            'total_handled_today': total_handled_today,
            'total_handled_all_time': total_handled_all_time,
            'agent_status': agent.status
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get agent stats: {str(e)}',
            'pending_sessions': 0,
            'my_active_sessions': 0,
            'total_handled_today': 0,
            'total_handled_all_time': 0,
            'agent_status': 'OFFLINE'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_pending_sessions_view(request):
    """
    Get pending sessions that can be accepted by agents (unassigned sessions)
    GET /api/agent-dashboard/pending-sessions/

    Returns:
    [
        {
            "id": 1,
            "session_id": "sess_123",
            "user_name": "John Doe",
            "user_phone": "+1234567890",
            "message": "I need help with...",
            "priority": "HIGH",
            "created_at": "2025-08-27T10:00:00Z",
            "waiting_time": "5 minutes"
        }
    ]
    """
    # Check if user is an agent
    if request.user.role != User.Role.AGENT:
        return Response({'error': 'Agent access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        agent = request.user.agent_profile

        # Get unassigned sessions for this agent's company (pending sessions)
        sessions = HumanHandoffSession.objects.filter(
            agent__isnull=True,  # Not assigned to any agent yet
            resolved_at__isnull=True,  # Not resolved yet
            chat_session__company_id=agent.company_id  # Same company as agent
        ).select_related('chat_session').order_by('escalated_at')  # FIFO order

        session_data = []
        for session in sessions:
            # Get user profile for this session
            profile = UserProfile.objects.filter(
                session_id=session.chat_session.session_id
            ).first()
            
            # Calculate waiting time
            waiting_time = datetime.now() - session.escalated_at.replace(tzinfo=None)
            waiting_minutes = int(waiting_time.total_seconds() / 60)

            if waiting_minutes < 60:
                waiting_time_str = f"{waiting_minutes} minutes"
            else:
                waiting_hours = waiting_minutes // 60
                remaining_minutes = waiting_minutes % 60
                waiting_time_str = f"{waiting_hours}h {remaining_minutes}m"

            session_data.append({
                'id': session.id,
                'session_id': session.chat_session.session_id,
                'user_name': profile.name if profile else 'Unknown User',
                'user_phone': profile.phone if profile else 'N/A',
                'message': session.escalation_reason or 'No message',
                'priority': session.priority,
                'created_at': session.escalated_at.isoformat(),
                'waiting_time': waiting_time_str
            })

        return Response(session_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get pending sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_active_sessions_view(request):
    """
    Get active sessions for the current agent
    GET /api/agent-dashboard/active-sessions/

    Returns:
    [
        {
            "id": 1,
            "session_id": "sess_123",
            "user_name": "John Doe",
            "user_phone": "+1234567890",
            "last_message": "Thank you for your help",
            "started_at": "2025-08-27T10:00:00Z",
            "message_count": 15
        }
    ]
    """
    # Check if user is an agent
    if request.user.role != User.Role.AGENT:
        return Response({'error': 'Agent access required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        agent = request.user.agent_profile

        # Get active sessions for this agent
        sessions = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=True  # Not resolved yet
        ).select_related('chat_session').order_by('-escalated_at')

        session_data = []
        for session in sessions:
            # Get user profile for this session
            profile = UserProfile.objects.filter(
                session_id=session.chat_session.session_id
            ).first()
            
            # Get message count (this would need to be implemented based on your chat message model)
            message_count = 0  # Placeholder - implement based on your chat message model

            session_data.append({
                'id': session.id,
                'session_id': session.chat_session.session_id,
                'user_name': profile.name if profile else 'Unknown User',
                'user_phone': profile.phone if profile else 'N/A',
                'last_message': session.escalation_reason or 'No messages yet',
                'started_at': session.escalated_at.isoformat(),
                'message_count': message_count
            })

        return Response(session_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get active sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_session_view(request):
    """
    Accept a pending session (assigns unassigned session to the agent)
    POST /api/agent-dashboard/accept-session/

    Request:
    {
        "session_id": 123
    }
    """
    # Check if user is an agent
    if request.user.role != User.Role.AGENT:
        return Response({'error': 'Agent access required'}, status=status.HTTP_403_FORBIDDEN)

    session_id = request.data.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        agent = request.user.agent_profile

        # Get an unassigned session (pending session)
        session = HumanHandoffSession.objects.get(
            id=session_id,
            agent__isnull=True,  # Not assigned to any agent yet
            resolved_at__isnull=True  # Not resolved yet
        )

        # Assign the session to this agent
        session.agent = agent
        session.save()

        # Update agent status to BUSY
        agent.status = 'BUSY'
        agent.save()

        return Response({
            'message': 'Session accepted successfully',
            'session_id': session.chat_session.session_id
        }, status=status.HTTP_200_OK)

    except HumanHandoffSession.DoesNotExist:
        return Response({'error': 'Session not found or already assigned'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to accept session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_session_view(request):
    """
    Complete an active session
    POST /api/agent-dashboard/complete-session/

    Request:
    {
        "session_id": 123
    }
    """
    # Check if user is an agent
    if request.user.role != User.Role.AGENT:
        return Response({'error': 'Agent access required'}, status=status.HTTP_403_FORBIDDEN)

    session_id = request.data.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        agent = request.user.agent_profile

        # Get the session
        session = HumanHandoffSession.objects.get(
            id=session_id,
            agent=agent,
            resolved_at__isnull=True  # Not resolved yet
        )

        # Complete the session
        from django.utils import timezone
        session.resolved_at = timezone.now()
        session.save()

        # Check if agent has other active sessions
        other_active_sessions = HumanHandoffSession.objects.filter(
            agent=agent,
            resolved_at__isnull=True  # Not resolved yet
        ).count()

        # If no other active sessions, set agent status to AVAILABLE
        if other_active_sessions == 0:
            agent.status = 'AVAILABLE'
            agent.save()

        return Response({
            'message': 'Session completed successfully',
            'session_id': session.chat_session.session_id
        }, status=status.HTTP_200_OK)

    except HumanHandoffSession.DoesNotExist:
        return Response({'error': 'Session not found or not assigned to you'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to complete session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
ASGI config for auth_system project.
"""

import os

# Configure Django settings first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Initialize Django ASGI app
django_asgi_app = get_asgi_application()

# Import your app routing AFTER settings + Django app init
from chatbot import routing as chatbot_routing
from human_handoff import routing as handoff_routing

# Combine all WebSocket URL patterns
websocket_urlpatterns = (
    chatbot_routing.websocket_urlpatterns +
    handoff_routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

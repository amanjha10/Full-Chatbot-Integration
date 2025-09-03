"""
URL configuration for auth_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/admin-dashboard/', include('admin_dashboard.urls')),
    path('api/agent-dashboard/', include('agent_dashboard.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    path('api/human-handoff/', include('human_handoff.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
URL configuration for auth_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from chatbot import views as chatbot_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/admin-dashboard/', include('admin_dashboard.urls')),
    path('api/agent-dashboard/', include('agent_dashboard.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    path('api/human-handoff/', include('human_handoff.urls')),
    # Unified file sharing endpoints
    path('api/chat/upload/', chatbot_views.file_upload_view, name='unified_file_upload'),
    path('api/chat/files/', chatbot_views.file_list_view, name='unified_file_list'),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files from STATICFILES_DIRS during development
    from django.contrib.staticfiles.views import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve),
    ]

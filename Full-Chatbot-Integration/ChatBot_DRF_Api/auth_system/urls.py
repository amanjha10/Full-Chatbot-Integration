"""
URL configuration for auth_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from chatbot import views as chatbot_views
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import os
from django.urls import re_path

@csrf_exempt
def serve_static_file(request, filename=None, path=None, is_media=False):
    """Simple static and media file serving for development"""
    if is_media and path:
        # Serving media files
        file_path = os.path.join(settings.MEDIA_ROOT, path)
    elif filename:
        # Serving static files
        file_path = os.path.join(settings.BASE_DIR, 'static', filename)
    else:
        raise Http404("Invalid file request")

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("File not found")

@csrf_exempt
def serve_media_file(request, path):
    return serve_static_file(request, path=path, is_media=True)

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
    # Static file serving
    path('static/<str:filename>', serve_static_file, name='serve_static'),
    # Media file serving
    re_path(r'^media/(?P<path>.*)$', serve_media_file, name='serve_media'),
]

# Serve media and static files during development
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

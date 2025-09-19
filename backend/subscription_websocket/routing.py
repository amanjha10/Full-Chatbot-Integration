from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/subscription/(?P<company_id>\w+)/$', consumers.SubscriptionStatusConsumer.as_asgi()),
]

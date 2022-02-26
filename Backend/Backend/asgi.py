# mysite/asgi.py
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import Backend.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Backend.settings")

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            Backend.routing.websocket_urlpatterns
        )
    ),
})
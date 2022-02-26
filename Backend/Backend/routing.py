from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/service/<str:group>/', consumers.ServiceConsumer.as_asgi())
]
# chat/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ServiceConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name  = self.scope['url_route']['kwargs']['group']
        self.shared_group_name = f'group_{self.group_name}'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.shared_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.shared_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        server = text_data_json['server']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.shared_group_name,
            {
                'type': 'service_update',
                'message': message,
                'server' : server
            }
        )

    # Receive message from room group
    def service_update(self, event):
        message = event['message']
        server = event['server']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'server' : server
        }))
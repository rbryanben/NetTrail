from email.mime import application
import imp
from xml.parsers.expat import model
from rest_framework import serializers
from .models import *

class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = ['id','last_known_ip','user_defined_name','color_tag','hostname','log_count']

class ServerLogSerializer(serializers.ModelSerializer):
    server = ServerSerializer()
    class Meta:
        model = ServerLog
        fields = ['id','src_ip','dest_ip','src_mac','dst_mac','protocol','ttl','time_local','time_received','server']     

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id','color_tag','url_path','user_defined_name','log_count']     

class UserDefinedLogSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(many=True)
    class Meta:
        model = UserDefinedLog
        fields = ['failed_message','failed_code','success_message','success_code','route_path','method','user_defined_name','application']     

class TCPLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCPLog
        fields = ['path','uid_got','status','time_local','user_agent','ip','remote_user','http_reference','request','body_bytes_sent']     
import random
from django.db import models


"""
    Returns a random string from the list ["#1abc9c", "#16a085", "#2ecc71", "#27ae60", "#3498db", "#2980b9", "#9b59b6", "#8e44ad", "#34495e", "#2c3e50", "#f1c40f", "#f39c12", "#e67e22", "#d35400", "#e74c3c", "#c0392b", "#ecf0f1"]
"""
def getRandomColor():
    colors = ["#1abc9c", "#16a085", "#2ecc71", "#27ae60", "#3498db", "#2980b9", "#9b59b6", "#8e44ad", "#34495e", "#2c3e50", "#f1c40f", "#f39c12", "#e67e22", "#d35400", "#e74c3c", "#c0392b", "#ecf0f1"]
    return random.choice(colors)
 
class Server(models.Model):
    last_known_ip = models.CharField(max_length=15)
    user_defined_name = models.CharField(max_length=32, unique=True)
    color_tag = models.CharField(max_length=32)
    hostname = models.CharField(max_length=32, unique=True)

    def construct(self,last_known_ip, hostname):
        self.last_known_ip = last_known_ip
        self.user_defined_name = hostname
        self.color_tag = getRandomColor()
        self.hostname = hostname
        self.save()

    @property
    def log_count(self):
        return ServerLog.objects.filter(server=self).count

class ServerLog(models.Model):
    src_ip = models.CharField(max_length=15)
    dest_ip = models.CharField(max_length=15)
    src_mac = models.CharField(max_length=17)
    dst_mac = models.CharField(max_length=17)
    protocol = models.CharField(max_length=5)
    ttl = models.BigIntegerField()
    time_local = models.CharField(max_length=64)
    time_received = models.DateTimeField(auto_now=True)
    server = models.ForeignKey(Server,on_delete=models.CASCADE)
    


    def construct(self,dest_ip,src_ip, protocol, time_local, server_hostname, host_ip):
        self.dest_ip = dest_ip
        self.src_ip = src_ip
        self.protocol = protocol
        self.time_local = time_local
        self.ttl = 100
        # set the server 
        try:
            self.server = Server.objects.get(hostname=server_hostname)
        except Server.DoesNotExist:
            # If server does not exist register it and assign that server
            new_server = Server()
            new_server.construct(host_ip,server_hostname)
            self.server = new_server

        self.save()

class Application(models.Model):
    color_tag = models.CharField(max_length=32)
    url_path = models.CharField(max_length=256)
    user_defined_name = models.CharField(max_length=32)

class UserDefinedLog(models.Model):
    failed_message = models.CharField(max_length=256)
    failed_code = models.IntegerField(default=500)
    success_message = models.CharField(max_length=256)
    success_code = models.IntegerField(default=200)
    route_path = models.CharField(max_length=256)
    method = models.CharField(max_length=6)
    user_defined_name = models.CharField(max_length=64)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)

class TCPLog(models.Model):
    path = models.CharField(max_length=256)
    uid_got = models.CharField(max_length=64)
    status = models.IntegerField()
    time_local = models.CharField(max_length=64)
    user_agent = models.CharField(max_length=64)
    ip = models.CharField(max_length=15)
    remote_user = models.CharField(max_length=64)
    http_reference = models.CharField(max_length=64)
    request = models.CharField(max_length=64)
    body_bytes_sent = models.BigIntegerField()

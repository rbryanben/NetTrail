import imp
from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(TCPLog)
admin.site.register(ServerLog)
admin.site.register(Server)
admin.site.register(Application)
admin.site.register(UserDefinedLog)
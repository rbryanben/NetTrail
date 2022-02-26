# ClientAPI urls.py
from unicodedata import name
from django.urls import path
from .views import *

urlpatterns = [
    path("getServiceStatus",getServiceStatus,name="Get Service Status"),
    path("configureService",configureService,name="Configure Service"),
    path("serverLogsHandler",receiveServerLogs, name="Server Logs Handler"),
    path("getServers",getServers,name="Get Servers"),
    path("getServerLogs",getServerLogs,name="Get Server Logs"),
    path("getApplicationLogs",applicationLogs,name="Application Logs"),
    path("applications",applications_,name="Applications")
]

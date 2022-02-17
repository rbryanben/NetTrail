# ClientAPI urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("getServiceStatus",getServiceStatus,name="Get Service Status"),
    path("configureService",configureService,name="Configure Service")
]

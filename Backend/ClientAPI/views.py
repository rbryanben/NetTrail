from hashlib import new
from telnetlib import STATUS
from urllib.request import Request
import requests
import json
from json.decoder import JSONDecodeError
import os
from posixpath import split
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .serializers import *
from .models import *
from django.utils.datastructures import MultiValueDictKeyError
from asgiref.sync import async_to_sync
from django.core import serializers
from channels.layers import get_channel_layer
from .models import TCPLog
channel_layer = get_channel_layer()

""" Get Service Status

    Checks if there is a conf.d file in the conf folder. And trys to load all the 
    data from the conf.d file. If it fails, the service is configured wrong
"""
def getServiceStatus(request):
    try:
        with open("conf\conf.d","r+") as configFile:
            # Read and load data into a dictionary
            configFileData = configFile.read()
            configurations = json.loads(configFileData)
            # Check if the gateway_application_ip, log_retrival_count and server_log_buffer
            #   are defined
            if (configurations["gateway_application_ip"] == "" or configurations["log_retrival_count"] == "" 
                or configurations["server_log_buffer"] == "" ):
                raise KeyError

            # Server is configured
            return JsonResponse(configurations, safe=False,status=200)

    except FileNotFoundError:
        return HttpResponse("Service Not Configured",status=501)
    except JSONDecodeError:
        return HttpResponse("Invalid Configuration File",status=501)
    except KeyError:
        return HttpResponse("Service Not Configured",status=501)


"""
    Configure Service 

    Checks the data received from the POST method and writes to the conf.d file  
""" 
@csrf_exempt
def configureService(request):
    try:
        configurations = json.loads(request.body)
        # Check Configurations 
        if (configurations["gateway_application_ip"] == "" or configurations["log_retrival_count"] == "" 
                or configurations["server_log_buffer"] == "" ):
                raise JSONDecodeError

        # Write to configuration file 
        with open("conf\conf.d","w+") as configFile:
            # Read and load data into a dictionary
            configFile.write(json.dumps(configurations))

        # Configured
        return JsonResponse(configurations,safe=False,status=200)
    except JSONDecodeError:
        return HttpResponse("Invalid Configuration",status=501)
    except FileNotFoundError:
        os.mkdir(os.getcwd() + "/conf")
        return configureService(request)


"""
    Get Servers

    This request is meant to provide a client application with a list of servers, and carries 1 
    optional parameter server_id. If the server_id is defined, only the server with that id will 
    be returned instead of the entire list. 

    Update

    If the request is update, extract the request body of json to a dictionary. Then check if the key color exists,
    and the key user_defined_name exists.
"""
@csrf_exempt
def getServers(request):
    if (request.method == "GET"):
        try:
            server_id_query = request.GET["server_id"]
            servers = Server.objects.get(id=server_id_query)
            serversSerialized = ServerSerializer(servers)
            return JsonResponse(serversSerialized.data,safe=False,status=200)
        except MultiValueDictKeyError:
            servers = Server.objects.all()
            serversSerialized = ServerSerializer(servers,many=True)
            return JsonResponse(serversSerialized.data,safe=False,status=200)
        except Server.DoesNotExist:
            return HttpResponse("Invalid Server Identification",status=404)
        except:
            return HttpResponse("Internal Server Error",status=500)

    if (request.method == "UPDATE"):
        try:
            updateKeys = json.loads(request.body)
            server = Server.objects.get(id=updateKeys["server_id"])
            if "color" in updateKeys:
                server.color_tag = updateKeys["color"]

            if "user_defined_name" in updateKeys:
                server.user_defined_name = updateKeys["user_defined_name"]

            if "ipv4" in updateKeys:
                server.last_known_ip = updateKeys["ipv4"]
            server.save()
            return HttpResponse("Updated",status=200)
        except MultiValueDictKeyError:
            return JsonResponse(serversSerialized.data,safe=False,status=204)
        except Server.DoesNotExist:
            return HttpResponse("Invalid Server Identification",status=404)


def getServersOptimised(request):
    servers = Server.objects.all()
    serversSerialized = serializers.serialize("json",servers)
    return HttpResponse(serversSerialized,status=200)
    
"""
    Get Server Logs 

    This request is meant to provide a client application with a list of server logs, and carries
    6 optional parameters, server_id, last_log_id, pending_logs, start_time, src_ip, 
    dest_ip, src_mac, log_count. When called without any parameter the server will return 
    the last 1000 logs from all servers combined. 
    The optional parameters are filters that are execute in the order they appeared in the 
    above text. Adding the filter server_id will return the last 1000 logs of the server with 
    that id. Adding last_log will return 1000 logs before the id of the specified log. Adding 
    log_count will return n logs. Adding pending_logs will return the new logs from the 
    specified log id
"""
def getServerLogs(request):
    if (request.method == "GET"):
        # Filters
        server_id = None
        pending_logs = None
        keySet = request.GET

        ## Server id key
        try:
            server_id = keySet["server_id"]
        except:
            pass


        ## pending logs
        try:
            pending_logs = keySet["pending_logs"]
        except:
            pass


        # Apply filters 
        if server_id:
            server_logs = ServerLog.objects.filter(server_id=server_id).order_by("-id")
        else:
            server_logs = ServerLog.objects.all().order_by("-id")
        
        if pending_logs:
            server_logs = server_logs.filter(id__gte=int(pending_logs) + 1).order_by("id")

        serializedLogs =serializers.serialize("json",server_logs,use_natural_foreign_keys=True,use_natural_primary_keys=True)
        return HttpResponse(serializedLogs,status=200)


"""
    Receive Server Logs

    Receives server logs captures them in the database and update to all client applications
"""
@csrf_exempt 
def receiveServerLogs(request):
    # Test Serialization 
    logs = json.loads(request.body)
    lastLog = None
    # Store to the database
    for log in logs:
        logToSave = ServerLog()
        logToSave.construct(log["dest_ip"],log["src_ip"],log["protocol"],log["time_local"],log["hostname"],getClientIp(request))
        lastLog = logToSave
    
    # Return Server Logger Configurations
    try:
        with open("conf\conf.d","r+") as configFile:
                # Read and load data into a dictionary
                configFileData = configFile.read()
                configurations = json.loads(configFileData)
                buffer = configurations["server_log_buffer"]
    except:
        buffer = 50

    # Update All Logs Layer
    async_to_sync(channel_layer.group_send)("group_ServerLogsAll", {
        "type" : "service_update",
        "message" : "new_logs",
        "server" : lastLog.server.id
    })

    return HttpResponse(buffer, status=200)

    
def getClientIp(request):
    x_forwared_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwared_for:
        return x_forwared_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')



def applicationLogs(request):
    configurations = None
    # Write to configuration file 
    with open("conf\conf.d","r+") as configFile:
        # Read and load data into a dictionary
        configurations = json.loads(configFile.read())

    # Get logs and put them into list
    data = requests.get(f'http://{configurations["gateway_application_ip"]}:1885/app.log')
    logsSplitted = data.text.split("#")
    logsSplitted.pop()

    # Create a list of dictionaries
    logs = []

    #iterate logs
    for item in logsSplitted:
        log = json.loads(item)

        # Get Request Tokens
        referrer = log["request"]
        referrer_tokens = referrer.split("/")
        APP_NAME = referrer_tokens[1]
        
        # Default Application 
        APPLICATION = {
            "name" : "Unassigned",
            "color" : "silver"
        }

        # If Application exists set it as the new APPLICATION
        if (len(Application.objects.filter(url_path=APP_NAME)) > 0):
            APPLICATION = Application.objects.get(url_path=APP_NAME).toDictionary()
        
        # Add the application to the log
        log['Application'] = APPLICATION


        # Filter out requests from access log
        if log["request"] != "GET /access.log HTTP/1.1":
            #check if an application is defined
            try:
                application_name = request.GET["Application"]
                if (log["Application"]["path"] == application_name):
                    logs.append(log)
            except MultiValueDictKeyError:
                logs.append(log)
            except:
                pass

    logs.reverse()
    return HttpResponse(json.dumps(logs))


"""
    Returns or update the applications 
"""
@csrf_exempt
def applications_(request):
    if request.method == "GET":
        apps = Application.objects.all()
        serializedApps = ApplicationSerializer(apps,many=True)
        return JsonResponse(serializedApps.data,safe=False,status=200)

    if request.method == "PUT":
        params = json.loads(request.body)
        app = Application.objects.get(id=params["id"])

        if "color" in params:
            app.color_tag = params["color"]
        if 'route' in params:
            app.url_path = params["route"]
        if 'name' in params:
            app.user_defined_name = params["name"]
    
        app.save()
        return HttpResponse(status=200)

    if request.method == "POST":
        params = json.loads(request.body)
        #check if an app with that route exists
        try:
            app = Application.objects.get(url_path=params["route"])   
            return HttpResponse("Exists",status=409)
        except:
            newApp = Application()
            newApp.construct(params["color"],params["route"],params["name"])
            return HttpResponse(status=200)

class ApplicationLog:
    def __init__(self,path,uid_got,status,time_local,user_agent,ip,remote_user,http_reference,request,body_bytes_sent) -> None:
        self.path = path
        self.uid_got = uid_got
        self.status = status
        self.time_local = time_local
        self.user_agent = user_agent
        self.ip = ip
        self.remote_user = remote_user
        self.http_reference = http_reference
        self.request = request
        self.body_bytes_sent = body_bytes_sent

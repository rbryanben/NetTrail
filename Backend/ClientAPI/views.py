from http import server
import pickle
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

    elif (request.method == "UPDATE"):
        try:
            updateKeys = json.loads(request.body)
            server = Server.objects.get(id=updateKeys["server_id"])
            if "color" in updateKeys:
                server.color_tag = updateKeys["color"]
            if "user_defined_name" in updateKeys:
                server.user_defined_name = updateKeys["user_defined_name"]
            server.save()
            return HttpResponse("Updated",status=200)
        except MultiValueDictKeyError:
            return JsonResponse(serversSerialized.data,safe=False,status=204)
        except Server.DoesNotExist:
            return HttpResponse("Invalid Server Identification",status=404)

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
        last_log_id = None
        pending_logs = None
        start_time = None
        src_ip = None
        dest_ip = None
        src_mac = None
        dest_mac = None
        log_count = None

        keySet = request.GET

        ## Server id key
        try:
            server_id = keySet["server_id"]
        except:
            pass

        ## last_log_id 
        try:
            last_log_id = keySet["last_log_id"]
        except:
            pass

        ## pending logs
        try:
            pending_logs = keySet["pending_logs"]
        except:
            pass

        ## start time 
        try:
            start_time = keySet["start_time"]
        except:
            pass
            
        ## src_ip
        try:
            src_ip = keySet["src_ip"]
        except:
            pass

        ## dest_ip
        try:
            dest_ip = keySet["dest_ip"]
        except:
            pass

        ## src_mac
        try:
            src_mac = keySet["src_mac"]
        except:
            pass

        ## dest mac
        try:
            dest_mac = keySet["dest_mac"]
        except:
            pass

        ## log count 
        try:
            log_count = keySet["log_count"]
        except:
            pass

        # Apply filters 
        server_logs = ServerLog.objects.all()

        if server_id:
            server_logs = server_logs.filter(server_id=server_id)
        if last_log_id:
            server_logs = server_logs.filter(id__lte=last_log_id)
        if pending_logs:
            server_logs = server_logs.filter(id__gte=pending_logs)
        if src_ip:
            server_logs = server_logs.filter(src_ip=src_ip)
        if dest_ip:
            server_logs = server_logs.filter(dest_ip=dest_ip)
        if src_mac:
            server_logs = server_logs.filter(src_mac=src_mac)
        if dest_mac:
            server_logs = server_logs.filter(dest_mac=dest_mac)
        if log_count:
            server_logs = server_logs.order_by('-id')[:int(log_count)]

        serializedLogs = ServerLogSerializer(server_logs,many=True)
        return JsonResponse(serializedLogs.data,safe=False,status=200)


"""
    Receive Server Logs

    Receives server logs captures them in the database and update to all client applications
"""
@csrf_exempt 
def receiveServerLogs(request):
    # Test Serialization 
    logs = json.loads(request.body)
    # Store to the database
    for log in logs:
        logToSave = ServerLog()
        logToSave.construct(log["dest_ip"],log["src_ip"],log["protocol"],log["time_local"],log["hostname"],getClientIp(request))
    
    # Return Server Logger Configurations
    try:
        with open("conf\conf.d","r+") as configFile:
                # Read and load data into a dictionary
                configFileData = configFile.read()
                configurations = json.loads(configFileData)
                buffer = configurations["server_log_buffer"]
    except:
        buffer = 50
    return HttpResponse(buffer, status=200)

    
def getClientIp(request):
    x_forwared_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwared_for:
        return x_forwared_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
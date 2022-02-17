import imp
import json
from json.decoder import JSONDecodeError
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

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
        return HttpResponse("Service Not Configured",status=500)
    except JSONDecodeError:
        return HttpResponse("Invalid Configuration File",status=500)
    except KeyError:
        return HttpResponse("Service Not Configured",status=500)


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
        return HttpResponse("Invalid Configuration",status=200)
    except FileNotFoundError:
        os.mkdir(os.getcwd() + "/conf")
        return configureService(request)

    
        
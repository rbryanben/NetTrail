# About NetTrail
Application to log all activity within a network and application stack, for applications that are running on premise. This done by obtaining logs from an Nginx gateway server, network router through sys protocol and traffic inbound to outbound to an individual server by sniffing the network adapter. All built with Python.

# NetTrail Demo 
https://user-images.githubusercontent.com/63599157/163568806-43e56687-c540-4833-b329-b649b0f0b147.mp4


# Network Traffic & Application Log Collection
<img style="height:250px;" src="https://user-images.githubusercontent.com/63599157/163566835-46e54d95-cda6-4604-9699-07c99441f4ac.png"/>

Traffic to a server is collected by a service application called the ServiceLogger. The ServiceLogger watches a given address for inbound and outbound traffic, collects these as a batch and then send to the application service running on the network.
For the application logs, we expose the access.log file for nginx to a certain port, which can be retrieved  by the application server for proccessing.

# Application Architecture
<img style="height:250px;" src="https://user-images.githubusercontent.com/63599157/163566751-b02fe99d-ab67-47c8-9684-8e4b9a9d60be.png"/>


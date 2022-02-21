from email.quoprimime import body_check
import json
import socket
import os
import struct
import textwrap
from ctypes import *
from datetime import datetime
import requests

class ServerLog:
    def __init__(self,dest_ip,src_ip, protocol):
        self.dest_ip = dest_ip
        self.src_ip = src_ip
        self.protocol = protocol
        self.time_local = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")

    def dump(self):
        return {
            "dest_ip" : self.dest_ip,
            "src_ip" : self.src_ip,
            "protocol" : self.protocol,
            "time_local" : self.time_local,
            "hostname" : socket.gethostname()
        }
        
##
#  Windows Section
#
class IP(Structure): 
    _fields_ = [
        ("ihl", c_ubyte, 4),
        ("version", c_ubyte, 4),
        ("tos", c_ubyte),
        ("len", c_ushort),

        ("id", c_ushort),
        ("offset", c_ushort),
        ("ttl", c_ubyte),
        ("protocol_num", c_ubyte),
        ("sum", c_ushort),
        ("src", c_ulong),
        ("dst", c_ulong)
    ]

    def __new__(self, socket_buffer=None):
        return self.from_buffer_copy(socket_buffer) 

    def __init__(self, socket_buffer=None):
        # map protocol constants to their names
        self.protocol_map = {1:"ICMP", 6:"TCP", 17:"UDP"}

        # human readable IP addresses 
        self.src_address = socket.inet_ntoa(struct.pack("<L",self.src)) 
        self.dst_address = socket.inet_ntoa(struct.pack("<L",self.dst))
        # human readable protocol
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)

        

def windowsMain(host,log_buffer,service_application_address):
    #log list
    logs = []
    # socket protocol definition
    socket_protocol = socket.IPPROTO_IP 

    #connection and bind host
    conn = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
    conn.bind((host, 0))

    #include headers 
    conn.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    #turn on RCVALL
    conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    while (True):
        raw_buffer = conn.recvfrom(65565)[0]
        ip_header = IP(raw_buffer[0:20])
        
        # Add To Log
        newLog = ServerLog(ip_header.dst_address,ip_header.src_address,ip_header.protocol)

       
        #
        # Filter Optimsed
        #
        # Filter Local and Mother URLs
        if not (
            newLog.src_ip == newLog.dest_ip or
            newLog.src_ip == service_application_address or
            newLog.dest_ip == service_application_address or
            newLog.src_ip[:3] == '127'):


            # Filter Repeats
            if len(logs) >= 2 :
                
                # Check for repeat 
                lastLog = logs[len(logs) - 2]
                yestLog = logs[len(logs) - 1]

                if  not (lastLog["src_ip"] == newLog.src_ip and lastLog["dest_ip"] == newLog.dest_ip or
                    newLog.src_ip == yestLog["src_ip"]):
                    logs.append(newLog.dump())
                    
                    print(f" Source: {newLog.src_ip} | Destination: {newLog.dest_ip} | Protocol: {ip_header.protocol}" )
                    # Check if the log is equal to the buffer size
                    # and send to mother
                    if len(logs) >= log_buffer:
                        # Send to mother
                        print("Event: Sending Logs to "+service_application_address)
                        try:
                            bufferConfiguration = requests.post(service_application_address + "/api/serverLogsHandler", data=json.dumps(logs))
                            log_buffer = int(bufferConfiguration.text)
                            logs.clear()
                        except:
                            print("Error: Failed To Send Logs.")
                            logs.clear()            
                else:
                    pass
                    
            else:
                print(newLog.src_ip,newLog.dest_ip)
                logs.append(newLog.dump())

##
#   Posix (Linux Ubuntu) 
#
def posixMain(log_buffer,service_application_address):
    # connection 
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3),)
    logs = []
    while (True):
        packet, address = conn.recvfrom(65535)
        # unpack the ethernet header 
        ethernet_header = packet[0:14]
        eth_header = struct.unpack('!6s6s2s', ethernet_header)
        #
        ## Assign the mac addresses, but we dont require this yet
        #

        # unpack the ip header 
        ipheader = packet[14:34]
        ip_header = struct.unpack('!12s4s4s',ipheader)
        sourceIP = socket.inet_ntoa(ip_header[1])
        destinationIP = socket.inet_ntoa(ip_header[2])
        protocol = "TCP"
        
        # Add To Log
        newLog = ServerLog(destinationIP,sourceIP,protocol)

        print(f" Source: {newLog.src_ip} | Destination: {newLog.dest_ip} | Protocol: TCP" )
        
        # Filter Optimsed
        #
        # Filter Local and Mother URLs
        if not (
            newLog.src_ip == newLog.dest_ip or
            newLog.src_ip == service_application_address or
            newLog.dest_ip == service_application_address or
            newLog.src_ip[:3] == '127'):


            # Filter Repeats
            if len(logs) >= 2 :
                
                # Check for repeat 
                lastLog = logs[len(logs) - 2]
                yestLog = logs[len(logs) - 1]

                if  not (lastLog["src_ip"] == newLog.src_ip and lastLog["dest_ip"] == newLog.dest_ip or
                    newLog.src_ip == yestLog["src_ip"]):
                    logs.append(newLog.dump())
                    # Check if the log is equal to the buffer size
                    # and send to mother
                    if len(logs) >= log_buffer:
                        # Send to mother
                        print("Event: Sending Logs to "+service_application_address)
                        try:
                            bufferConfiguration = requests.post(service_application_address + "/api/serverLogsHandler", data=json.dumps(logs))
                            log_buffer = int(bufferConfiguration.text)
                            logs.clear()
                        except:
                            print("Error: Failed To Send Logs.")
                            logs.clear()            
                else:
                    pass
                    
            else:
                print(newLog.src_ip,newLog.dest_ip)
                logs.append(newLog.dump())

#unpack ethernet frame 
def ethernetFrame(data):
    dest_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
    return formatMac(dest_mac), formatMac(src_mac), socket.htons(proto), data[14:]

#format mac
def formatMac(bytesAddress):
    bytesStr = map('{:02x}'.format,bytesAddress)
    return ':'.join(bytesStr).upper()

#unpack ipv4
def IPv4_packet(data):
    version_header_length = data[0]
    version = version_header_length >> 4
    header_length = (version_header_length & 15)* 4 
    ttl, proto, src, src, target = struct.unpack('! 8x B B 2x 4s 4s', data[:20])
    return version, header_length, ttl, proto, ipv4(src), ipv4(target), data[header_length:]

# formats IPv4 address
def ipv4(bytes):
    return '.'.join(map(str,bytes))

# Unpack ICMP packet 
def icmpPacket(data):
    icmp_type, code , checksum = struct.unpack('! B B H', data[:4])
    return icmp_type, code, checksum, data[4:]

# Unpack TCP 
def tcp_segment(data):
    src_port, dest_port, sequence_, acknowledgements, offset_reserved_flags = struct.unpack('! H H L L H', data[:14])
    offset = (offset_reserved_flags >> 12) * 4
    flag_urg = (offset_reserved_flags & 32) >> 5
    flag_ack = (offset_reserved_flags & 16) >> 4
    flag_psh = (offset_reserved_flags & 8) >> 3
    flag_rst = (offset_reserved_flags & 4) >> 2
    flag_syn = (offset_reserved_flags & 2) >> 1
    flag_fin = (offset_reserved_flags & 1) 

    return src_port, dest_port, sequence_, acknowledgements, offset_reserved_flags, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data[offset:]

def udp_segment(data):
    src_port, dest_port, size = struct.unpack('! H H 2x H')
    return src_port, dest_port, size, data[8:]

def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string,bytes):
        string = ''.join(r'\x{:02x}'.format(byte) for byte in string)
        if size % 2:
            size -= 1 
    return '\n'.join([prefix + line for line in textwrap.wrap(string,size)])
  

## Get Configurations
try:    
    with open("conf.d","r") as configurationFileHandle:
        configurationFileData = configurationFileHandle.read()
        configurations = json.loads(configurationFileData)
        hostAddress = configurations["host_address"]
        log_buffer = configurations["log_buffer"]
        service_application = configurations["service_application"]
except FileNotFoundError:
    print("\n\nWarning: Configuration File Not Found (Running Defaults)\n\n")
    hostAddress = socket.gethostbyname(socket.gethostname())
    log_buffer = 50
    service_application = "http://0.0.0.0"
except KeyError:
    print("\n\nWarning: Invalid Configurations (Running Defaults)\n\n")
    hostAddress = socket.gethostbyname(socket.gethostname())
    log_buffer = 50
    service_application = "http://0.0.0.0"
    
## Application Start 
if os.name == 'posix':
    posixMain(log_buffer,service_application)
elif os.name == 'nt':
    try:
        windowsMain(hostAddress, log_buffer,service_application)
    except socket.gaierror:
        print("\n\nError: Invalid Host Address\n\n")

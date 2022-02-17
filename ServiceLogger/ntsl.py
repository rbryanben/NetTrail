from audioop import add
from itertools import count
import socket
import os
import struct
import textwrap
from ctypes import *


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

        

def main(host):
   
    while (True):
        # socket protocol definition
        if os.name == "nt":
            socket_protocol = socket.IPPROTO_IP 
        else:
            socket_protocol = socket.IPPROTO_ICMP

        
        
        #connection and bind host
        conn = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
        conn.bind((host, 0))

        if os.name == "nt":
            conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)

        #include headers 
        conn.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        if os.name == "nt": 
            conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

        raw_buffer = conn.recvfrom(65565)[0]
        ip_header = IP(raw_buffer[0:20])
        print(ip_header.protocol,  ip_header.dst_address, ip_header.src_address)

 
        
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

main("192.168.172.236")
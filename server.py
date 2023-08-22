import socket
from time import sleep

from utils import parse_packet

VPN_SERVER_PORT = 12000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', VPN_SERVER_PORT))

print("Server listening on UDP port", VPN_SERVER_PORT)

while sleep(0.01) is None:
    message, address = server_socket.recvfrom(1024)

    parsed_packet = parse_packet(message)

    print(parsed_packet)

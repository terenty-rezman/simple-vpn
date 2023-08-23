import socket
from time import sleep
from ipaddress import IPv4Address
import asyncio

import websockets

from utils import parse_packet
from tun import TUNInterface

VPN_SERVER_PORT = 12000

# tun interface config
TUN_IF_NAME = "custom-tunnel"
TUN_IF_ADDRESS = '10.1.0.2/24'


async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)


async def ws_server():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever


def udp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', VPN_SERVER_PORT))
    print("Server listening on UDP port", VPN_SERVER_PORT)

    interface = TUNInterface(TUN_IF_NAME, address=IPv4Address(TUN_IF_ADDRESS))

    while sleep(0.01) is None:
        message, address = server_socket.recvfrom(1024)

        parsed_packet = parse_packet(message)

        print(parsed_packet)


if __name__ == "__main__":
    asyncio.run(ws_server())

"""tun.py
*CAP_NET_ADMIN capability is required to create TUN interfaces.*
Based on: https://github.com/povilasb/iptun/blob/master/iptun/tun.py
"""
import logging as LOGGER
import time
from ipaddress import IPv4Address
import re
import time
import socket
import asyncio

import websockets

from utils import run, parse_packet
from tun import TUNInterface

LOGGER.basicConfig(level=LOGGER.DEBUG)

# connect to server
SERVER_ADDR = "38.242.223.247"
SERVER_UDP_PORT = 12000

# tun interface config
TUN_IF_NAME = "custom-tunnel"
TUN_IF_ADDRESS = '10.1.0.1'
    

def setup_route_table(interface_name):
    # enable packet forwarding on host
    run("/usr/sbin/sysctl -w net.ipv4.ip_forward=1");

    # get old gateway ip addr
    old_default_route = run("ip route show 0/0")

    ipv4 = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"
    old_gateway_ip_addr = re.search(ipv4, old_default_route)

    # add route to vpn server through old gateway ip
    run(f"ip route add {SERVER_ADDR} via {old_gateway_ip_addr[0]}")

    # add default route for all trafic through our tun interface
    run(f"ip route add 0/1 dev {interface_name}");
    run(f"ip route add 128/1 dev {interface_name}");


def cleanup_route_table():
    run(f"ip route del {SERVER_ADDR}");
    run("ip route del 0/1");
    run("ip route del 128/1");


def create_udp_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)
    return s


async def test() -> None:
    to_server = create_udp_socket()
    server_addr = (SERVER_ADDR, SERVER_UDP_PORT)

    interface = await TUNInterface(TUN_IF_NAME, address=IPv4Address(TUN_IF_ADDRESS))
    setup_route_table()

    try:
        while True:
            packet = await interface.read(1024)
            parsed_packet = parse_packet(packet)
            print(parsed_packet)
            to_server.sendto(packet, server_addr)

    except KeyboardInterrupt:
        pass
    finally:
        cleanup_route_table()


async def ws_client():
    async with websockets.connect("ws://tech.divid.team:8765") as websocket:
        await websocket.send("Hello world!")
        message = await websocket.recv()
        print(f"Received: {message}")


if __name__ == '__main__':
    asyncio.run(ws_client())

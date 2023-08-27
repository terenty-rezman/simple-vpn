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
from websockets.client import WebSocketClientProtocol
from pypacker.layer3 import ip

from utils import run, parse_packet, print_packet
from tun import create_tun, TUNInterface

LOGGER.basicConfig(level=LOGGER.INFO)

# connect to ws server
#SERVER_ADDR = "wss://tech.divid.team/myvpn"
#SERVER_ADDR = "ws://tech.divid.team:8777"
SERVER_ADDR = "ws://79.143.31.251:8777"

# tun interface config
TUN_IF_NAME = "custom-tunnel"
TUN_IF_ADDRESS = '10.1.0.2/24'


def resolve_ip_address(addr: str):
    # remove scheme
    addr = re.sub("^\w*://", "", addr)
    # remove port
    addr = re.sub(":\d+$", "", addr)
    # resolve if domain name 
    if any(letter.isalpha() for letter in addr):
        addr = socket.gethostbyname_ex(addr)[2][0]
    return addr


def setup_route_table(interface_name, server_ip_addr):
    # enable packet forwarding on host
    run("/usr/sbin/sysctl -w net.ipv4.ip_forward=1");

    # get old gateway ip addr
    old_default_route = run("ip route show 0/0")

    ipv4 = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"
    old_gateway_ip_addr = re.search(ipv4, old_default_route)

    # add route to vpn server through old gateway ip
    run(f"ip route add {server_ip_addr} via {old_gateway_ip_addr[0]}")

    # add default route for all trafic through our tun interface
    run(f"ip route add 0/1 dev {interface_name}");
    run(f"ip route add 128/1 dev {interface_name}");

    run("iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE");
    run("iptables -I FORWARD 1 -i tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT");
    run("iptables -I FORWARD 1 -o tun0 -j ACCEPT");


def cleanup_route_table(server_ip_address):
    run(f"ip route del {server_ip_address}");
    run("ip route del 0/1");
    run("ip route del 128/1");

    run("iptables -t nat -D POSTROUTING -o tun0 -j MASQUERADE");
    run("iptables -D FORWARD -i tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT");
    run("iptables -D FORWARD -o tun0 -j ACCEPT");


async def tun_writer(tun_interface: TUNInterface, ws_socket: WebSocketClientProtocol):
    while True:
        packet = await ws_socket.recv()
        parsed_packet = parse_packet(packet)
        print_packet(parsed_packet, "SERVER:")
        await tun_interface.write_packet(packet)


async def tun_reader(tun_interface: TUNInterface, ws_socket: WebSocketClientProtocol):
    while True:
        packet = await tun_interface.read_packet()
        parsed_packet = parse_packet(packet)
        print_packet(parsed_packet, "TUN:")
        await ws_socket.send(packet)


async def main():
    try:
        server_ip_addr = resolve_ip_address(SERVER_ADDR) 

        tun_interface = await create_tun(TUN_IF_NAME, TUN_IF_ADDRESS)
        setup_route_table(TUN_IF_NAME, server_ip_addr)

        ws_to_server = await websockets.connect(SERVER_ADDR)
        print("connected to server")

        await asyncio.gather(
            tun_reader(tun_interface, ws_to_server),
            tun_writer(tun_interface, ws_to_server)
        )
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_route_table(server_ip_addr)


if __name__ == '__main__':
    asyncio.run(main())

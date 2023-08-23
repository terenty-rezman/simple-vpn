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
from tun import create_tun

LOGGER.basicConfig(level=LOGGER.DEBUG)

# connect to ws server
SERVER_ADDR = "wss://tech.divid.team/myvpn"
SERVER_ADDR = "ws://tech.divid.team:8777"

# tun interface config
TUN_IF_NAME = "custom-tunnel"
TUN_IF_ADDRESS = '10.1.0.1'


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


def cleanup_route_table(server_ip_address):
    run(f"ip route del {server_ip_address}");
    run("ip route del 0/1");
    run("ip route del 128/1");


def create_udp_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)
    return s


async def tun_writer(tun_interface, ws_socket):
    while True:
        message = await ws_socket.recv()
        print("received", message)
        await tun_interface.write(message)


async def tun_reader(tun_interface, ws_socket):
    while True:
        packet = await tun_interface.read(1024)
        parsed_packet = parse_packet(packet)
        print(parsed_packet)
        await ws_socket.send(packet)


async def main():
    try:
        server_ip_addr = resolve_ip_address(SERVER_ADDR) 

        ws_to_server = await websockets.connect(SERVER_ADDR)

        tun_interface = await create_tun(TUN_IF_NAME, IPv4Address(TUN_IF_ADDRESS))
        setup_route_table(TUN_IF_NAME, server_ip_addr)

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

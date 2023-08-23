import socket
from time import sleep
from ipaddress import IPv4Address
import asyncio
from functools import partial

import websockets

from utils import parse_packet, run
from tun import create_tun


# tun interface config
TUN_IF_NAME = "custom-tunnel"
TUN_IF_ADDRESS = '10.1.0.2'


def setup_route_table(interface_name):
    run("iptables -t nat -A POSTROUTING -s 10.1.0.0/24 ! -d 10.1.0.0/24 -m comment --comment 'vpndemo' -j MASQUERADE");
    run("iptables -A FORWARD -s 10.1.0.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT");
    run("iptables -A FORWARD -d 10.1.0.0/24 -j ACCEPT");


def cleanup_route_table():
    run("iptables -t nat -D POSTROUTING -s 10.1.0.0/24 ! -d 10.1.0.0/24 -m comment --comment 'vpndemo' -j MASQUERADE");
    run("iptables -D FORWARD -s 10.1.0.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT");
    run("iptables -D FORWARD -d 10.1.0.0/24 -j ACCEPT");


async def handle_client(tun_interface, websocket):
    await asyncio.gather(
        tun_reader(tun_interface, websocket),
        tun_writer(tun_interface, websocket)
    )

async def tun_writer(tun_interface, ws_socket):
    while True:
        message = await ws_socket.recv()
        print("WRITE TO TUN", message)
        await tun_interface.write(message)


async def tun_reader(tun_interface, ws_socket):
    while True:
        packet = await tun_interface.read(1024)
        parsed_packet = parse_packet(packet)
        print("READ FROM TUN", parsed_packet)
        await ws_socket.send(packet)


async def ws_server():
    try:
        tun_interface = await create_tun(TUN_IF_NAME, IPv4Address(TUN_IF_ADDRESS))
        setup_route_table(TUN_IF_ADDRESS)

        async with websockets.serve(partial(handle_client, tun_interface), "0.0.0.0", 8777):
            print("listening...")
            await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_route_table()


if __name__ == "__main__":
    asyncio.run(ws_server())

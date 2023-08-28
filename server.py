import asyncio
from functools import partial

import websockets
from websockets.server import WebSocketServerProtocol

from utils import parse_packet, run, print_packet, install_ctrl_c_handler
from tun import create_tun, TUNInterface

LISTEN_PORT = 8777

# tun interface config
TUN_IF_NAME = "custom-tunnel"
TUN_IF_ADDRESS = '10.1.0.1/24'


def setup_route_table(interface_name):
    # enable packet forwarding on host
    run("sysctl -w net.ipv4.ip_forward=1");

    run("iptables -t nat -A POSTROUTING -s 10.1.0.0/24 ! -d 10.1.0.0/24 -m comment --comment 'vpndemo' -j MASQUERADE");
    run("iptables -A FORWARD -s 10.1.0.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT");
    run("iptables -A FORWARD -d 10.1.0.0/24 -j ACCEPT");

    # run("iptables -I DOCKER-USER -j ACCEPT");


def cleanup_route_table():
    print("CLEAN UP")
    run("iptables -t nat -D POSTROUTING -s 10.1.0.0/24 ! -d 10.1.0.0/24 -m comment --comment 'vpndemo' -j MASQUERADE");
    run("iptables -D FORWARD -s 10.1.0.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT");
    run("iptables -D FORWARD -d 10.1.0.0/24 -j ACCEPT");

    # run("iptables -D DOCKER-USER -j ACCEPT");


async def handle_client(tun_interface: TUNInterface, websocket: WebSocketServerProtocol):
    print("client connected")
    await asyncio.gather(
        tun_reader(tun_interface, websocket),
        tun_writer(tun_interface, websocket)
    )
    print("client disconnected")


# receive packets from client, write them to tun
async def tun_writer(tun_interface: TUNInterface, ws_socket: WebSocketServerProtocol):
    while True:
        try:
            packet = await ws_socket.recv()
        except websockets.ConnectionClosed:
            break
        parsed_packet = parse_packet(packet)
        print_packet(parsed_packet, "CLIENT:")
        await tun_interface.write_packet(packet)


# read packets from tun, send them to client
async def tun_reader(tun_interface: TUNInterface, ws_socket: WebSocketServerProtocol):
    while True:
        packet = await tun_interface.read_packet()
        parsed_packet = parse_packet(packet)
        print_packet(parsed_packet, "TUN:")
        try:
            await ws_socket.send(packet)
        except websockets.ConnectionClosed:
            break


async def ws_server():
    try:
        install_ctrl_c_handler()

        tun_interface = await create_tun(TUN_IF_NAME, TUN_IF_ADDRESS)
        setup_route_table(TUN_IF_ADDRESS)

        server = await websockets.serve(
            partial(handle_client, tun_interface), 
            "0.0.0.0", LISTEN_PORT
        )
        print("listening...")
        await server.serve_forever()
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        cleanup_route_table()
        print("stopping...")


if __name__ == "__main__":
    asyncio.run(ws_server())

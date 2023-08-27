import asyncio
from functools import partial

import websockets

from utils import parse_packet, run
from tun import create_tun


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


async def handle_client(tun_interface, websocket):
    await asyncio.gather(
        tun_reader(tun_interface, websocket),
        tun_writer(tun_interface, websocket)
    )



from pypacker.layer3 import icmp
from pypacker.layer3 import ip
async def send_icmp(tun):
    ping = ip.IP(src_s="10.1.0.1", dst_s="8.8.8.8", p=1) +\
        icmp.ICMP(type=8) +\
        icmp.ICMP.Echo(id=123, seq=1)

    await tun.write(ping.bin())



async def tun_writer(tun_interface, ws_socket):
    while True:
        packet = await ws_socket.recv()
        parsed_packet = parse_packet(packet)
        if not parsed_packet[ip.ip6.IP6] and parsed_packet[ip.tcp.TCP]:
            print("CLIENT:", parsed_packet.src_s, "->", parsed_packet.dst_s, parsed_packet.len) 
        await tun_interface.write(packet)
         


async def tun_reader(tun_interface, ws_socket):
    while True:
        packet = await tun_interface.read(1024)
        parsed_packet = parse_packet(packet)
        if not parsed_packet[ip.ip6.IP6] and parsed_packet[ip.tcp.TCP]:
            print("TUN:", parsed_packet.src_s, "->", parsed_packet.dst_s, parsed_packet.len)
        await ws_socket.send(packet)


async def ws_server():
    try:
        tun_interface = await create_tun(TUN_IF_NAME, TUN_IF_ADDRESS)
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

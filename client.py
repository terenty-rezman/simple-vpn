"""tun.py
*CAP_NET_ADMIN capability is required to create TUN interfaces.*
Based on: https://github.com/povilasb/iptun/blob/master/iptun/tun.py
"""
import logging as LOGGER
import os
import struct
import subprocess
import time
from concurrent.futures.thread import ThreadPoolExecutor
from fcntl import ioctl
from ipaddress import IPv4Address
import re
import time
import socket

LOGGER.basicConfig(level=LOGGER.DEBUG)

_UNIX_TUNSETIFF = 0x400454ca
_UNIX_IFF_TUN = 0x0001
_UNIX_IFF_NO_PI = 0x1000

SERVER_ADDR = "tech.divid.team"
SERVER_UDP_PORT = 12000

TUN_NAME = "custom-tunnel"


def run(cmd: str):
    return subprocess.check_output(cmd.split()).decode()


class TUNInterface:
    def __init__(self, name: str, address: IPv4Address):
        self._name = name
        self._address = address

        # Create TUN interface.
        self._descriptor = os.open('/dev/net/tun', os.O_RDWR)
        ioctl(
            self._descriptor,
            _UNIX_TUNSETIFF,
            struct.pack('16sH', name.encode('ASCII'), _UNIX_IFF_TUN | _UNIX_IFF_NO_PI)
        )

        # Assign address to interface.
        subprocess.call(['/sbin/ip', 'addr', 'add', str(address), 'dev', name])

    def up(self) -> None:
        # Put interface into "up" state.
        subprocess.call(['/sbin/ip', 'link', 'set', 'dev', self._name, 'up'])
        self.setup_route_table()

    def down(self) -> None:
        self.cleanup_route_table()

    def read(self, number_bytes: int) -> bytes:
        packet = os.read(self._descriptor, number_bytes)
        LOGGER.debug('Read %d bytes from %s: %s', len(packet), self.name, packet[:10])
        return packet

    def write(self, packet: bytes) -> None:
        LOGGER.debug('Writing %s bytes to %s: %s', len(packet), self.name, packet[:10])
        os.write(self._descriptor, packet)
    
    def setup_route_table(self):
        # enable packet forwarding on host
        run("/usr/sbin/sysctl -w net.ipv4.ip_forward=1");

        # get old gateway ip addr
        old_default_route = run("ip route show 0/0")

        ipv4 = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"
        old_gateway_ip_addr = re.search(ipv4, old_default_route)

        # add route to vpn server through old gateway ip
        run(f"ip route add {SERVER_ADDR} via {old_gateway_ip_addr[0]}")

        # add default route for all trafic through our tun interface
        run(f"ip route add 0/1 dev {self._name}");
        run(f"ip route add 128/1 dev {self._name}");
    
    def cleanup_route_table(self):
        run(f"ip route del {SERVER_ADDR}");
        run("ip route del 0/1");
        run("ip route del 128/1");


def create_udp_socket():
    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.settimeout(1.0)
    return socket 


def test() -> None:
    to_server = create_udp_socket()
    server_addr = (SERVER_ADDR, SERVER_UDP_PORT)

    interface = TUNInterface(TUN_NAME, address=IPv4Address('10.1.0.0'))

    try:
        interface.up()

        while time.sleep(0.01) is None:
            packet = interface.read(1024)
            to_server.sendto(packet, server_addr)

    except KeyboardInterrupt:
        pass
    finally:
        interface.down()


if __name__ == '__main__':
    test()

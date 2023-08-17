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

LOGGER.basicConfig(level=LOGGER.DEBUG)

_UNIX_TUNSETIFF = 0x400454ca
_UNIX_IFF_TUN = 0x0001
_UNIX_IFF_NO_PI = 0x1000


class TUNInterface:

    def __init__(self, name: str, address: IPv4Address):
        self._name = name
        self._address = address

        # Create TUN interface.
        self._descriptor = os.open('/dev/net/tun', os.O_RDWR)
        ioctl(self._descriptor,
              _UNIX_TUNSETIFF,
              struct.pack('16sH', name.encode('ASCII'), _UNIX_IFF_TUN | _UNIX_IFF_NO_PI)
              )

        # Assign address to interface.
        subprocess.call(['/sbin/ip', 'addr', 'add', str(address), 'dev', name])

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> IPv4Address:
        return self._address

    def up(self) -> None:
        # Put interface into "up" state.
        subprocess.call(['/sbin/ip', 'link', 'set', 'dev', self._name, 'up'])

        # store existing default route
        self.existing_default_route = subprocess.check_output(["/sbin/ip", "route", "show", "default", "0.0.0.0/0"]).decode()

        # Intercept outgoing packets.
        if self.existing_default_route:
            # add default route
            print("replace default:", self.existing_default_route)
            subprocess.call(['/sbin/ip', 'route', 'replace', 'default', 'dev', self._name])
        else:
            # replace default route
            subprocess.call(['/sbin/ip', 'route', 'add', 'default', 'dev', self._name])

    def down(self) -> None:
        if self.existing_default_route:
            print("restore default route")
            subprocess.call(['/sbin/ip', 'route', 'replace', *self.existing_default_route.split()])


    def read(self, number_bytes: int) -> bytes:
        packet = os.read(self._descriptor, number_bytes)
        LOGGER.debug('Read %d bytes from %s: %s', len(packet), self.name, packet[:10])
        return packet

    def write(self, packet: bytes) -> None:
        LOGGER.debug('Writing %s bytes to %s: %s', len(packet), self.name, packet[:10])
        os.write(self._descriptor, packet)


def test() -> None:
    interface = TUNInterface('custom-tunnel', address=IPv4Address('10.1.0.0'))
    try:
        interface.up()

        while time.sleep(0.01) is None:
            interface.read(1024)
    except KeyboardInterrupt:
        pass
    finally:
        interface.down()


if __name__ == '__main__':
    test()

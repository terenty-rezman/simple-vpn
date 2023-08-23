from ipaddress import IPv4Address
import os
import struct
import subprocess
from fcntl import ioctl

import aiofiles


_UNIX_TUNSETIFF = 0x400454ca
_UNIX_IFF_TUN = 0x0001
_UNIX_IFF_NO_PI = 0x1000


class TUNInterface:
    def __init__(self, name: str, address: IPv4Address):
        self._name = name
        self._address = address
    
    async def init(self):
        self._tun = await aiofiles.open('/dev/net/tun', "r+b", buffering=0)

        # Create TUN interface.
        descriptor = self._tun.fileno()

        ioctl(
            descriptor,
            _UNIX_TUNSETIFF,
            struct.pack('16sH', self._name.encode('ASCII'), _UNIX_IFF_TUN | _UNIX_IFF_NO_PI)
        )

        # Assign address to interface.
        subprocess.call(['/sbin/ip', 'addr', 'add', str(self._address), 'dev', self._name])

        # up interface
        subprocess.call(['/sbin/ip', 'link', 'set', 'dev', self._name, 'up'])

    async def read(self, number_bytes: int) -> bytes:
        packet = await self._tun.read(number_bytes)
        # LOGGER.debug('Read %d bytes from %s: %s', len(packet), self._name, packet[:10])
        return packet

    async def write(self, packet: bytes) -> None:
        # LOGGER.debug('Writing %s bytes to %s: %s', len(packet), self._name, packet[:10])
        await self._tun.write(packet)


async def create_tun(name: str, address: IPv4Address) -> TUNInterface:
    tun = TUNInterface(name, address)
    await tun.init()
    return tun

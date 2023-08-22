from ipaddress import IPv4Address
import os
import struct
import subprocess
from fcntl import ioctl


_UNIX_TUNSETIFF = 0x400454ca
_UNIX_IFF_TUN = 0x0001
_UNIX_IFF_NO_PI = 0x1000


async def test_tun():
    import aiofiles

    # descriptor = os.open('/dev/net/tun', os.O_RDWR)
    tun = await aiofiles.open('/dev/net/tun', "r+b", buffering=0)

    descriptor = tun.fileno()

    ioctl(
        descriptor,
        _UNIX_TUNSETIFF,
        struct.pack('16sH', "TEST-TUN".encode('ASCII'), _UNIX_IFF_TUN | _UNIX_IFF_NO_PI)
    )

    # Assign address to interface.
    subprocess.call(['/sbin/ip', 'addr', 'add', str("10.1.0.1"), 'dev', "TEST-TUN"])

    # up interface
    subprocess.call(['/sbin/ip', 'link', 'set', 'dev', "TEST-TUN", 'up'])


    return tun


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

        # up interface
        subprocess.call(['/sbin/ip', 'link', 'set', 'dev', self._name, 'up'])

    def read(self, number_bytes: int) -> bytes:
        packet = os.read(self._descriptor, number_bytes)
        # LOGGER.debug('Read %d bytes from %s: %s', len(packet), self._name, packet[:10])
        return packet

    def write(self, packet: bytes) -> None:
        # LOGGER.debug('Writing %s bytes to %s: %s', len(packet), self._name, packet[:10])
        os.write(self._descriptor, packet)

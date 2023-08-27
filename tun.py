import struct
import subprocess
from fcntl import ioctl

import aiofiles

from utils import run

MTU = 1400
_UNIX_TUNSETIFF = 0x400454ca
_UNIX_IFF_TUN = 0x0001
_UNIX_IFF_NO_PI = 0x1000


class TUNInterface:
    def __init__(self, name: str, address: str):
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
        run(f"/sbin/ip addr add {self._address} dev {self._name}")
        run(f"/sbin/ip link set dev {self._name} mtu {MTU}")

        # up interface
        run(f"/sbin/ip link set dev {self._name} up")

    async def read_packet(self) -> bytes:
        packet = await self._tun.readall()
        return packet

    async def write_packet(self, packet: bytes) -> int:
        return await self._tun.write(packet)


async def create_tun(name: str, address: str) -> TUNInterface:
    tun = TUNInterface(name, address)
    await tun.init()
    return tun

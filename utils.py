from typing import Union
import subprocess

from pypacker.layer3.ip import IP as IPv4Packet
from pypacker.layer3.ip6 import IP6 as IPv6Packet


def run(cmd: str):
    return subprocess.check_output(cmd.split()).decode()


def packet_version(packet: bytes) -> int:
    # Credit: https://github.com/povilasb/iptun/blob/master/iptun/ip.py#L26
    return packet[0] >> 4


def parse_packet(data: bytes) -> Union[IPv4Packet, IPv6Packet]:
    # Credit: https://github.com/povilasb/iptun/blob/master/iptun/ip.py#L30
    packet_ver = packet_version(data)

    if packet_ver == 4:
        packet = IPv4Packet(data)
    elif packet_ver == 6:
        packet = IPv6Packet(data)
    else:
        raise ValueError(f'Unsupported IP packet version: {packet_ver}')

    return packet

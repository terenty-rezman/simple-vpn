from typing import Union
import subprocess

from pypacker.layer3.ip import IP as IPv4Packet
from pypacker.layer3.ip6 import IP6 as IPv6Packet
from pypacker import ip


def run(cmd: str):
    print(cmd)
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


def print_packet(packet: Union[IPv4Packet, IPv6Packet], prefix=None):
    if packet[ip.tcp.TCP] and not packet[ip.ip6.IP6]:
        print(
            prefix or "", packet.src_s, "->", packet.dst_s, 
            packet[ip.tcp.TCP].flags_t,
            # parsed_packet.highest_layer.body_bytes or ""
            packet.len
        )

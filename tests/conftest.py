"""Shared test fixtures for icom-lan tests."""

import struct

import pytest

from icom_lan.types import HEADER_SIZE, PacketType

_HEADER_FMT = "<IHHII"


@pytest.fixture
def control_packet() -> bytes:
    """A minimal 0x10-byte control packet (type=0x01, seq=0)."""
    return struct.pack(
        _HEADER_FMT, HEADER_SIZE, PacketType.CONTROL, 0, 0x12345678, 0x9ABCDEF0
    )


@pytest.fixture
def ping_packet() -> bytes:
    """A 0x15-byte ping packet (type=0x07)."""
    header = struct.pack(_HEADER_FMT, 0x15, PacketType.PING, 42, 0xAABBCCDD, 0x11223344)
    payload = b"\x00" + struct.pack("<I", 12345)  # reply=0, time=12345
    return header + payload


@pytest.fixture
def data_packet_with_civ() -> bytes:
    """A data packet (type=0x00) carrying a small CI-V payload."""
    civ_payload = bytes([0xFE, 0xFE, 0x94, 0xE0, 0x03, 0xFD])  # Read freq command
    inner = b"\x00" + struct.pack("<HH", len(civ_payload), 1)  # reply, datalen, sendseq
    header = struct.pack(
        _HEADER_FMT,
        HEADER_SIZE + len(inner) + len(civ_payload),
        PacketType.DATA,
        5,
        0x01,
        0x02,
    )
    return header + inner + civ_payload

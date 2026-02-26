"""Scope/waterfall frame assembly for Icom transceivers.

Wave data arrives as CI-V 0x27/0x00 packets in sequence bursts.
ScopeAssembler reconstructs complete frames from multi-packet sequences.

Reference: wfview icomcommander.cpp parseSpectrum() line 1921.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import bcd_decode

__all__ = ["ScopeFrame", "ScopeAssembler"]


@dataclass
class ScopeFrame:
    """Complete spectrum scope frame.

    Attributes:
        receiver: Receiver index (0=main, 1=sub).
        mode: Scope mode (0=center, 1=fixed, 2=scroll-C, 3=scroll-F).
        start_freq_hz: Start frequency in Hz.
        end_freq_hz: End frequency in Hz.
        pixels: Amplitude values as bytes, each 0x00–0xA0 (0–160).
        out_of_range: True if signal is outside the scope display range.
    """

    receiver: int
    mode: int
    start_freq_hz: int
    end_freq_hz: int
    pixels: bytes
    out_of_range: bool


def _bcd_byte_decode(b: int) -> int:
    """Decode a single BCD byte to decimal integer.

    Args:
        b: BCD byte (e.g. 0x11 → 11, 0x15 → 15).

    Returns:
        Decimal value 0–99.
    """
    return ((b >> 4) & 0x0F) * 10 + (b & 0x0F)


class _ReceiverState:
    """Assembly state for one receiver channel (main or sub)."""

    __slots__ = ("_mode", "_start_freq", "_end_freq", "_oor", "_chunks")

    def __init__(self) -> None:
        self._mode: int = 0
        self._start_freq: int = 0
        self._end_freq: int = 0
        self._oor: bool = False
        self._chunks: list[bytes] = []

    def feed(self, raw_payload: bytes, receiver: int) -> ScopeFrame | None:
        """Process one sequence packet.

        Args:
            raw_payload: Bytes starting with [seq_bcd, seqMax_bcd, data...].
                Sequence 1: data = [mode, 5-byte start BCD, 5-byte end BCD, oor, pixels...].
                Sequences 2..seqMax: data = pixel bytes (amplitude 0–160).
            receiver: Receiver index (0=main, 1=sub).

        Returns:
            Complete ScopeFrame when final sequence is received, else None.
        """
        if len(raw_payload) < 2:
            return None

        seq = _bcd_byte_decode(raw_payload[0])
        seq_max = _bcd_byte_decode(raw_payload[1])

        if seq == 1:
            self._chunks = []
            # Sequence 1 carries metadata: mode, start/end freq, OOR flag.
            # Minimum: 2 (seq/seqMax) + 1 (mode) + 5 (start) + 5 (end) + 1 (oor) = 14
            if len(raw_payload) < 14:
                return None

            self._mode = raw_payload[2]
            self._start_freq = bcd_decode(bytes(raw_payload[3:8]))
            self._end_freq = bcd_decode(bytes(raw_payload[8:13]))
            self._oor = bool(raw_payload[13])

            if self._oor:
                return ScopeFrame(
                    receiver=receiver,
                    mode=self._mode,
                    start_freq_hz=self._start_freq,
                    end_freq_hz=self._end_freq,
                    pixels=b"",
                    out_of_range=True,
                )

            # Center mode: start=center_freq, end=bandwidth.
            # Adjust to real edge frequencies per wfview parseSpectrum().
            if self._mode == 0:
                center = self._start_freq
                bw = self._end_freq
                self._start_freq = center - bw
                self._end_freq = center + bw

            # LAN single-packet mode: seq == seqMax, pixels follow OOR flag.
            if seq == seq_max:
                self._chunks.append(bytes(raw_payload[14:]))
                return self._build_frame(receiver)

            return None

        elif 1 < seq < seq_max:
            # Middle sequences: bytes [2:] are pixel amplitude data.
            self._chunks.append(bytes(raw_payload[2:]))
            return None

        elif seq == seq_max:
            # Last sequence: append remaining pixels and emit complete frame.
            self._chunks.append(bytes(raw_payload[2:]))
            return self._build_frame(receiver)

        return None

    def _build_frame(self, receiver: int) -> ScopeFrame:
        return ScopeFrame(
            receiver=receiver,
            mode=self._mode,
            start_freq_hz=self._start_freq,
            end_freq_hz=self._end_freq,
            pixels=b"".join(self._chunks),
            out_of_range=self._oor,
        )


class ScopeAssembler:
    """Assembles multi-sequence scope frames for main and sub receivers.

    Wave data arrives as a burst of CI-V 0x27/0x00 packets numbered
    seq=1..seqMax. This class reassembles those into complete ScopeFrame
    objects, maintaining independent state for each receiver channel.

    IC-7610 parameters: SpectrumSeqMax=15, SpectrumAmpMax=200, SpectrumLenMax=689.

    Usage::

        asm = ScopeAssembler()
        # raw_payload: CI-V frame data after the receiver byte
        # i.e. starting with [seq_bcd, seqMax_bcd, ...]
        frame = asm.feed(raw_payload, receiver=0)
        if frame is not None:
            process_frame(frame)
    """

    def __init__(self) -> None:
        self._main = _ReceiverState()
        self._sub = _ReceiverState()

    def feed(self, raw_payload: bytes, receiver: int) -> ScopeFrame | None:
        """Feed one scope sequence packet.

        Args:
            raw_payload: Bytes starting with [seq_bcd, seqMax_bcd, data...].
            receiver: Receiver index (0=main, 1=sub).

        Returns:
            Complete ScopeFrame when final sequence received, else None.
        """
        state = self._sub if receiver else self._main
        return state.feed(raw_payload, receiver)

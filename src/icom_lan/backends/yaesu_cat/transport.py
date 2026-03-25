"""Yaesu CAT serial transport — async line protocol with semicolon terminator.

All serial I/O is serialized through a single asyncio.Lock.  Every public
method (write, query) acquires the lock, so callers never need to worry about
interleaving or stale auto-info bytes.

Design principle: **no fire-and-forget**.  Even SET commands may trigger echo
or auto-info responses from the radio (lock status, IF info, etc.).  The
transport always drains these before releasing the lock.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from serial_asyncio import SerialTransport  # type: ignore[import-not-found]

__all__ = ["YaesuCatTransport", "CatTransportError", "CatTimeoutError"]

logger = logging.getLogger(__name__)

_DEPENDENCY_HINT = (
    "Yaesu CAT serial backend requires optional dependencies pyserial and "
    "pyserial-asyncio. Install with: pip install icom-lan[serial]"
)

# How long to wait for echo / auto-info after a write command (seconds).
# Short timeout: we just need to catch immediate echo, not wait for it.
# The primary defense is prefix matching in query(), not the drain.
_WRITE_DRAIN_TIMEOUT = 0.02


class CatTransportError(Exception):
    """Base error for CAT transport failures."""


class CatTimeoutError(CatTransportError):
    """Raised when read operation times out."""


class YaesuCatTransport:
    """Async serial transport for Yaesu CAT protocol.

    Usage::

        transport = YaesuCatTransport(device="/dev/cu.usbserial-01AE340D0", baudrate=38400)
        await transport.connect()

        response = await transport.query("FA;")  # Query freq
        print(f"Response: {response}")

        await transport.write("FA014074000;")  # Set freq (drains echo)

        await transport.close()

    Features:
    - **All I/O serialized** via a single lock — no interleaving
    - write() drains echo/auto-info before returning (not fire-and-forget)
    - query() skips echo + mismatched auto-info responses (prefix match)
    - Line-based readline (until `;` terminator)
    - Configurable timeouts + debug logging
    """

    def __init__(
        self,
        *,
        device: str,
        baudrate: int = 38400,
        timeout: float = 1.0,
        echo_suppression: bool = True,
        debug_logging: bool = False,
    ) -> None:
        self._device = device
        self._baudrate = baudrate
        self._timeout = timeout
        self._echo_suppression = echo_suppression
        self._debug_logging = debug_logging

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        """Whether transport is connected."""
        return self._connected

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open serial connection."""
        if self._connected:
            return

        try:
            import serial_asyncio  # type: ignore[import-not-found]
        except ImportError as exc:
            raise CatTransportError(_DEPENDENCY_HINT) from exc

        logger.info("Opening CAT serial port: %s @ %d baud", self._device, self._baudrate)

        try:
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self._device,
                baudrate=self._baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
            )
            self._connected = True
            logger.info("CAT serial port opened: %s", self._device)
        except Exception as exc:
            raise CatTransportError(
                f"Failed to open serial port {self._device}: {exc}"
            ) from exc

    async def close(self) -> None:
        """Close serial connection."""
        if not self._connected:
            return

        logger.info("Closing CAT serial port: %s", self._device)

        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

        self._reader = None
        self._writer = None
        self._connected = False
        logger.info("CAT serial port closed: %s", self._device)

    # ------------------------------------------------------------------
    # Low-level I/O (NO lock — callers must hold self._lock)
    # ------------------------------------------------------------------

    async def _raw_write(self, command: str) -> None:
        """Send bytes to serial port.  Caller must hold the lock."""
        if not self._connected or not self._writer:
            raise CatTransportError("Transport not connected")

        if not command.endswith(";"):
            command += ";"

        if self._debug_logging:
            logger.debug("CAT TX: %r", command)

        try:
            self._writer.write(command.encode("ascii"))
            await self._writer.drain()
        except Exception as exc:
            raise CatTransportError(f"Write failed: {exc}") from exc

    async def readline(self, *, timeout: float | None = None) -> str:
        """Read one line (until `;` terminator).  Caller must hold the lock.

        Returns:
            Response line (with trailing `;` stripped)
        """
        if not self._connected or not self._reader:
            raise CatTransportError("Transport not connected")

        if timeout is None:
            timeout = self._timeout

        try:
            line_bytes = await asyncio.wait_for(
                self._reader.readuntil(b";"),
                timeout=timeout,
            )
            line = line_bytes.decode("ascii").rstrip(";")

            if self._debug_logging:
                logger.debug("CAT RX: %r", line)

            return line
        except asyncio.TimeoutError as exc:
            raise CatTimeoutError(
                f"Read timeout ({timeout}s) waiting for ';' terminator"
            ) from exc
        except Exception as exc:
            raise CatTransportError(f"Read failed: {exc}") from exc

    async def flush_rx(self) -> int:
        """Drain any stale data from the receive buffer.

        Returns the number of bytes discarded.
        """
        if not self._reader:
            return 0
        buf = getattr(self._reader, "_buffer", None)
        if not buf:
            return 0
        discarded = len(buf)
        if discarded:
            if self._debug_logging:
                logger.debug("CAT: flushing %d stale bytes: %r", discarded, bytes(buf))
            buf.clear()
            logger.info("CAT: flushed %d stale bytes from RX buffer", discarded)
        return discarded

    async def _drain_responses(self, drain_timeout: float = _WRITE_DRAIN_TIMEOUT) -> int:
        """Read and discard all pending responses until timeout.

        Used after SET commands to drain echo + auto-info notifications.
        Returns number of lines drained.
        """
        drained = 0
        while True:
            try:
                line = await self.readline(timeout=drain_timeout)
                drained += 1
                if self._debug_logging:
                    logger.debug("CAT: drained post-write response: %r", line)
            except CatTimeoutError:
                break  # No more data — clean
        # Also flush any partial bytes
        await self.flush_rx()
        return drained

    # ------------------------------------------------------------------
    # Public API (ALL acquire lock)
    # ------------------------------------------------------------------

    async def write(self, command: str) -> None:
        """Send SET command and drain any echo/auto-info response.

        Unlike fire-and-forget, this method waits briefly for the radio to
        send back echo or status notifications, then discards them.  This
        prevents stale bytes from corrupting the next query().

        Args:
            command: CAT command string (e.g., "MD0E;" to set mode PSK)
        """
        async with self._lock:
            await self.flush_rx()
            await self._raw_write(command)
            drained = await self._drain_responses()
            if drained and self._debug_logging:
                logger.debug("CAT: drained %d response(s) after write %r", drained, command)

    async def query(self, command: str, *, timeout: float | None = None) -> str:
        """Send GET command and return the matching response.

        Serialized via lock.  Skips echo lines and mismatched auto-info
        responses (prefix-based filtering).

        Args:
            command: CAT command string (e.g., "FA;")
            timeout: Read timeout in seconds (default: instance timeout)

        Returns:
            Response line (with trailing `;` stripped)
        """
        async with self._lock:
            await self.flush_rx()
            await self._raw_write(command)

            # Derive expected prefix from command (e.g. "SM0;" → "SM")
            expected_prefix = command.rstrip(";").rstrip("0123456789")
            cmd_body = command.rstrip(";")

            if timeout is None:
                timeout = self._timeout

            max_attempts = 6
            for _attempt in range(max_attempts):
                response = await self.readline(timeout=timeout)

                # "?" = command not recognized by radio
                if response == "?":
                    raise CatTransportError(
                        f"Radio rejected command {command!r} (returned '?;')"
                    )

                # Echo suppression
                if self._echo_suppression and response == cmd_body:
                    if self._debug_logging:
                        logger.debug("CAT: echo detected, reading actual response")
                    continue

                # Auto-info suppression: skip responses that don't match our
                # command prefix (e.g. LK0 when we asked SM0)
                if expected_prefix and not response.startswith(expected_prefix):
                    logger.info(
                        "CAT: skipping stale auto-info %r (expected prefix %r)",
                        response, expected_prefix,
                    )
                    continue

                return response

            raise CatTransportError(
                f"Query {command!r}: exhausted {max_attempts} attempts, no matching response"
            )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "YaesuCatTransport":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        await self.close()

"""CI-V event routing and request tracking utilities."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum

from .types import CivFrame

__all__ = [
    "CivEvent",
    "CivEventType",
    "CivRequestKey",
    "CivRequestTracker",
    "iter_civ_frames",
    "request_key_from_frame",
]


class CivEventType(StrEnum):
    """Classified CI-V event categories."""

    ACK = "ack"
    NAK = "nak"
    RESPONSE = "response"
    SCOPE_CHUNK = "scope_chunk"
    SCOPE_FRAME = "scope_frame"


@dataclass(frozen=True, slots=True)
class CivEvent:
    """One routed CI-V event."""

    type: CivEventType
    frame: CivFrame | None = None
    receiver: int | None = None


@dataclass(frozen=True, slots=True)
class CivRequestKey:
    """Request matcher key for CI-V responses."""

    command: int
    sub: int | None
    receiver: int | None = None


@dataclass(slots=True)
class _AckWaiter:
    future: asyncio.Future[CivFrame] | None
    token: int
    created_monotonic: float


@dataclass(slots=True)
class _PendingRequest:
    key: CivRequestKey
    future: asyncio.Future[CivFrame]


def request_key_from_frame(frame: CivFrame) -> CivRequestKey:
    """Build request key from an outgoing CI-V frame."""
    return CivRequestKey(
        command=frame.command,
        sub=frame.sub,
        receiver=frame.receiver,
    )


def iter_civ_frames(payload: bytes) -> Iterator[bytes]:
    """Yield CI-V frames found in an arbitrary payload buffer."""
    idx = 0
    while idx < len(payload) - 4:
        if payload[idx] != 0xFE or payload[idx + 1] != 0xFE:
            idx += 1
            continue
        fd_pos = payload.find(b"\xfd", idx + 4)
        if fd_pos < 0:
            break
        yield payload[idx : fd_pos + 1]
        idx = fd_pos + 1


class CivRequestTracker:
    """Tracks pending requests and resolves matching CI-V responses."""

    def __init__(self) -> None:
        self._ack_waiters: list[_AckWaiter] = []
        self._response_waiters: list[_PendingRequest] = []
        self._next_ack_token = 1

    @property
    def pending_count(self) -> int:
        """Number of unresolved pending requests."""
        return len(self._ack_waiters) + len(self._response_waiters)

    @property
    def ack_sink_count(self) -> int:
        """Number of fire-and-forget ACK sink waiters currently tracked."""
        return sum(1 for w in self._ack_waiters if w.future is None)

    def register_ack(self, wait: bool = True) -> asyncio.Future[CivFrame] | int:
        """Register a pending request that expects an ACK/NAK.

        Returns:
            - Future when ``wait=True`` (caller awaits ACK/NAK)
            - Integer sink token when ``wait=False`` (fire-and-forget sink)
        """
        token = self._next_ack_token
        self._next_ack_token += 1
        created = time.monotonic()

        if wait:
            future: asyncio.Future[CivFrame] = asyncio.get_running_loop().create_future()
            self._ack_waiters.append(
                _AckWaiter(future=future, token=token, created_monotonic=created)
            )
            return future

        self._ack_waiters.append(
            _AckWaiter(future=None, token=token, created_monotonic=created)
        )
        return token

    def register_response(self, key: CivRequestKey) -> asyncio.Future[CivFrame]:
        """Register a pending request that expects a specific data response."""
        future: asyncio.Future[CivFrame] = asyncio.get_running_loop().create_future()
        self._response_waiters.append(_PendingRequest(key=key, future=future))
        return future

    def unregister(self, future: asyncio.Future[CivFrame]) -> None:
        """Remove a request future from pending list."""
        self._ack_waiters = [w for w in self._ack_waiters if w.future is not future]
        self._response_waiters = [
            w for w in self._response_waiters if w.future is not future
        ]

    def unregister_ack_sink(self, token: int) -> bool:
        """Remove a fire-and-forget ACK sink by token."""
        for i, waiter in enumerate(self._ack_waiters):
            if waiter.token == token and waiter.future is None:
                self._ack_waiters.pop(i)
                return True
        return False

    def drop_ack_sinks(self) -> int:
        """Drop all fire-and-forget ACK sinks.

        Returns:
            Number of dropped sink entries.
        """
        before = len(self._ack_waiters)
        self._ack_waiters = [w for w in self._ack_waiters if w.future is not None]
        return before - len(self._ack_waiters)

    def resolve(self, event: CivEvent) -> bool:
        """Resolve a pending request from an incoming event."""
        frame = event.frame
        if frame is None:
            return False

        if event.type in (CivEventType.ACK, CivEventType.NAK):
            while self._ack_waiters:
                waiter = self._ack_waiters.pop(0)
                if waiter.future is not None and not waiter.future.done():
                    waiter.future.set_result(frame)
                    return True
                elif waiter.future is None:
                    # Successfully sunk an ACK for a fire-and-forget request
                    return True
            return False

        if event.type == CivEventType.RESPONSE:
            for i, pending in enumerate(self._response_waiters):
                if self._matches(pending.key, frame):
                    self._response_waiters.pop(i)
                    if not pending.future.done():
                        pending.future.set_result(frame)
                    return True
            return False

        return False

    def fail_all(self, exc: Exception) -> None:
        """Fail all pending requests and clear the tracker."""
        for w in self._ack_waiters:
            if w.future is not None and not w.future.done():
                w.future.set_exception(exc)
        self._ack_waiters.clear()

        for w in self._response_waiters:
            if not w.future.done():
                w.future.set_exception(exc)
        self._response_waiters.clear()

    @staticmethod
    def _matches(key: CivRequestKey, frame: CivFrame) -> bool:
        if frame.command != key.command:
            return False
        if frame.sub != key.sub:
            return False
        if key.receiver is not None and frame.receiver != key.receiver:
            return False
        return True

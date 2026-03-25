"""YaesuCatPoller — polling scheduler for YaesuCatRadio.

Three polling groups with different intervals share a single serial lock:

- **Fast  (75 ms):**  S-meter (main + sub) for smooth UI animation.
- **Medium (200 ms):** Frequency, mode, PTT — changes at human speed.
- **Slow  (1000 ms):** AGC, AF/RF/squelch levels — rarely change.

Each group runs as an independent asyncio task.  The shared lock prevents
concurrent serial requests so the CAT bus is never overwhelmed.

Usage::

    poller = YaesuCatPoller(radio, callback=on_state_update)
    await poller.start()
    ...
    await poller.pause()
    await poller.resume()
    await poller.stop()
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ...radio_state import RadioState
    from ...web.radio_poller import CommandQueue
    from .radio import YaesuCatRadio

__all__ = ["YaesuCatPoller"]

logger = logging.getLogger(__name__)

_FAST_INTERVAL: float = 0.075    # 13.3 Hz
_MEDIUM_INTERVAL: float = 0.200  # 5 Hz
_SLOW_INTERVAL: float = 1.000    # 1 Hz
_EMA_ALPHA: float = 0.3


class YaesuCatPoller:
    """Polling scheduler for :class:`~.radio.YaesuCatRadio`.

    Args:
        radio:           Connected :class:`YaesuCatRadio` instance.
        callback:        Called with the current :class:`RadioState` after
                         every successful poll.
        fast_interval:   Seconds between fast (S-meter) polls.
        medium_interval: Seconds between medium (freq/mode/PTT) polls.
        slow_interval:   Seconds between slow (AGC/levels) polls.
        ema_alpha:       EMA smoothing factor for S-meter (0 = disabled,
                         0.3 = moderate smoothing, 1.0 = no smoothing).
    """

    def __init__(
        self,
        radio: "YaesuCatRadio",
        callback: Callable[["RadioState"], None],
        *,
        command_queue: "CommandQueue | None" = None,
        fast_interval: float = _FAST_INTERVAL,
        medium_interval: float = _MEDIUM_INTERVAL,
        slow_interval: float = _SLOW_INTERVAL,
        ema_alpha: float = _EMA_ALPHA,
    ) -> None:
        self._radio = radio
        self._callback = callback
        self._command_queue = command_queue
        self._fast_interval = fast_interval
        self._medium_interval = medium_interval
        self._slow_interval = slow_interval
        self._ema_alpha = ema_alpha

        # Shared serial access lock — one request in flight at a time.
        self._lock: asyncio.Lock = asyncio.Lock()
        # Clear = paused, set = running.
        self._paused: asyncio.Event = asyncio.Event()
        self._paused.set()

        self._tasks: list[asyncio.Task[None]] = []

        # EMA state per receiver (None until first sample).
        self._ema_s_main: float | None = None
        self._ema_s_sub: float | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start all three polling loops."""
        if self._tasks:
            return
        self._paused.set()
        loop = asyncio.get_running_loop()
        self._tasks = [
            loop.create_task(self._fast_loop(), name="yaesu-poller-fast"),
            loop.create_task(self._medium_loop(), name="yaesu-poller-medium"),
            loop.create_task(self._slow_loop(), name="yaesu-poller-slow"),
        ]
        logger.info("YaesuCatPoller: started")

    async def stop(self) -> None:
        """Cancel all polling loops and wait for them to finish."""
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("YaesuCatPoller: stopped")

    async def pause(self) -> None:
        """Suspend polling.  In-flight requests complete; new ones wait."""
        self._paused.clear()
        logger.debug("YaesuCatPoller: paused")

    async def resume(self) -> None:
        """Resume a paused poller."""
        self._paused.set()
        logger.debug("YaesuCatPoller: resumed")

    @property
    def running(self) -> bool:
        """True if any polling task is alive."""
        return bool(self._tasks) and any(not t.done() for t in self._tasks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_ema(self, raw: int, prev: float | None) -> float:
        """Apply exponential moving average smoothing to a meter sample."""
        if prev is None or self._ema_alpha <= 0:
            return float(raw)
        return self._ema_alpha * raw + (1.0 - self._ema_alpha) * prev

    # ------------------------------------------------------------------
    # Polling loops
    # ------------------------------------------------------------------

    async def _fast_loop(self) -> None:
        while True:
            await self._paused.wait()
            try:
                async with self._lock:
                    await self._poll_fast()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("YaesuCatPoller: fast poll error", exc_info=True)
            await asyncio.sleep(self._fast_interval)

    async def _medium_loop(self) -> None:
        while True:
            await self._paused.wait()
            try:
                async with self._lock:
                    await self._drain_commands()
                    await self._poll_medium()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("YaesuCatPoller: medium poll error", exc_info=True)
            await asyncio.sleep(self._medium_interval)

    async def _slow_loop(self) -> None:
        while True:
            await self._paused.wait()
            try:
                async with self._lock:
                    await self._poll_slow()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("YaesuCatPoller: slow poll error", exc_info=True)
            await asyncio.sleep(self._slow_interval)

    # ------------------------------------------------------------------
    # Command queue drain
    # ------------------------------------------------------------------

    async def _drain_commands(self) -> None:
        """Process all pending commands from the web UI command queue."""
        if self._command_queue is None or not self._command_queue.has_commands:
            return

        commands = self._command_queue.drain()
        for cmd in commands:
            try:
                await self._execute_command(cmd)
            except Exception:
                logger.warning(
                    "YaesuCatPoller: command %s failed",
                    type(cmd).__name__,
                    exc_info=True,
                )

    # CI-V band codes → Yaesu BS band codes
    _CIV_TO_YAESU_BAND: dict[int, int] = {
        0x00: 0,   # 160m → 1.8M
        0x01: 1,   # 80m  → 3.5M
        0x02: 2,   # 60m  → 5M
        0x03: 3,   # 40m  → 7M
        0x04: 4,   # 30m  → 10M
        0x05: 5,   # 20m  → 14M
        0x06: 6,   # 17m  → 18M
        0x07: 7,   # 15m  → 21M
        0x08: 8,   # 12m  → 24M
        0x09: 9,   # 10m  → 28M
        0x0A: 10,  # 6m   → 50M
    }

    async def _execute_command(self, cmd: Any) -> None:
        """Dispatch a single command to the radio.

        Commands come from the web UI CommandQueue.  The dispatcher handles
        all command types; unsupported commands for this radio are silently
        dropped.  For commands that have a profile entry, ``generic_set``
        is used as fallback.
        """
        from ...web.radio_poller import (
            PttOff,
            PttOn,
            SelectVfo,
            SetAfLevel,
            SetAgc,
            SetApf,
            SetAttenuator,
            SetAutoNotch,
            SetBand,
            SetBreakIn,
            SetCompressor,
            SetCompressorLevel,
            SetCwPitch,
            SetDataMode,
            SetDialLock,
            SetDigiSel,
            SetDriveGain,
            SetDualWatch,
            SetFilter,
            SetFilterShape,
            SetFilterWidth,
            SetFreq,
            SetIpPlus,
            SetKeySpeed,
            SetManualNotch,
            SetMicGain,
            SetMode,
            SetMonitor,
            SetMonitorGain,
            SetNB,
            SetNBLevel,
            SetNR,
            SetNRLevel,
            SetNotchFilter,
            SetPbtInner,
            SetPbtOuter,
            SetPower,
            SetPreamp,
            SetRfGain,
            SetRitFrequency,
            SetRitStatus,
            SetRitTxStatus,
            SetSplit,
            SetSquelch,
            SetTwinPeak,
            SetVox,
            VfoSwap,
        )

        radio = self._radio
        name = type(cmd).__name__

        try:
            match cmd:
                # ── Core: Frequency / Mode / Band ──
                case SetFreq(freq=freq, receiver=rx):
                    await radio.set_freq(freq, receiver=rx)
                case SetMode(mode=mode, receiver=rx):
                    await radio.set_mode(mode, receiver=rx)
                case SetBand(band=band):
                    yaesu_band = self._CIV_TO_YAESU_BAND.get(band, band)
                    await radio.set_band(yaesu_band)
                case SelectVfo(vfo=vfo):
                    if radio.has_command("set_vfo_select"):
                        code = "0" if vfo.upper() in ("A", "MAIN") else "1"
                        await radio.generic_set("set_vfo_select", vfo=code)
                case VfoSwap():
                    if radio.has_command("vfo_a_to_b"):
                        await radio.generic_set("vfo_a_to_b")

                # ── PTT ──
                case PttOn():
                    await radio.set_ptt(True)
                case PttOff():
                    await radio.set_ptt(False)

                # ── Audio / RF Levels ──
                case SetAfLevel(level=level):
                    await radio.set_af_level(level)
                case SetRfGain(level=level):
                    await radio.set_rf_gain(level)
                case SetSquelch(level=level):
                    await radio.set_squelch(level)
                case SetMicGain(level=level):
                    await radio.set_mic_gain(level)
                case SetPower(level=level):
                    await radio.set_power(level)
                case SetDriveGain(level=level):
                    if radio.has_command("set_drive_gain"):
                        await radio.generic_set("set_drive_gain", level=level)

                # ── RF Front End ──
                case SetAttenuator(state=state):
                    await radio.set_attenuator(state)
                case SetPreamp(band=band, value=value):
                    await radio.set_preamp(band, value)

                # ── DSP / Noise ──
                case SetAgc(mode=mode):
                    await radio.set_agc(mode)
                case SetNB(on=on):
                    if radio.has_command("set_nb"):
                        await radio.generic_set("set_nb", state="1" if on else "0")
                case SetNR(on=on):
                    if radio.has_command("set_nr"):
                        await radio.generic_set("set_nr", state="1" if on else "0")
                case SetNBLevel(level=level):
                    await radio.set_nb_level(level)
                case SetNRLevel(level=level):
                    await radio.set_nr_level(level)
                case SetAutoNotch(on=on):
                    await radio.set_auto_notch(on)
                case SetManualNotch(on=on):
                    if radio.has_command("set_manual_notch"):
                        await radio.generic_set("set_manual_notch", state=int(on))
                case SetNotchFilter(level=level):
                    if radio.has_command("set_manual_notch_freq"):
                        await radio.generic_set("set_manual_notch_freq", freq=level)

                # ── Filters ──
                case SetFilter(filter_num=num):
                    pass  # FTX-1 uses filter_width, not discrete filter numbers
                case SetFilterWidth(width=width):
                    if radio.has_command("set_filter_width"):
                        await radio.generic_set("set_filter_width", level=width)
                case SetFilterShape(shape=shape):
                    pass  # Not available on FTX-1
                case SetPbtInner() | SetPbtOuter():
                    pass  # Not available on FTX-1

                # ── CW ──
                case SetKeySpeed(speed=speed):
                    if radio.has_command("set_keyer_speed"):
                        await radio.generic_set("set_keyer_speed", wpm=speed)
                case SetCwPitch(value=value):
                    if radio.has_command("set_key_pitch"):
                        await radio.generic_set("set_key_pitch", idx=value)
                case SetBreakIn(break_in_mode=mode):
                    if radio.has_command("set_break_in"):
                        await radio.generic_set("set_break_in", state=str(mode))

                # ── TX Controls ──
                case SetCompressor(on=on):
                    if radio.has_command("set_processor"):
                        await radio.generic_set("set_processor", state="1" if on else "0")
                case SetCompressorLevel(level=level):
                    if radio.has_command("set_processor_level"):
                        await radio.generic_set("set_processor_level", level=level)
                case SetVox(on=on):
                    if radio.has_command("set_vox"):
                        await radio.generic_set("set_vox", state="1" if on else "0")
                case SetMonitor(on=on):
                    if radio.has_command("set_monitor_on"):
                        await radio.generic_set("set_monitor_on", level=1 if on else 0)
                case SetMonitorGain(level=level):
                    if radio.has_command("set_monitor_level"):
                        await radio.generic_set("set_monitor_level", level=level)
                case SetSplit(on=on):
                    if radio.has_command("set_split"):
                        await radio.generic_set("set_split", state="1" if on else "0")

                # ── RIT / Clarifier ──
                case SetRitStatus(on=on):
                    if radio.has_command("set_clarifier"):
                        # Clarifier: CF000{rx}{tx}{pad:03d}
                        await radio.generic_set(
                            "set_clarifier",
                            rx="1" if on else "0",
                            tx="0",
                            pad=0,
                        )
                case SetRitTxStatus(on=on):
                    if radio.has_command("set_clarifier"):
                        await radio.generic_set(
                            "set_clarifier",
                            rx="0",
                            tx="1" if on else "0",
                            pad=0,
                        )
                case SetRitFrequency(freq=freq):
                    if radio.has_command("set_clarifier_freq"):
                        sign = "+" if freq >= 0 else "-"
                        await radio.generic_set(
                            "set_clarifier_freq",
                            sign=sign,
                            offset=abs(freq),
                        )

                # ── Data Mode ──
                case SetDataMode(mode=mode):
                    if radio.has_command("set_data_mode"):
                        await radio.generic_set("set_data_mode", mode=mode)

                # ── Dial Lock ──
                case SetDialLock(on=on):
                    if radio.has_command("set_lock"):
                        await radio.generic_set("set_lock", state="1" if on else "0")

                # ── Dual Watch ──
                case SetDualWatch(on=on):
                    if radio.has_command("set_dual_watch"):
                        await radio.generic_set("set_dual_watch", state="1" if on else "0")

                # ── IC-7610-specific (not applicable) ──
                case SetIpPlus() | SetApf() | SetTwinPeak() | SetDigiSel():
                    pass  # Icom-only DSP features

                case _:
                    logger.debug("CMD: unhandled %s — ignoring", name)
                    return

            logger.info("CMD: %s", name)

        except Exception:
            logger.warning("CMD: %s failed", name, exc_info=True)

    # ------------------------------------------------------------------
    # Poll actions
    # ------------------------------------------------------------------

    async def _poll_fast(self) -> None:
        """Fast group: S-meter for main and sub receivers."""
        state = self._radio.radio_state

        raw_main = await self._radio.get_s_meter(0)
        self._ema_s_main = self._apply_ema(raw_main, self._ema_s_main)
        state.main.s_meter = int(round(self._ema_s_main))

        try:
            raw_sub = await self._radio.get_s_meter(1)
            self._ema_s_sub = self._apply_ema(raw_sub, self._ema_s_sub)
            state.sub.s_meter = int(round(self._ema_s_sub))
        except Exception:
            # Sub receiver S-meter may not be supported on all rigs.
            logger.debug("YaesuCatPoller: sub S-meter unavailable", exc_info=True)

        self._callback(state)

    async def _poll_medium(self) -> None:
        """Medium group: frequency, mode, PTT."""
        await self._radio.get_freq(0)
        await self._radio.get_mode(0)

        try:
            await self._radio.get_freq(1)
            await self._radio.get_mode(1)
        except Exception:
            logger.debug("YaesuCatPoller: sub freq/mode unavailable", exc_info=True)

        await self._radio.get_ptt()

        self._callback(self._radio.radio_state)

    async def _poll_slow(self) -> None:
        """Slow group: AGC, levels, DSP, TX settings."""
        state = self._radio.radio_state
        radio = self._radio

        # -- Levels --
        for attr, getter, field in (
            ("agc", "get_agc", "mode"),
            ("af_level", "get_af_level", "level"),
            ("rf_gain", "get_rf_gain", "level"),
            ("squelch", "get_squelch", "level"),
        ):
            try:
                if radio.has_command(getter):
                    result = await radio.generic_get(getter)
                    val = result.get(field, 0)
                    if isinstance(val, str):
                        val = int(val)
                    setattr(state.main, attr, val)
            except Exception:
                logger.debug("YaesuCatPoller: %s failed", getter, exc_info=True)

        # -- DSP: NB/NR levels, auto notch --
        for attr, getter, field in (
            ("nb_level", "get_nb_level", "level"),
            ("nr_level", "get_nr_level", "level"),
            ("auto_notch", "get_auto_notch", "state"),
        ):
            try:
                if radio.has_command(getter):
                    result = await radio.generic_get(getter)
                    val = result.get(field, 0)
                    if isinstance(val, str):
                        val = int(val)
                    setattr(state.main, attr, val)
            except Exception:
                logger.debug("YaesuCatPoller: %s failed", getter, exc_info=True)

        # -- Filter width --
        try:
            if radio.has_command("get_filter_width"):
                result = await radio.generic_get("get_filter_width")
                state.main.filter_width = result.get("level", 0)
        except Exception:
            logger.debug("YaesuCatPoller: get_filter_width failed", exc_info=True)

        # -- TX power --
        try:
            if radio.has_command("get_power"):
                result = await radio.generic_get("get_power")
                state.power_level = result.get("watts", 0)
        except Exception:
            logger.debug("YaesuCatPoller: get_power failed", exc_info=True)

        # -- Mic gain --
        try:
            if radio.has_command("get_mic_gain"):
                result = await radio.generic_get("get_mic_gain")
                state.mic_gain = result.get("level", 0)
        except Exception:
            logger.debug("YaesuCatPoller: get_mic_gain failed", exc_info=True)

        # -- Split --
        try:
            if radio.has_command("get_split"):
                result = await radio.generic_get("get_split")
                val = result.get("state", "0")
                state.split = val in (1, "1", True)
        except Exception:
            logger.debug("YaesuCatPoller: get_split failed", exc_info=True)

        # -- VOX --
        try:
            if radio.has_command("get_vox"):
                result = await radio.generic_get("get_vox")
                val = result.get("state", "0")
                state.vox = val in (1, "1", True)
        except Exception:
            logger.debug("YaesuCatPoller: get_vox failed", exc_info=True)

        # -- Dial lock --
        try:
            if radio.has_command("get_lock"):
                result = await radio.generic_get("get_lock")
                val = result.get("state", "0")
                state.dial_lock = val in (1, "1", True)
        except Exception:
            logger.debug("YaesuCatPoller: get_lock failed", exc_info=True)

        self._callback(state)

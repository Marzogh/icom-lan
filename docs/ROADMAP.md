# Roadmap

## Current State: v0.2.0 (Python)

- ✅ Phase 1 — Transport (UDP, auth, keep-alive, dual-port)
- ✅ Phase 2 — CI-V Commands (frequency, mode, power, meters, PTT, CW, VFO, split)
- ⬜ Phase 3 — Audio Streaming
- ⬜ Phase 4 — Polish & Publish
- ⬜ Phase 5 — Rust Core
- ⬜ Phase 6 — Spectrum & Waterfall
- ⬜ Phase 7 — Web UI (full wfview/RS-BA1 replacement)

---

## Phase 3 — Audio Streaming (Python)

**Goal:** RX/TX audio через Opus codec на порту 50003.

### Tasks

- [ ] Изучить `icomudpaudio.cpp` — формат аудио-пакетов, заголовки, sequence
- [ ] Открытие аудио-потока (OpenClose на audio port, аналогично CI-V)
- [ ] RX: приём Opus-пакетов → декодирование → callback API
- [ ] TX: PCM input → Opus encode → отправка на радио
- [ ] Буферизация и jitter buffer (компенсация неравномерности UDP)
- [ ] Sample rate negotiation (8/16/24/48 kHz — задаётся в conninfo)
- [ ] Тесты с реальным радио

### API Design

```python
# RX — callback-based
def on_audio(pcm_data: bytes, sample_rate: int):
    # process audio...

async with IcomRadio(...) as radio:
    radio.start_audio_rx(callback=on_audio)
    await asyncio.sleep(10)
    radio.stop_audio_rx()

# TX — push-based
async with IcomRadio(...) as radio:
    radio.start_audio_tx(sample_rate=48000)
    radio.push_audio(pcm_data)
    radio.stop_audio_tx()

# Full duplex
async with IcomRadio(...) as radio:
    radio.start_audio(rx_callback=on_audio, tx_sample_rate=48000)
```

### Dependencies

- `opuslib` — Python bindings for libopus (optional dependency, `pip install icom-lan[audio]`)

---

## Phase 4 — Polish & Publish (Python)

**Goal:** Production-ready библиотека на PyPI.

### Tasks

- [ ] Sync API wrapper (для тех кто не хочет async)
- [ ] Autodiscovery улучшение (multicast, timeout config)
- [ ] Multi-model support (CI-V address presets для IC-705, IC-7300, IC-9700)
- [ ] Token renewal timer (wfview: TOKEN_RENEWAL = 60s, sends `sendToken(0x05)`)
- [ ] Reconnect logic (auto-reconnect при потере связи)
- [ ] Proper integration test suite (`@pytest.mark.integration`)
- [ ] PyPI публикация (`uv publish` / `twine upload`)
- [ ] GitHub Release с changelog
- [ ] MkDocs documentation site (GitHub Pages) — ✅ done
- [ ] Badges: PyPI version, downloads, CI status

### Sync API Design

```python
from icom_lan.sync import IcomRadio

# Blocking API (wraps asyncio internally)
with IcomRadio("192.168.1.100", username="u", password="p") as radio:
    freq = radio.get_frequency()
    radio.set_frequency(14_074_000)
```

---

## Phase 5 — Rust Core 🦀

**Goal:** Переписать ядро на Rust. Python API остаётся, но внутри — нативный код. Плюс standalone CLI и WASM.

### Мотивация

| Фича | Почему Rust |
|------|------------|
| **Audio latency** | Нет GIL, нет GC pauses → предсказуемый real-time audio |
| **Один бинарник** | Скачал → запустил. Без Python, pip, venv |
| **Memory safety** | Парсинг бинарных UDP-пакетов с гарантией компилятора |
| **Multi-platform FFI** | Один codebase → Python, Node.js, C/C++, Swift, WASM |
| **Tokio async** | 3 порта + pings + retransmit + audio — эффективнее asyncio |
| **WASM** | Управление радио из браузера (!) |
| **Embedded** | Raspberry Pi, embedded Linux без Python runtime |

### Архитектура

```
┌──────────────────────────────────────────────────┐
│              icom-lan-core (Rust)                 │
│                                                   │
│  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Transport │  │ Protocol │  │ Audio (Opus)  │  │
│  │  (tokio)  │  │ (CI-V)   │  │ (decode/enc)  │  │
│  └─────┬─────┘  └────┬─────┘  └──────┬────────┘  │
│        └──────────────┴───────────────┘           │
│                       │                           │
│  ┌────────────────────┴───────────────────────┐   │
│  │           Public Rust API                  │   │
│  │  IcomRadio::connect / get_freq / set_mode  │   │
│  └────────────────────────────────────────────┘   │
└───────┬──────────┬──────────┬──────────┬──────────┘
        │          │          │          │
   ┌────┴───┐ ┌───┴────┐ ┌───┴───┐ ┌───┴────┐
   │ PyO3   │ │  CLI   │ │ WASM  │ │ C FFI  │
   │(Python)│ │(clap)  │ │(wasm- │ │(cbind- │
   │        │ │        │ │ pack) │ │ gen)   │
   └────────┘ └────────┘ └───────┘ └────────┘
```

### Crates (зависимости Rust)

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }       # async runtime
bytes = "1"                                            # efficient byte buffers
opus = "0.3"                                           # Opus codec
tracing = "0.1"                                        # structured logging
thiserror = "2"                                        # error types

# Bindings
pyo3 = { version = "0.24", features = ["extension-module"], optional = true }
wasm-bindgen = { version = "0.2", optional = true }
clap = { version = "4", features = ["derive"], optional = true }

[features]
python = ["pyo3"]
wasm = ["wasm-bindgen"]
cli = ["clap"]
ffi = []
```

### Поэтапный план

#### Phase 5.1 — Rust Core (transport + protocol)

- [ ] Cargo workspace setup (`icom-lan-core`, `icom-lan-cli`, `icom-lan-py`)
- [ ] UDP transport на tokio (connect, ping, retransmit, sequence tracking)
- [ ] Discovery handshake (Are You There → I Am Here → Are You Ready)
- [ ] Authentication (credential encoding, login, token, conninfo)
- [ ] CI-V command encoding/decoding (BCD, frame builder/parser)
- [ ] IcomRadio struct с async API
- [ ] Unit tests (tokio::test)
- [ ] Integration test с IC-7610

#### Phase 5.2 — CLI (standalone binary)

- [ ] `clap` CLI с теми же командами что Python CLI
- [ ] `icom-lan status / freq / mode / meter / ptt / cw / discover`
- [ ] Cross-compile: macOS (arm64, x86_64), Linux (arm64, x86_64), Windows
- [ ] GitHub Releases с бинарниками
- [ ] Homebrew formula: `brew install morozsm/tap/icom-lan`

#### Phase 5.3 — Python bindings (PyO3)

- [ ] PyO3 + maturin setup
- [ ] `IcomRadio` class с async support (pyo3-asyncio)
- [ ] Drop-in замена Python-версии: тот же API, тот же `from icom_lan import IcomRadio`
- [ ] PyPI publish как native wheel (`pip install icom-lan` → Rust binary внутри)
- [ ] Бенчмарки: Python-pure vs Rust+PyO3

#### Phase 5.4 — Audio (Rust-native Opus)

- [ ] Opus decode/encode через `opus` crate (или `audiopus`)
- [ ] Audio port (50003) handling в transport
- [ ] Jitter buffer
- [ ] Callback API для RX, push API для TX
- [ ] Full-duplex audio
- [ ] Latency benchmark vs Python+opuslib

#### Phase 5.5 — WASM (browser control)

- [ ] `wasm-bindgen` + `wasm-pack` build
- [ ] WebSocket → UDP proxy (WASM не может UDP напрямую)
- [ ] Minimal web UI: частота, режим, S-meter, waterfall (?)
- [ ] npm package: `@icom-lan/web`

#### Phase 5.6 — C FFI

- [ ] `cbindgen` для генерации C header
- [ ] Shared library (.so / .dylib / .dll)
- [ ] Пример интеграции с GNU Radio
- [ ] Пример интеграции с SDR++

### Оценка трудозатрат

| Этап | Сложность | Время (ориентир) |
|------|-----------|-----------------|
| 5.1 Core | Средняя | 2–3 недели |
| 5.2 CLI | Лёгкая | 2–3 дня |
| 5.3 PyO3 | Средняя | 1 неделя |
| 5.4 Audio | Высокая | 2–3 недели |
| 5.5 WASM | Высокая | 2 недели |
| 5.6 C FFI | Средняя | 3–5 дней |

### Структура репозитория (Rust)

```
icom-lan/
├── crates/
│   ├── icom-lan-core/        # Ядро: transport, protocol, commands, audio
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── transport.rs
│   │   │   ├── protocol.rs
│   │   │   ├── commands.rs
│   │   │   ├── auth.rs
│   │   │   ├── audio.rs
│   │   │   └── error.rs
│   │   └── Cargo.toml
│   ├── icom-lan-cli/         # CLI binary
│   │   ├── src/main.rs
│   │   └── Cargo.toml
│   ├── icom-lan-py/          # Python bindings (PyO3)
│   │   ├── src/lib.rs
│   │   ├── pyproject.toml
│   │   └── Cargo.toml
│   └── icom-lan-wasm/        # WASM bindings
│       ├── src/lib.rs
│       └── Cargo.toml
├── Cargo.toml                # workspace
├── Cargo.lock
├── docs/                     # общая документация (текущая)
├── tests/                    # integration tests
└── README.md
```

### Open Questions

- **Mono-repo или separate repo?** Вариант: `icom-lan` (Python, текущий) + `icom-lan-rs` (Rust). Или mono-repo с Python в `python/` subdir.
- **Minimum Rust version (MSRV)?** Предлагаю 1.75+ (async fn in traits стабилизирован).
- **Async runtime:** tokio (стандарт де-факто) или async-std? → tokio.
- **Opus crate:** `opus` (C bindings) или `opus-rs` или pure-Rust `symphonia`? → C bindings (`opus`) для совместимости с libopus.

---

## Phase 6 — Spectrum & Waterfall

**Goal:** Парсинг waterfall/spectrum данных, которые радио уже отправляет (cmd `0x27`). Сейчас мы их выбрасываем в `_send_civ_raw` — пора начать использовать.

### Контекст

IC-7610 непрерывно шлёт spectrum-данные через CI-V порт (50002) — это те самые пакеты с `cmd=0x27`, которые мы фильтруем. Они содержат:
- Scope данные (амплитуды FFT-бинов)
- Центральная частота, span
- Метаданные отображения (ref level, edge frequencies)
- Два scope — Main и Sub (у IC-7610 два независимых приёмника)

### Ключевые ссылки в wfview

- `rigcommander.cpp` → `parseSpectrum()` — парсинг spectrum-пакетов
- CI-V cmd `0x27`, sub `0x00` — scope data
- CI-V cmd `0x27`, sub `0x10`/`0x11` — scope on/off
- Формат: заголовок (division, center freq, span) + массив байтов (амплитуды 0-200)

### Tasks

- [ ] Изучить формат spectrum-пакетов в `rigcommander.cpp` → `parseSpectrum()`
- [ ] Reverse-engineer `0x27` sub-commands (scope enable/disable, mode, speed)
- [ ] Парсер spectrum data → структура `SpectrumFrame(center_freq, span, data: list[int])`
- [ ] Callback API: `radio.on_spectrum(callback)` — continuous stream
- [ ] Scope control: `radio.set_scope(enabled=True, mode="center", span=100_000)`
- [ ] Dual scope support (Main + Sub для IC-7610)
- [ ] Ring buffer для последних N фреймов (для waterfall отображения)
- [ ] Бенчмарк: сколько spectrum-пакетов в секунду шлёт IC-7610

### API Design

```python
from icom_lan import IcomRadio, SpectrumFrame

def on_spectrum(frame: SpectrumFrame):
    print(f"Center: {frame.center_freq/1e6:.3f} MHz, "
          f"Span: {frame.span/1e3:.0f} kHz, "
          f"Bins: {len(frame.data)}, "
          f"Peak: {max(frame.data)}")

async with IcomRadio(...) as radio:
    # Enable spectrum stream
    await radio.set_scope(enabled=True)
    radio.on_spectrum(on_spectrum)

    # ... do work, spectrum data flows via callback ...

    await radio.set_scope(enabled=False)
```

### Data Structure

```python
@dataclass
class SpectrumFrame:
    scope: int              # 0 = Main, 1 = Sub
    center_freq: int        # Hz
    span: int               # Hz
    edge_low: int           # Hz (left edge)
    edge_high: int          # Hz (right edge)
    data: list[int]         # amplitude values (0-200 per bin)
    division: int           # number of divisions
    out_of_range: bool      # scope data out of range flag
```

---

## Phase 7 — Web UI 🌐

**Goal:** Полноценный web-интерфейс для управления радио. Замена RS-BA1 / wfview — open source, в браузере.

### Зачем

- **RS-BA1** — платный ($100+), Windows only, закрытый
- **wfview** — GPLv3, Qt desktop app, тяжёлый
- **icom-lan Web UI** — MIT, в браузере, zero install, работает с телефона

### Архитектура

```
┌──────────────┐     WebSocket      ┌──────────────────┐
│   Browser    │◄──────────────────►│   icom-lan       │
│              │                    │   server          │
│  ┌────────┐  │                    │  ┌────────────┐   │     UDP
│  │ React/ │  │                    │  │ WebSocket  │   │◄──────────►  Radio
│  │ Canvas │  │                    │  │ ↔ UDP      │   │   50001-3
│  │ WebGL  │  │                    │  │ proxy      │   │
│  └────────┘  │                    │  └────────────┘   │
└──────────────┘                    └──────────────────┘
```

Или с WASM (Phase 5.5):

```
┌────────────────────────────────┐
│          Browser               │
│  ┌──────────┐  ┌────────────┐  │     WebSocket→UDP
│  │ WASM     │  │ UI         │  │◄────────────────►  Radio
│  │ icom-lan │  │ (React/    │  │     (proxy)
│  │ core     │  │  Canvas)   │  │
│  └──────────┘  └────────────┘  │
└────────────────────────────────┘
```

### Features

#### MVP (Phase 7.1)

- [ ] Frequency display + tuning (click/drag/scroll/keyboard)
- [ ] Mode selector (USB/LSB/CW/AM/FM)
- [ ] S-meter bar (real-time)
- [ ] PTT button (with safety confirm)
- [ ] Power/SWR/ALC meters
- [ ] VFO A/B switch, split indicator
- [ ] Mobile-responsive layout

#### Waterfall (Phase 7.2)

- [ ] Real-time spectrum display (Canvas 2D или WebGL)
- [ ] Waterfall (scrolling history)
- [ ] Click-to-tune на waterfall
- [ ] Zoom/pan по частоте
- [ ] Color schemes (classic, viridis, plasma)
- [ ] Dual waterfall для IC-7610 (Main + Sub)
- [ ] FPS control (10/20/30 fps)

#### Audio (Phase 7.3)

- [ ] RX audio через Web Audio API (Opus → PCM → speakers)
- [ ] TX audio через getUserMedia() (mic → Opus → radio)
- [ ] VOX mode (auto PTT по аудио)
- [ ] Audio level meters (RX/TX)
- [ ] Noise reduction (Web Audio filters)

#### Advanced (Phase 7.4)

- [ ] Band stack (быстрое переключение диапазонов с запоминанием)
- [ ] Memory channels (список сохранённых частот)
- [ ] Logbook integration (ADIF export)
- [ ] DX cluster overlay на waterfall
- [ ] Multi-user (несколько браузеров к одному серверу)
- [ ] PWA (installable, offline capable)
- [ ] Dark/light theme

### Tech Stack (предварительно)

| Компонент | Технология |
|-----------|-----------|
| Frontend | React + TypeScript (или Svelte) |
| Waterfall | Canvas 2D / WebGL (gpu-accelerated) |
| Audio | Web Audio API + Opus.js (или WASM decoder) |
| Transport | WebSocket (browser ↔ server) |
| Server | Rust (axum) или Python (FastAPI + websockets) |
| State | Zustand / signals (reactive) |
| Build | Vite |

### Вдохновение

- [OpenWebRX](https://www.openwebrx.de/) — web SDR с waterfall (отличный UX)
- [WebSDR](http://www.websdr.org/) — pioneer web-based radio
- [KiwiSDR](http://kiwisdr.com/) — browser-based SDR receiver
- [wfview](https://wfview.org/) — desktop reference (feature set)
- [RS-BA1](https://www.icomjapan.com/lineup/products/RS-BA1/) — Icom's official (UX anti-pattern 😅)

### Оценка

| Этап | Сложность | Время |
|------|-----------|-------|
| 7.1 MVP (controls) | Средняя | 1–2 недели |
| 7.2 Waterfall | Высокая | 2–3 недели |
| 7.3 Audio | Высокая | 2–3 недели |
| 7.4 Advanced | Очень высокая | ongoing |

---

## The Grand Vision 🔭

```
Phase 1-2:  Python CLI + API          ✅ Done
Phase 3:    Audio streaming            ← next
Phase 4:    PyPI, polish
Phase 5:    Rust core + bindings
Phase 6:    Spectrum/waterfall data
Phase 7:    Web UI — the full package
            ─────────────────────────
            Open-source RS-BA1 killer
            In your browser
            From your phone
            MIT licensed
            73 de KN4KYD
```

---

*Created: 2026-02-25*
*Last updated: 2026-02-25*

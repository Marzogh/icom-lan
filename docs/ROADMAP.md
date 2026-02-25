# Roadmap

## Current State: v0.2.0 (Python)

- ✅ Phase 1 — Transport (UDP, auth, keep-alive, dual-port)
- ✅ Phase 2 — CI-V Commands (frequency, mode, power, meters, PTT, CW, VFO, split)
- ⬜ Phase 3 — Audio Streaming
- ⬜ Phase 4 — Polish & Publish
- ⬜ Phase 5 — Rust Core

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

*Created: 2026-02-25*
*Last updated: 2026-02-25*

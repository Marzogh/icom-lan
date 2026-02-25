# CLAUDE.md — Claude Code Instructions

## Context

This is `icom-lan`, a Python library for controlling Icom ham radio transceivers over LAN (UDP).
The Icom LAN protocol is proprietary and undocumented. We reverse-engineer it from wfview source code
in `references/wfview/` (GPLv3). Our implementation is MIT-licensed and written from scratch.

Read `AGENTS.md` first — it has the full project philosophy and structure.
Read `docs/PROJECT.md` for current phase and protocol documentation.

## Development Rules

### TDD — No Exceptions
```
1. Write a failing test
2. Write minimal code to pass
3. Refactor
4. Repeat
```
Never write library code without a corresponding test. If you're tempted to skip the test, write it first anyway.

### Testing Strategy
- `tests/test_protocol.py` — Pure unit tests. Parse known byte sequences, verify output.
  These are the most important tests — protocol correctness is everything.
- `tests/test_transport.py` — Mock UDP socket, verify handshake sequences.
- `tests/test_commands.py` — CI-V encode/decode with known values.
- `tests/test_radio.py` — High-level API tests with mocked transport.
- `tests/integration/` — Real radio tests. Never run automatically. Mark with `@pytest.mark.integration`.

### Mock Strategy
Use `unittest.mock` or `pytest-mock`. For UDP:
```python
@pytest.fixture
def mock_socket():
    """Simulate Icom radio UDP responses."""
    with patch('asyncio.DatagramProtocol') as mock:
        yield mock
```
Build a `FakeRadio` class in `tests/conftest.py` that responds like a real IC-7610.

### Code Style
- Python 3.11+ (use modern syntax: `match`, `type`, union with `|`)
- `ruff` for linting and formatting
- `mypy --strict` for type checking
- Google-style docstrings in English
- Module-level `__all__` in every file
- Private helpers prefixed with `_`

### Error Handling
- Custom exceptions in `exceptions.py`: `ConnectionError`, `AuthenticationError`, `CommandError`, `TimeoutError`
- All inherit from `IcomLanError`
- Never catch and swallow exceptions silently
- Timeout on every network operation (default 5s, configurable)

### Logging
```python
import logging
logger = logging.getLogger(__name__)
```
- DEBUG: packet hex dumps, timing
- INFO: connect/disconnect, frequency changes
- WARNING: retransmits, unexpected packets
- ERROR: connection lost, auth failed

### Dependencies
- **Core:** zero dependencies (stdlib only: asyncio, struct, logging, enum, dataclasses)
- **Audio:** `opuslib` (optional, declared in `[project.optional-dependencies]`)
- **Dev:** pytest, pytest-asyncio, mypy, ruff

## Protocol Implementation Notes

### Byte Order
Icom protocol is **little-endian** for most fields. Use `struct.pack('<H', value)`.
Exception: CI-V frequency data is **BCD-encoded** (not standard int).

### Packet Structure (from packettypes.h)
Every UDP packet starts with a fixed header. Study `packettypes.h` thoroughly before writing any code.
Key types: CONTROL, CIV, AUDIO, RETRANSMIT, PING, CONNINFO, TOKEN, LOGIN, STATUS.

### CI-V Encoding
Frequencies are BCD: 14.074.000 Hz = `0x00 0x00 0x74 0x40 0x01` (right to left, pairs of digits).
Study `icomcommander.cpp` for the full encoding/decoding logic.

### Keep-alive
The radio drops the connection if it doesn't receive periodic pings.
Interval: ~500ms for control, ~100ms for audio.
Missing 3-5 pings = disconnect.

### Authentication Flow
1. Send "are you there" packet
2. Radio responds with its ID
3. Send login packet (username + password, XOR-encoded, not encrypted)
4. Radio responds with auth status + token
5. Start keep-alive loop

## Key Files to Study (in order)
1. `references/wfview/include/packettypes.h` — Start here. All packet structures.
2. `references/wfview/src/radio/icomudpbase.cpp` — Base UDP mechanics.
3. `references/wfview/src/radio/icomudphandler.cpp` — Login/auth sequence.
4. `references/wfview/src/radio/icomudpcivdata.cpp` — CI-V wrapping.
5. `references/wfview/src/radio/icomcommander.cpp` — CI-V command reference (big file, skim).

## Commands

```bash
# Run tests
pytest

# Run with verbose
pytest -v

# Run only unit tests (no real radio)
pytest -m "not integration"

# Type check
mypy src/

# Lint & format
ruff check src/ tests/
ruff format src/ tests/
```

# Contributing

Contributions are welcome! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/morozsm/icom-lan.git
cd icom-lan
pip install -e ".[dev]"
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv sync --extra dev
```

## Running Tests

```bash
# All unit tests
pytest tests/test_*.py

# With verbose output
pytest tests/test_*.py -v

# Specific test file
pytest tests/test_commands.py

# Specific test
pytest tests/test_commands.py::test_get_frequency_builds_correct_frame
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures (FakeRadio, packet builders)
├── test_auth.py         # Credential encoding, login/conninfo packets
├── test_commands.py     # CI-V frame building and parsing
├── test_protocol.py     # Header parsing/serialization
├── test_radio.py        # IcomRadio high-level API (mocked transport)
├── test_transport.py    # IcomTransport (mocked UDP)
└── integration/         # Real hardware tests (require a radio)
    ├── test_connect.py
    └── test_get_freq.py
```

Unit tests use mocked transports — **no radio required**. Integration tests are in `tests/integration/` and require actual hardware.

## Code Style

- **Type annotations** on all public functions
- **Docstrings** on all public classes and methods (Google/NumPy style)
- Follow existing code patterns
- No external dependencies for the core library (stdlib only)

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add AGC level control
fix: handle timeout during conninfo exchange
docs: add IC-705 setup instructions
test: add VFO swap command test
chore: bump version to 0.3.0
```

## Adding a New CI-V Command

1. **Add the command builder** in `commands.py`:

    ```python
    def get_agc(to_addr: int = IC_7610_ADDR, from_addr: int = CONTROLLER_ADDR) -> bytes:
        """Build a 'get AGC' CI-V command."""
        return build_civ_frame(to_addr, from_addr, 0x16, sub=0x12)
    ```

2. **Add a response parser** if needed (also in `commands.py`)

3. **Add the high-level method** in `radio.py`:

    ```python
    async def get_agc(self) -> int:
        """Get the AGC level."""
        self._check_connected()
        civ = get_agc(to_addr=self._radio_addr)
        resp = await self._send_civ_raw(civ)
        return parse_level_response(resp)
    ```

4. **Add a CLI command** in `cli.py` if user-facing

5. **Write tests** in `tests/test_commands.py` and `tests/test_radio.py`

6. **Update documentation**:
    - `docs/guide/commands.md` — user-facing command docs
    - `docs/api/radio.md` — API reference
    - `docs/api/commands.md` — low-level command reference

## Adding a New Radio Model

1. Look up the radio's default CI-V address
2. Test basic operations (frequency, mode, meters)
3. Document any model-specific behavior
4. Add to the radios table in `docs/guide/radios.md`
5. Add the CI-V address constant in `commands.py` if desired

## Reporting Bugs

[Open an issue](https://github.com/morozsm/icom-lan/issues/new) with:

- Radio model and firmware version
- Python version and OS
- Steps to reproduce
- Debug log output (`logging.basicConfig(level=logging.DEBUG)`)
- Expected vs actual behavior

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes with tests
4. Ensure all tests pass: `pytest tests/test_*.py`
5. Commit with conventional commit message
6. Open a PR against `main`

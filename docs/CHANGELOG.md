# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-02-25

### Added

- **CLI tool** (`icom-lan`) with commands: `status`, `freq`, `mode`, `power`, `meter`, `ptt`, `cw`, `power-on`, `power-off`, `discover`
- **VFO control**: `select_vfo()`, `vfo_equalize()`, `vfo_exchange()`, `set_split_mode()`
- **RF controls**: `set_attenuator()`, `set_preamp()`
- **CW keying**: `send_cw_text()`, `stop_cw_text()` — with auto-chunking
- **Power control**: `power_control()` for remote power on/off
- **Network discovery**: broadcast-based autodiscovery of Icom radios
- `__main__.py` for `python -m icom_lan` execution
- JSON output option (`--json`) for CLI commands
- Frequency parsing with k/m suffix (`14.074m`, `7074k`)

### Changed

- Bumped version to 0.2.0

## [0.1.0] — 2026-02-24

### Added

- **Transport layer**: async UDP connection with discovery handshake
- **Dual-port architecture**: control port (50001) + CI-V port (50002)
- **Full authentication**: login → token ack → conninfo exchange → status
- **CI-V commands**: `get/set_frequency()`, `get/set_mode()`, `get/set_power()`
- **Meters**: `get_s_meter()`, `get_swr()`, `get_alc()`
- **PTT**: `set_ptt(on/off)`
- **Keep-alive**: automatic ping loop (500ms) and retransmit handling
- **Sequence tracking**: gap detection and retransmit requests
- **Context manager**: `async with IcomRadio(...) as radio:`
- **Custom exceptions**: `ConnectionError`, `AuthenticationError`, `CommandError`, `TimeoutError`
- **Type annotations**: full `py.typed` marker
- **151 unit tests** with mocked transport (no hardware required)
- Integration tests for IC-7610

### Technical

- Clean-room implementation of the Icom LAN UDP protocol
- Protocol knowledge from wfview reverse engineering (GPLv3 reference only)
- BCD frequency encoding/decoding
- Icom credential substitution-table obfuscation
- Waterfall/echo filtering in CI-V response handling
- GUID echo in conninfo exchange (required for CI-V port discovery)

[0.2.0]: https://github.com/morozsm/icom-lan/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/morozsm/icom-lan/releases/tag/v0.1.0

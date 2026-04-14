# icom-lan 0.16.1

**Release date:** April 14, 2026

## Highlights

Patch release fixing a crash when LAN discovery runs without network connectivity,
plus CI improvements (strict mypy compliance, dynamic badges).

## Fixed

- **LAN discovery crash** — `OSError: [Errno 65] No route to host` when Wi-Fi is
  off or no network route exists no longer produces a raw Python traceback.
  The CLI now prints a clear error and suggests `--host <IP>`.
- **CI strict mypy** — resolved `no-any-return` in `radio_poller.py` for the
  `mypy --strict src/icom_lan/web` boundary check that runs in CI.
- **Dynamic CI badges** — tests (count), version, and mypy badges in README now
  auto-update on every push to main via gist-backed shields.io endpoints.

## Install / Upgrade

```bash
pip install icom-lan==0.16.1
# or upgrade:
pip install --upgrade icom-lan
```

# icom-lan 0.15.1

**Release date:** April 10, 2026

## Highlights

Web UI v2 (RadioLayout) is now the default interface for new visitors and fresh installs.
The redesigned layout features a professional two-sidebar arrangement with drag-and-drop
panel reorder, improved spectrum/waterfall integration, and better mobile responsiveness.

## What's Changed

- **Web UI v2 is now the default layout.** Previously, new visitors saw v1 (AppShell).
  Now v2 (RadioLayout) loads by default.
- Users who previously selected v1 are **not affected** — their choice is persisted
  in `localStorage` and respected.
- Switch between versions at any time with `?ui=v1` or `?ui=v2` in the URL.

## Breaking Changes

None. This is a default-change only — no APIs, protocols, or configurations are affected.

## Install / Upgrade

```bash
pip install icom-lan==0.15.1
# or upgrade:
pip install --upgrade icom-lan
```

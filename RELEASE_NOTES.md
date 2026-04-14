# icom-lan 0.16.0

**Release date:** April 14, 2026

## Highlights

This release introduces a pluggable DSP pipeline for real-time audio processing,
a CW auto-tuner with FFT peak detection, UDP service discovery for companion apps,
and a fully unified frontend architecture with skin support. 121 commits since v0.15.1,
with 54 new features, comprehensive test coverage, and zero mypy/ruff errors.

## What's New

### DSP Pipeline (Epic #682)
Pluggable audio processing framework: `DSPNode` protocol, `DSPPipeline` engine,
`NRScipyNode` (spectral subtraction noise reduction via scipy FFT), `TapRegistry`
for multi-consumer PCM analysis, and a `[dsp]` optional dependency group.

### CW Auto Tuner (#675, #677, #678)
FFT-based peak detection engine for automatic CW signal tuning, wired through
the backend with a restored AUTO TUNE button in the Web UI.

### AudioAnalyzer (#679)
Realtime SNR estimation from the PCM audio stream.

### UDP Discovery Responder
Companion apps broadcast `ICOM_LAN_DISCOVER` on UDP port 8470 and receive a JSON
unicast response with server URL, version, and radio status. Disable with `--no-discovery`.

### Unified Frontend Architecture (Epics #647–#665)
`FrontendRuntime` singleton, skin registry, runtime adapters, self-wired panels
(AGC, Mode, Antenna, CW, DSP, TX, Filter, and more), eslint import boundary
enforcement, and LCD/mobile layout migration to the unified runtime path.

### Multi-Radio Enhancements
- **SUB receiver** — TOML commands, receiver routing, level polling
- **TX meters** — ALC, Power, COMP, SWR polling during transmit
- **IC-7300** — segmented BCD filter encoding, scope markers
- **Yaesu FTX-1** — IF bulk query, clarifier, APF, CW spot, power switch, data mode

### Infrastructure
- Scope backpressure with adaptive poller gap and backlog shedding
- Initial state fetch on connect/reconnect
- Cross-sidebar drag with localStorage persistence
- Single version source (pyproject.toml via `importlib.metadata`)
- All mypy and ruff errors resolved (0 errors across 144 source files)

## Breaking Changes

None.

## Install / Upgrade

```bash
pip install icom-lan==0.16.0
# or upgrade:
pip install --upgrade icom-lan
```

## Commits

```
bed2e1d fix: resolve all mypy and ruff errors for release readiness
b6ccd3f feat: UDP discovery responder for companion app auto-detection
87e4b49 feat(#678): restore AUTO TUNE button with software CW auto-tune
ea3085d feat(#679): AudioAnalyzer — realtime SNR estimation from PCM stream
abf75dd feat(#677): wire cw_auto_tune command through backend
2ecac12 fix(#636): LCD layout adapts to reduced viewport height
70b5305 refactor(#594): extract DspPanel + CwPanel logic to panel-logic modules
a716e8a feat(#682): hook DSP pipeline into audio stream + [dsp] optional dep
a3ea766 feat(#682): NRScipyNode + inter-node resample utility
6db3d53 feat(#682): PassthroughNode + GainNode — base DSP nodes
7d09410 feat(#682): TapRegistry — multi-consumer PCM analysis bus
2866802 feat(#682): DSPNode Protocol + DSPPipeline + exceptions
20bbe28 feat(#675): CwAutoTuner engine — FFT peak detection module (#680)
2105493 feat(#665): SystemController — centralize all HTTP system actions
c536036 chore(#653): cutover to unified frontend architecture
776c372 feat(#648): introduce FrontendRuntime shell and adapter boundary
edd3f57 feat(#647): add eslint import boundary guardrails
40e3e08 feat(#533): wire scope shedding to transport pressure callback
f283300 feat(#532): re-run _fetch_initial_state on reconnect
7269574 feat(#532): call _fetch_initial_state() at end of connect()
5843a75 feat(#573): dynamic panel rendering
203157a feat(#567): cross-sidebar drag — move panels between sidebars
9d3443b feat(#560): poll CW parameters in slow loop
64027f3 feat(#559): poll TX meters during transmit
... and 97 more commits
```

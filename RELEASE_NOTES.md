# icom-lan 0.16.3

**Release date:** April 16, 2026

## Fixed

- **Web UI:** resolve 33 issues across controls, sync, errors, layout, a11y, and
  performance — wiring layer (DW/VFO targeting), control panels (freq keyboard,
  ATU/ATT/APF), canvas perf (rAF idle loop, DX cap, gradient cache), error
  notifications (Toast mounted in v2 layouts), connection state (WS reconnect,
  scope/audio indicators), waterfall resize preservation (#693, #694–#702)
- **DSP pipeline:** add sample rate validation and auto-resampling for RNNoise (#692)
- **Audio broadcaster:** resolve subscriber leak and pong-timeout loop (#687, #690)
- **Audio WebSocket:** fix crash loop on PTT (#684, #688)
- **CLI:** hard errors for invalid inputs, silent ignores, startup ordering (#689)
- **CLI:** hard errors for explicitly requested features with validation (#686)

## Install / Upgrade

```bash
pip install icom-lan==0.16.3
# or upgrade:
pip install --upgrade icom-lan
```

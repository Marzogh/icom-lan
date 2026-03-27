<script lang="ts">
  import { onMount } from 'svelte';

  interface Props {
    /** FFT pixel data from AudioFftScope (0-160 range) */
    data: Uint8Array | null;
    /** Register a push callback for streaming updates */
    onRegisterPush?: (fn: (data: Uint8Array) => void) => void;
    /** Filter passband width in Hz (e.g. 2400 for SSB) */
    filterWidth?: number;
    /** IF shift in Hz */
    ifShift?: number;
    /** Manual notch active */
    manualNotch?: boolean;
    /** Manual notch frequency (0-255 raw) */
    notchFreq?: number;
    /** Audio sample rate */
    sampleRate?: number;
    /** Current mode */
    mode?: string;
    /** Compact mode (embedded in LCD) */
    compact?: boolean;
  }

  let {
    data,
    onRegisterPush,
    filterWidth = 2400,
    ifShift = 0,
    manualNotch = false,
    notchFreq = 128,
    sampleRate = 48000,
    mode = 'USB',
    compact = false,
  }: Props = $props();

  let canvas: HTMLCanvasElement;
  let cssWidth = $state(1);
  let cssHeight = $state(1);
  let rafId = 0;
  let visible = true;
  let latestPixels: Uint8Array | null = null;

  // ── Dark scope palette (like real FTX-1 scope) ──
  const SCOPE_BG = '#0C0C0C';
  const BAR_COLOR_LO = 'rgba(160, 165, 170, 0.6)';   // gray bars (low)
  const BAR_COLOR_HI = 'rgba(200, 205, 210, 0.85)';   // brighter bars (high)
  const FILTER_ARC_COLOR = '#FFD700';                   // golden yellow
  const FILTER_GLOW = 'rgba(255, 160, 0, 0.15)';       // orange glow under arc
  const BORDER_COLOR = 'rgba(140, 150, 160, 0.3)';     // subtle border highlight

  // ── Smoothing ──
  let smoothed: Float32Array | null = null;
  const SMOOTH_ATTACK = 0.35;
  const SMOOTH_DECAY = 0.12;

  function draw(): void {
    if (!visible) { rafId = 0; return; }
    const pixels = latestPixels ?? data;
    let w = cssWidth;
    let h = cssHeight;
    if ((w <= 1 || h <= 1) && canvas) {
      w = canvas.clientWidth || canvas.parentElement?.clientWidth || 1;
      h = canvas.clientHeight || canvas.parentElement?.clientHeight || 1;
      if (w > 1 && h > 1) {
        cssWidth = w;
        cssHeight = h;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
        const ctx = canvas.getContext('2d');
        ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    }
    if (canvas && w > 1 && h > 1) {
      const ctx = canvas.getContext('2d');
      if (ctx) renderScope(ctx, pixels, w, h);
    }
    rafId = requestAnimationFrame(draw);
  }

  function renderScope(
    ctx: CanvasRenderingContext2D,
    pixels: Uint8Array | null,
    w: number,
    h: number,
  ): void {
    const maxVal = 160;
    const halfBw = sampleRate / 2;

    // ── Dark background ──
    ctx.fillStyle = SCOPE_BG;
    ctx.fillRect(0, 0, w, h);

    // ── Subtle border highlight ──
    ctx.strokeStyle = BORDER_COLOR;
    ctx.lineWidth = 0.5;
    ctx.strokeRect(0.5, 0.5, w - 1, h - 1);

    // ── Filter passband arc (golden U-shape at top) ──
    const filterCenterX = w / 2 + (ifShift / halfBw) * (w / 2);
    const filterHalfW = (filterWidth / 2 / halfBw) * (w / 2);

    // Arc: U-shape hanging from top
    const arcLeft = filterCenterX - filterHalfW;
    const arcRight = filterCenterX + filterHalfW;
    const arcDepth = h * 0.35; // how deep the U dips

    // Glow fill under the arc
    const glowGrad = ctx.createLinearGradient(0, 0, 0, arcDepth + 5);
    glowGrad.addColorStop(0, FILTER_GLOW);
    glowGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.moveTo(arcLeft, 0);
    ctx.quadraticCurveTo(filterCenterX, arcDepth * 2, arcRight, 0);
    ctx.lineTo(arcRight, 0);
    ctx.closePath();
    ctx.fill();

    // Arc line
    ctx.strokeStyle = FILTER_ARC_COLOR;
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(255, 200, 0, 0.4)';
    ctx.shadowBlur = 4;
    ctx.beginPath();
    ctx.moveTo(arcLeft, 0);
    ctx.quadraticCurveTo(filterCenterX, arcDepth * 2, arcRight, 0);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Edges from arc down to bottom (angled sides)
    ctx.strokeStyle = 'rgba(255, 215, 0, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(arcLeft, 0);
    ctx.lineTo(arcLeft - w * 0.03, h);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(arcRight, 0);
    ctx.lineTo(arcRight + w * 0.03, h);
    ctx.stroke();

    // ── Manual notch (sharp V) ──
    if (manualNotch) {
      const notchX = (notchFreq / 255) * w;
      const notchDepth = h * 0.5;
      ctx.strokeStyle = 'rgba(255, 80, 80, 0.7)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(notchX - w * 0.015, 0);
      ctx.lineTo(notchX, notchDepth);
      ctx.lineTo(notchX + w * 0.015, 0);
      ctx.stroke();
    }

    // ── FFT Spectrum bars ──
    drawFftBars(ctx, pixels, w, h, maxVal);

    // ── Thin baseline ──
    ctx.strokeStyle = 'rgba(160, 165, 170, 0.2)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(0, h - 1);
    ctx.lineTo(w, h - 1);
    ctx.stroke();
  }

  function drawFftBars(
    ctx: CanvasRenderingContext2D,
    pixels: Uint8Array | null,
    w: number,
    h: number,
    maxVal: number,
  ): void {
    const barWidth = 1;
    const barGap = 1;
    const barStep = barWidth + barGap;
    const numBars = Math.floor(w / barStep);

    if (!smoothed || smoothed.length !== numBars) {
      smoothed = new Float32Array(numBars);
    }

    for (let i = 0; i < numBars; i++) {
      const x = i * barStep;

      let rawAmp: number;
      if (pixels && pixels.length > 0) {
        const pixIdx = Math.floor((i / numBars) * pixels.length);
        rawAmp = Math.min(pixels[pixIdx], maxVal) / maxVal;
      } else {
        // No data: random low noise floor
        rawAmp = Math.random() * 0.08 + 0.02;
      }

      // Smooth
      const prev = smoothed[i];
      if (rawAmp > prev) {
        smoothed[i] = prev + (rawAmp - prev) * SMOOTH_ATTACK;
      } else {
        smoothed[i] = prev + (rawAmp - prev) * SMOOTH_DECAY;
      }

      const amp = smoothed[i];
      const barH = amp * h * 0.85;
      if (barH < 1) continue;

      const y = h - barH;

      // Color: brighter for taller bars
      ctx.fillStyle = amp > 0.4 ? BAR_COLOR_HI : BAR_COLOR_LO;
      ctx.fillRect(x, y, barWidth, barH);
    }
  }

  function onVisibilityChange() {
    visible = !document.hidden;
    if (visible && rafId === 0) rafId = requestAnimationFrame(draw);
  }

  onMount(() => {
    onRegisterPush?.((pixels: Uint8Array) => {
      latestPixels = pixels;
    });

    document.addEventListener('visibilitychange', onVisibilityChange);
    rafId = requestAnimationFrame(draw);

    const ro = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (!rect) return;
      cssWidth = Math.max(1, Math.floor(rect.width));
      cssHeight = Math.max(1, Math.floor(rect.height));
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(cssWidth * dpr);
      canvas.height = Math.round(cssHeight * dpr);
      const ctx = canvas.getContext('2d');
      ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
    });
    ro.observe(canvas);

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      ro.disconnect();
      cancelAnimationFrame(rafId);
      rafId = 0;
    };
  });
</script>

<div class="amber-af-scope">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .amber-af-scope {
    width: 100%;
    height: 100%;
    position: relative;
    background: #0C0C0C;
    border-radius: 2px;
  }

  canvas {
    display: block;
    width: 100%;
    height: 100%;
  }
</style>

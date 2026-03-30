import { describe, it, expect } from 'vitest';
import {
  pbtRawToHz,
  computePbtOverlay,
  generateGridLabels,
  computeSpectrumLine,
  computeNotchX,
  type GridLabel,
  type PbtOverlay,
} from '../audio-spectrum-renderer';

// ── pbtRawToHz ───────────────────────────────────────────────────────────────

describe('pbtRawToHz', () => {
  it('returns 0 for center value (128)', () => {
    expect(pbtRawToHz(128)).toBe(0);
  });

  it('returns positive Hz for values > 128', () => {
    // (200 - 128) * (1200/128) = 72 * 9.375 = 675
    expect(pbtRawToHz(200)).toBe(675);
  });

  it('returns negative Hz for values < 128', () => {
    // (56 - 128) * (1200/128) = -72 * 9.375 = -675
    expect(pbtRawToHz(56)).toBe(-675);
  });

  it('returns max Hz at raw=255', () => {
    // (255 - 128) * (1200/128) = 127 * 9.375 = 1190.625 → rounded to 1191
    expect(pbtRawToHz(255)).toBe(1191);
  });

  it('returns -max Hz at raw=0', () => {
    // (0 - 128) * (1200/128) = -128 * 9.375 = -1200
    expect(pbtRawToHz(0)).toBe(-1200);
  });

  it('supports custom center and max', () => {
    expect(pbtRawToHz(64, 64, 600)).toBe(0);
    expect(pbtRawToHz(128, 64, 600)).toBe(600);
  });
});

// ── computePbtOverlay ────────────────────────────────────────────────────────

describe('computePbtOverlay', () => {
  it('returns centered trapezoids when PBT is at center (128/128)', () => {
    const pbt = computePbtOverlay(128, 128, 2400, 48000);
    // filterWidth=2400, bandwidth=48000, halfBw=24000
    // halfFilter=1200, shift=0
    // innerLeft = (-1200 + 0) / 24000 * 0.5 + 0.5 = -0.025 + 0.5 = 0.475
    // innerRight = (1200 + 0) / 24000 * 0.5 + 0.5 = 0.025 + 0.5 = 0.525
    expect(pbt.inner.leftX).toBeCloseTo(0.475, 3);
    expect(pbt.inner.rightX).toBeCloseTo(0.525, 3);
    expect(pbt.outer.leftX).toBeCloseTo(0.475, 3);
    expect(pbt.outer.rightX).toBeCloseTo(0.525, 3);
  });

  it('shifts inner trapezoid when pbtInner > 128', () => {
    const pbt = computePbtOverlay(200, 128, 2400, 48000);
    // innerHz = (200-128) * (1200/128) = 675
    // innerLeft = (-1200 + 675) / 24000 * 0.5 + 0.5 = -525/24000*0.5 + 0.5
    expect(pbt.inner.leftX).toBeGreaterThan(pbt.outer.leftX);
    expect(pbt.inner.rightX).toBeGreaterThan(pbt.outer.rightX);
  });

  it('intersection is narrower than both when PBTs diverge', () => {
    // Inner shifted right, outer shifted left → intersection is small
    const pbt = computePbtOverlay(200, 56, 2400, 48000);
    const innerWidth = pbt.inner.rightX - pbt.inner.leftX;
    const intWidth = pbt.intersection.rightX - pbt.intersection.leftX;
    expect(intWidth).toBeLessThan(innerWidth);
  });

  it('intersection collapses to zero when PBTs don\'t overlap', () => {
    // Extreme PBT values with narrow filter: inner far right, outer far left
    const pbt = computePbtOverlay(255, 0, 500, 48000);
    const intWidth = pbt.intersection.rightX - pbt.intersection.leftX;
    expect(intWidth).toBeCloseTo(0, 1);
  });

  it('has slope width of 0.03', () => {
    const pbt = computePbtOverlay(128, 128, 2400, 48000);
    expect(pbt.inner.slopeWidth).toBe(0.03);
    expect(pbt.outer.slopeWidth).toBe(0.03);
  });
});

// ── generateGridLabels ───────────────────────────────────────────────────────

describe('generateGridLabels', () => {
  it('always includes center label at 0.5', () => {
    const labels = generateGridLabels(4800);
    const center = labels.find(l => l.text === '0');
    expect(center).toBeDefined();
    expect(center!.xFrac).toBe(0.5);
  });

  it('generates symmetric labels around center', () => {
    const labels = generateGridLabels(4800);
    const positive = labels.filter(l => l.xFrac > 0.5);
    const negative = labels.filter(l => l.xFrac < 0.5);
    expect(positive.length).toBe(negative.length);
    expect(positive.length).toBeGreaterThan(0);
  });

  it('formats kHz labels for large bandwidths', () => {
    const labels = generateGridLabels(48000);
    const hasK = labels.some(l => l.text.includes('k'));
    expect(hasK).toBe(true);
  });

  it('formats Hz labels for small bandwidths', () => {
    const labels = generateGridLabels(1000);
    // With 500 Hz half-bandwidth, step should be 100 or 200
    const nonCenter = labels.filter(l => l.text !== '0');
    for (const l of nonCenter) {
      // Should not have 'k' suffix for such small bandwidth
      expect(l.text.includes('k')).toBe(false);
    }
  });

  it('labels are sorted by xFrac ascending', () => {
    const labels = generateGridLabels(10000);
    for (let i = 1; i < labels.length; i++) {
      expect(labels[i].xFrac).toBeGreaterThanOrEqual(labels[i - 1].xFrac);
    }
  });

  it('all xFrac values are in [0, 1]', () => {
    const labels = generateGridLabels(3600);
    for (const l of labels) {
      expect(l.xFrac).toBeGreaterThanOrEqual(0);
      expect(l.xFrac).toBeLessThanOrEqual(1);
    }
  });
});

// ── computeSpectrumLine ──────────────────────────────────────────────────────

describe('computeSpectrumLine', () => {
  it('returns one point per pixel of canvas width', () => {
    const pixels = new Uint8Array(100);
    const points = computeSpectrumLine(pixels, 200, 100);
    expect(points.length).toBe(200);
  });

  it('returns empty array for empty pixel data', () => {
    const points = computeSpectrumLine(new Uint8Array(0), 200, 100);
    expect(points.length).toBe(0);
  });

  it('maps zero amplitude to bottom of usable area', () => {
    const pixels = new Uint8Array(10); // all zeros
    const height = 100;
    const usableH = height - 16; // GRID_MARGIN_BOTTOM = 16
    const points = computeSpectrumLine(pixels, 10, height);
    for (const p of points) {
      expect(p.y).toBe(usableH); // bottom
    }
  });

  it('maps max amplitude to top', () => {
    const pixels = new Uint8Array(10).fill(160); // max amplitude
    const points = computeSpectrumLine(pixels, 10, 100);
    for (const p of points) {
      expect(p.y).toBe(0); // top
    }
  });

  it('x coordinates span canvas width', () => {
    const pixels = new Uint8Array(50);
    const points = computeSpectrumLine(pixels, 300, 100);
    expect(points[0].x).toBe(0);
    expect(points[points.length - 1].x).toBe(299);
  });

  it('applies gain multiplier', () => {
    const pixels = new Uint8Array([40]); // 40/160 = 0.25 normally
    const noGain = computeSpectrumLine(pixels, 1, 100);
    const withGain = computeSpectrumLine(pixels, 1, 100, 2);
    // With gain=2: min(40*2, 160)/160 = 80/160 = 0.5
    expect(withGain[0].y).toBeLessThan(noGain[0].y); // higher amplitude = lower y
  });
});

// ── computeNotchX ────────────────────────────────────────────────────────────

describe('computeNotchX', () => {
  it('returns 0.5 for center notch (128)', () => {
    expect(computeNotchX(128, 48000)).toBeCloseTo(128 / 255, 3);
  });

  it('returns ~0 for notch at frequency 0', () => {
    expect(computeNotchX(0, 48000)).toBe(0);
  });

  it('returns ~1 for notch at frequency 255', () => {
    expect(computeNotchX(255, 48000)).toBe(1);
  });

  it('is proportional to raw frequency', () => {
    const x64 = computeNotchX(64, 48000);
    const x192 = computeNotchX(192, 48000);
    expect(x192 - 0.5).toBeCloseTo(0.5 - x64, 1);
  });
});

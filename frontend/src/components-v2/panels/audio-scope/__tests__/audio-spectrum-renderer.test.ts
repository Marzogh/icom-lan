import { describe, it, expect } from 'vitest';
import {
  pbtRawToHz,
  resetSmoothing,
  renderAudioSpectrum,
  type SpectrumState,
} from '../audio-spectrum-renderer';

// ── pbtRawToHz ───────────────────────────────────────────────────────────────

describe('pbtRawToHz', () => {
  it('returns 0 for center value (128)', () => {
    expect(pbtRawToHz(128)).toBe(0);
  });

  it('returns positive Hz for values > 128', () => {
    expect(pbtRawToHz(200)).toBe(675);
  });

  it('returns negative Hz for values < 128', () => {
    expect(pbtRawToHz(56)).toBe(-675);
  });

  it('returns max Hz at raw=255', () => {
    expect(pbtRawToHz(255)).toBe(1191);
  });

  it('returns -max Hz at raw=0', () => {
    expect(pbtRawToHz(0)).toBe(-1200);
  });

  it('supports custom center and max', () => {
    expect(pbtRawToHz(64, 64, 600)).toBe(0);
    expect(pbtRawToHz(128, 64, 600)).toBe(600);
  });
});

// ── resetSmoothing ───────────────────────────────────────────────────────────

describe('resetSmoothing', () => {
  it('does not throw', () => {
    expect(() => resetSmoothing()).not.toThrow();
  });

  it('can be called multiple times', () => {
    resetSmoothing();
    resetSmoothing();
  });
});

// ── renderAudioSpectrum ──────────────────────────────────────────────────────

describe('renderAudioSpectrum', () => {
  function mockCtx(): CanvasRenderingContext2D {
    const noop = () => {};
    return {
      clearRect: noop,
      fillRect: noop,
      fillText: noop,
      beginPath: noop,
      moveTo: noop,
      lineTo: noop,
      closePath: noop,
      stroke: noop,
      fill: noop,
      clip: noop,
      save: noop,
      restore: noop,
      quadraticCurveTo: noop,
      createLinearGradient: () => ({ addColorStop: noop }),
      set fillStyle(_: any) {},
      set strokeStyle(_: any) {},
      set lineWidth(_: any) {},
      set font(_: any) {},
      set textAlign(_: any) {},
    } as unknown as CanvasRenderingContext2D;
  }

  const baseState: SpectrumState = {
    pixels: new Uint8Array(100).fill(40),
    bandwidth: 3600,
    filterWidth: 2400,
    filterWidthMax: 3600,
    pbtInner: 128,
    pbtOuter: 128,
    manualNotch: false,
    notchFreq: 128,
    contour: 0,
    contourFreq: 128,
  };

  it('renders without throwing for valid state', () => {
    resetSmoothing();
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, baseState)).not.toThrow();
  });

  it('renders without throwing for null pixels', () => {
    resetSmoothing();
    const state = { ...baseState, pixels: null };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('renders without throwing for empty pixels', () => {
    resetSmoothing();
    const state = { ...baseState, pixels: new Uint8Array(0) };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('renders with PBT active', () => {
    resetSmoothing();
    const state = { ...baseState, pbtInner: 200, pbtOuter: 56 };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('renders with manual notch', () => {
    resetSmoothing();
    const state = { ...baseState, manualNotch: true, notchFreq: 100 };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('renders with contour active', () => {
    resetSmoothing();
    const state = { ...baseState, contour: 128, contourFreq: 100 };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('handles very small canvas', () => {
    resetSmoothing();
    expect(() => renderAudioSpectrum(mockCtx(), 10, 10, baseState)).not.toThrow();
  });

  it('handles max amplitude pixels', () => {
    resetSmoothing();
    const state = { ...baseState, pixels: new Uint8Array(100).fill(160) };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('handles narrow filter', () => {
    resetSmoothing();
    const state = { ...baseState, filterWidth: 200, filterWidthMax: 3600 };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });

  it('handles wide bandwidth', () => {
    resetSmoothing();
    const state = { ...baseState, bandwidth: 48000 };
    expect(() => renderAudioSpectrum(mockCtx(), 400, 160, state)).not.toThrow();
  });
});

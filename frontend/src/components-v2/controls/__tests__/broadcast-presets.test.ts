import { describe, it, expect } from 'vitest';
import { BROADCAST_SW_BANDS, findActiveBroadcastBand } from '../broadcast-presets';

describe('BROADCAST_SW_BANDS', () => {
  it('has 14 bands', () => {
    expect(BROADCAST_SW_BANDS).toHaveLength(14);
  });

  it('all bands have valid freq within start/end range', () => {
    for (const band of BROADCAST_SW_BANDS) {
      expect(band.freq).toBeGreaterThanOrEqual(band.start);
      expect(band.freq).toBeLessThanOrEqual(band.end);
    }
  });

  it('all bands have mode AM', () => {
    for (const band of BROADCAST_SW_BANDS) {
      expect(band.mode).toBe('AM');
    }
  });

  it('all bands have positive start/end/freq values', () => {
    for (const band of BROADCAST_SW_BANDS) {
      expect(band.start).toBeGreaterThan(0);
      expect(band.end).toBeGreaterThan(band.start);
      expect(band.freq).toBeGreaterThan(0);
    }
  });
});

describe('findActiveBroadcastBand', () => {
  it('returns correct band name for a frequency inside a band', () => {
    expect(findActiveBroadcastBand(6000000)).toBe('49m');
    expect(findActiveBroadcastBand(9500000)).toBe('31m');
    expect(findActiveBroadcastBand(15400000)).toBe('19m');
  });

  it('returns the band name for a frequency at the start boundary', () => {
    expect(findActiveBroadcastBand(5900000)).toBe('49m');
  });

  it('returns the band name for a frequency at the end boundary', () => {
    expect(findActiveBroadcastBand(6200000)).toBe('49m');
  });

  it('returns null for a frequency below all bands', () => {
    expect(findActiveBroadcastBand(1000000)).toBeNull();
  });

  it('returns null for a frequency above all bands', () => {
    expect(findActiveBroadcastBand(30000000)).toBeNull();
  });

  it('returns null for a frequency between bands', () => {
    // Between 49m (ends 6200000) and 41m (starts 7200000)
    expect(findActiveBroadcastBand(6500000)).toBeNull();
  });

  it('returns null for zero frequency', () => {
    expect(findActiveBroadcastBand(0)).toBeNull();
  });
});

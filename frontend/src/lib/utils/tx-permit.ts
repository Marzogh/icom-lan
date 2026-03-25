/**
 * TX permission check based on radio's band capabilities.
 *
 * Uses txBands from capabilities API (radio profile) when available,
 * falls back to US amateur radio allocations.
 */

interface TxBand {
  name: string;
  start: number; // Hz
  end: number;   // Hz
}

// Fallback: US Amateur Extra class TX allocations (Hz)
const US_TX_BANDS: TxBand[] = [
  { name: '160m', start: 1_800_000, end: 2_000_000 },
  { name: '80m', start: 3_500_000, end: 4_000_000 },
  { name: '60m', start: 5_330_500, end: 5_405_000 },
  { name: '40m', start: 7_000_000, end: 7_300_000 },
  { name: '30m', start: 10_100_000, end: 10_150_000 },
  { name: '20m', start: 14_000_000, end: 14_350_000 },
  { name: '17m', start: 18_068_000, end: 18_168_000 },
  { name: '15m', start: 21_000_000, end: 21_450_000 },
  { name: '12m', start: 24_890_000, end: 24_990_000 },
  { name: '10m', start: 28_000_000, end: 29_700_000 },
  { name: '6m', start: 50_000_000, end: 54_000_000 },
];

export type TxPermit = 'allowed' | 'denied';

/**
 * Check if TX is permitted at the given frequency (Hz).
 * Uses radio's txBands from capabilities when provided,
 * otherwise falls back to hardcoded US bands.
 */
export function getTxPermit(freqHz: number, txBands?: TxBand[] | null): TxPermit {
  const bands = txBands && txBands.length > 0 ? txBands : US_TX_BANDS;
  for (const band of bands) {
    if (freqHz >= band.start && freqHz <= band.end) {
      return 'allowed';
    }
  }
  return 'denied';
}

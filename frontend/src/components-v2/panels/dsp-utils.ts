export interface DspOption {
  value: string | number;
  label: string;
}

/**
 * Returns true when the given mode string is a CW mode.
 */
export function isCwMode(mode: string): boolean {
  return mode === 'CW' || mode === 'CW-R';
}

/**
 * Builds the options array for the NR mode SegmentedButton.
 * Values: 0=OFF, 1=NR1, 2=NR2 (both 1 and 2 turn NR on; backend is on/off only).
 */
export function buildNrOptions(): DspOption[] {
  return [
    { value: 0, label: 'OFF' },
    { value: 1, label: '1' },
    { value: 2, label: '2' },
  ];
}

/**
 * Builds the options array for the Notch mode SegmentedButton.
 */
export function buildNotchOptions(): DspOption[] {
  return [
    { value: 'off', label: 'OFF' },
    { value: 'auto', label: 'AUTO' },
    { value: 'manual', label: 'MAN' },
  ];
}

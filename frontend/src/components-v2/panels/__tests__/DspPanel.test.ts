import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, unmount, flushSync } from 'svelte';
import type { ComponentProps } from 'svelte';
import DspPanel from '../DspPanel.svelte';
import { buildNrOptions, buildNotchOptions } from '../dsp-utils';

vi.mock('$lib/stores/capabilities.svelte', () => ({
  hasCapability: vi.fn(() => true),
}));

// ---------------------------------------------------------------------------
// buildNrOptions
// ---------------------------------------------------------------------------

describe('buildNrOptions', () => {
  it('returns 3 options (OFF / 1 / 2)', () => {
    expect(buildNrOptions()).toHaveLength(3);
  });

  it('first option is OFF with value 0', () => {
    expect(buildNrOptions()[0]).toEqual({ value: 0, label: 'OFF' });
  });

  it('second option is 1 with value 1', () => {
    expect(buildNrOptions()[1]).toEqual({ value: 1, label: '1' });
  });

  it('third option is 2 with value 2', () => {
    expect(buildNrOptions()[2]).toEqual({ value: 2, label: '2' });
  });

  it('all option values are numbers', () => {
    buildNrOptions().forEach((o) => expect(typeof o.value).toBe('number'));
  });
});

// ---------------------------------------------------------------------------
// buildNotchOptions
// ---------------------------------------------------------------------------

describe('buildNotchOptions', () => {
  it('returns 3 options', () => {
    expect(buildNotchOptions()).toHaveLength(3);
  });

  it('first option is OFF with value "off"', () => {
    expect(buildNotchOptions()[0]).toEqual({ value: 'off', label: 'OFF' });
  });

  it('second option is AUTO with value "auto"', () => {
    expect(buildNotchOptions()[1]).toEqual({ value: 'auto', label: 'AUTO' });
  });

  it('third option is manual with value "manual"', () => {
    expect(buildNotchOptions()[2]).toEqual({ value: 'manual', label: 'MAN' });
  });
});

// ---------------------------------------------------------------------------
// DspPanel component
// ---------------------------------------------------------------------------

let components: ReturnType<typeof mount>[] = [];

function mountPanel(props: ComponentProps<typeof DspPanel>) {
  const t = document.createElement('div');
  document.body.appendChild(t);
  const component = mount(DspPanel, { target: t, props });
  flushSync();
  components.push(component);
  return t;
}

beforeEach(() => {
  components = [];
});

afterEach(() => {
  components.forEach((c) => unmount(c));
  document.body.innerHTML = '';
});

const baseProps: ComponentProps<typeof DspPanel> = {
  nrMode: 0,
  nrLevel: 128,
  nbActive: false,
  nbLevel: 128,
  notchMode: 'off',
  notchFreq: 1000,
  onNrModeChange: vi.fn(),
  onNrLevelChange: vi.fn(),
  onNbToggle: vi.fn(),
  onNbLevelChange: vi.fn(),
  onNotchModeChange: vi.fn(),
  onNotchFreqChange: vi.fn(),
};

function getFillButtons(container: HTMLElement): HTMLButtonElement[] {
  return Array.from(container.querySelectorAll<HTMLButtonElement>('.dsp-toggle-cell .v2-control-button'));
}

describe('compact toggle row', () => {
  it('renders NR, NB, NOTCH labels in FillButtons', () => {
    const t = mountPanel(baseProps);
    const texts = getFillButtons(t).map((b) => b.textContent?.trim());
    expect(texts).toContain('NR');
    expect(texts).toContain('NB');
    expect(texts).toContain('NOTCH');
  });

  it('renders settings (gear) buttons for each toggle cell', () => {
    const t = mountPanel(baseProps);
    const gears = t.querySelectorAll('.dsp-settings-btn');
    expect(gears.length).toBe(3);
  });
});

describe('NR toggle', () => {
  it('calls onNrModeChange(1) when NR is off and toggle is clicked', () => {
    const onNrModeChange = vi.fn();
    const t = mountPanel({ ...baseProps, nrMode: 0, onNrModeChange });
    const nrBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NR');
    nrBtn?.click();
    flushSync();
    expect(onNrModeChange).toHaveBeenCalledWith(1);
  });

  it('calls onNrModeChange(0) when NR is on and toggle is clicked', () => {
    const onNrModeChange = vi.fn();
    const t = mountPanel({ ...baseProps, nrMode: 1, onNrModeChange });
    const nrBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NR');
    nrBtn?.click();
    flushSync();
    expect(onNrModeChange).toHaveBeenCalledWith(0);
  });
});

describe('NB toggle', () => {
  it('calls onNbToggle(true) when NB is off and toggle is clicked', () => {
    const onNbToggle = vi.fn();
    const t = mountPanel({ ...baseProps, nbActive: false, onNbToggle });
    const nbBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NB');
    nbBtn?.click();
    flushSync();
    expect(onNbToggle).toHaveBeenCalledWith(true);
  });

  it('calls onNbToggle(false) when NB is on and toggle is clicked', () => {
    const onNbToggle = vi.fn();
    const t = mountPanel({ ...baseProps, nbActive: true, onNbToggle });
    const nbBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NB');
    nbBtn?.click();
    flushSync();
    expect(onNbToggle).toHaveBeenCalledWith(false);
  });
});

describe('Notch toggle', () => {
  it('calls onNotchModeChange("auto") when notch is off and toggle is clicked', () => {
    const onNotchModeChange = vi.fn();
    const t = mountPanel({ ...baseProps, notchMode: 'off', onNotchModeChange });
    const notchBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NOTCH');
    notchBtn?.click();
    flushSync();
    expect(onNotchModeChange).toHaveBeenCalledWith('auto');
  });

  it('calls onNotchModeChange("off") when notch is auto and toggle is clicked', () => {
    const onNotchModeChange = vi.fn();
    const t = mountPanel({ ...baseProps, notchMode: 'auto', onNotchModeChange });
    const notchBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NOTCH');
    notchBtn?.click();
    flushSync();
    expect(onNotchModeChange).toHaveBeenCalledWith('off');
  });

  it('calls onNotchModeChange("off") when notch is manual and toggle is clicked', () => {
    const onNotchModeChange = vi.fn();
    const t = mountPanel({ ...baseProps, notchMode: 'manual', onNotchModeChange });
    const notchBtn = getFillButtons(t).find((b) => b.textContent?.trim() === 'NOTCH');
    notchBtn?.click();
    flushSync();
    expect(onNotchModeChange).toHaveBeenCalledWith('off');
  });
});

describe('settings modals', () => {
  it('opens NR modal when NR gear is clicked', () => {
    const t = mountPanel(baseProps);
    const nrGear = t.querySelector<HTMLButtonElement>('[aria-label="NR settings"]');
    nrGear?.click();
    flushSync();
    expect(t.querySelector('[aria-label="Noise reduction settings"]')).toBeTruthy();
    expect(t.querySelector('.menu-backdrop')).toBeTruthy();
  });

  it('opens NB modal when NB gear is clicked', () => {
    const t = mountPanel(baseProps);
    const nbGear = t.querySelector<HTMLButtonElement>('[aria-label="NB settings"]');
    nbGear?.click();
    flushSync();
    expect(t.querySelector('[aria-label="Noise blanker settings"]')).toBeTruthy();
  });

  it('opens Notch modal when Notch gear is clicked', () => {
    const t = mountPanel(baseProps);
    const notchGear = t.querySelector<HTMLButtonElement>('[aria-label="Notch settings"]');
    notchGear?.click();
    flushSync();
    expect(t.querySelector('[role="dialog"][aria-label="Notch filter settings"]')).toBeTruthy();
  });

  it('closes modal when backdrop is clicked', () => {
    const t = mountPanel(baseProps);
    t.querySelector<HTMLButtonElement>('[aria-label="NR settings"]')?.click();
    flushSync();
    expect(t.querySelector('[aria-label="Noise reduction settings"]')).toBeTruthy();
    t.querySelector<HTMLButtonElement>('[aria-label="Close DSP settings"]')?.click();
    flushSync();
    expect(t.querySelector('[aria-label="Noise reduction settings"]')).toBeFalsy();
  });

  it('shows Notch Freq slider in notch modal only when manual is selected', () => {
    const t = mountPanel({ ...baseProps, notchMode: 'manual' });
    t.querySelector<HTMLButtonElement>('[aria-label="Notch settings"]')?.click();
    flushSync();
    const labels = Array.from(t.querySelectorAll('.vc-label')).map((el) => el.textContent?.trim());
    expect(labels).toContain('Notch Freq');
  });
});

describe('modal NR mode change', () => {
  it('calls onNrModeChange when NR modal segmented control changes', () => {
    const onNrModeChange = vi.fn();
    const t = mountPanel({ ...baseProps, onNrModeChange });
    t.querySelector<HTMLButtonElement>('[aria-label="NR settings"]')?.click();
    flushSync();
    const segments = t.querySelectorAll<HTMLButtonElement>(
      '[aria-label="Noise reduction settings"] .segment',
    );
    const seg2 = Array.from(segments).find((b) => b.textContent?.trim() === '2');
    seg2?.click();
    flushSync();
    expect(onNrModeChange).toHaveBeenCalledWith(2);
  });
});

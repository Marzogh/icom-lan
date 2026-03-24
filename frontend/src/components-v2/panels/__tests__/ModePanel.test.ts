import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, unmount, flushSync } from 'svelte';
import type { ComponentProps } from 'svelte';

import ModePanel from '../ModePanel.svelte';

let components: ReturnType<typeof mount>[] = [];

function mountPanel(props: ComponentProps<typeof ModePanel>) {
  const target = document.createElement('div');
  document.body.appendChild(target);
  const component = mount(ModePanel, { target, props });
  flushSync();
  components.push(component);
  return target;
}

beforeEach(() => {
  components = [];
});

afterEach(() => {
  components.forEach((component) => unmount(component));
  document.body.innerHTML = '';
});

const baseProps: ComponentProps<typeof ModePanel> = {
  currentMode: 'USB',
  modes: ['USB', 'LSB', 'CW', 'CW-R', 'AM', 'FM', 'RTTY', 'RTTY-R', 'PSK', 'PSK-R'],
  dataMode: 0,
  hasDataMode: true,
  dataModeCount: 3,
  dataModeLabels: { '0': 'OFF', '1': 'D1', '2': 'D2', '3': 'D3' },
  onModeChange: vi.fn(),
  onDataModeChange: vi.fn(),
};

describe('ModePanel', () => {
  it('renders mode buttons from capabilities', () => {
    const target = mountPanel(baseProps);
    const buttons = Array.from(target.querySelectorAll<HTMLButtonElement>('.mode-grid .v2-control-button')).map((button) => button.textContent?.trim());
    expect(buttons).toEqual(['USB', 'LSB', 'CW', 'CW-R', 'RTTY', 'RTTY-R', 'PSK', 'PSK-R', 'AM', 'FM']);
  });

  it('highlights the active mode button', () => {
    const target = mountPanel({ ...baseProps, currentMode: 'CW' });
    const buttons = Array.from(target.querySelectorAll<HTMLButtonElement>('.mode-grid .v2-control-button'));
    const button = buttons.find((b) => b.textContent?.trim() === 'CW');
    expect(button?.dataset.active).toBe('true');
  });

  it('calls onModeChange when a mode button is clicked', () => {
    const onModeChange = vi.fn();
    const target = mountPanel({ ...baseProps, onModeChange });
    const buttons = Array.from(target.querySelectorAll<HTMLButtonElement>('.mode-grid .v2-control-button'));
    buttons.find((b) => b.textContent?.trim() === 'LSB')?.click();
    flushSync();
    expect(onModeChange).toHaveBeenCalledWith('LSB');
  });

  it('renders DATA mode controls when supported', () => {
    const target = mountPanel(baseProps);
    const dataButtons = Array.from(target.querySelectorAll<HTMLButtonElement>('.data-grid .v2-control-button')).map((button) => button.textContent?.trim());
    expect(dataButtons).toEqual(['OFF', 'D1', 'D2', 'D3']);
  });

  it('does not render DATA mode controls when unsupported', () => {
    const target = mountPanel({ ...baseProps, hasDataMode: false });
    expect(target.querySelector('.data-grid')).toBeNull();
  });

  it('calls onDataModeChange with numeric modes', () => {
    const onDataModeChange = vi.fn();
    const target = mountPanel({ ...baseProps, onDataModeChange });
    const dataButtons = Array.from(target.querySelectorAll<HTMLButtonElement>('.data-grid .v2-control-button'));
    dataButtons.find((b) => b.textContent?.trim() === 'D3')?.click();
    flushSync();
    expect(onDataModeChange).toHaveBeenCalledWith(3);
  });
});
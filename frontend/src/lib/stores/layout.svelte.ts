/**
 * Layout preference store.
 * 'auto'     = standard layout when any scope available (HW or audio FFT), LCD otherwise
 * 'lcd'      = force LCD layout
 * 'standard' = force standard layout
 */

const STORAGE_KEY = 'icom-lan-layout';

export type LayoutMode = 'auto' | 'lcd' | 'standard';

let mode = $state<LayoutMode>(loadMode());

function loadMode(): LayoutMode {
  if (typeof window === 'undefined') return 'auto';
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'lcd' || saved === 'standard') return saved;
  // Migrate old 'spectrum' value to 'standard'
  if (saved === 'spectrum') return 'standard';
  return 'auto';
}

export function getLayoutMode(): LayoutMode {
  return mode;
}

export function setLayoutMode(m: LayoutMode): void {
  mode = m;
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, m);
  }
}

export function cycleLayoutMode(hasAnyScope: boolean): void {
  if (hasAnyScope) {
    // auto → lcd → standard → auto
    const order: LayoutMode[] = ['auto', 'lcd', 'standard'];
    const idx = order.indexOf(mode);
    setLayoutMode(order[(idx + 1) % order.length]);
  } else {
    // No scope at all: always LCD, no toggle needed
    setLayoutMode('lcd');
  }
}

/**
 * Resolve whether to use LCD layout given scope capabilities.
 * @param hasAnyScope — true if hardware spectrum OR audio FFT is available
 */
export function useLcdLayout(hasAnyScope: boolean): boolean {
  if (mode === 'lcd') return true;
  if (mode === 'standard') return false;
  // auto: standard layout when any scope is available, LCD otherwise
  return !hasAnyScope;
}

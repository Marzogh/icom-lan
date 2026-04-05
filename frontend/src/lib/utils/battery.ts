export interface BatteryManager {
  charging: boolean;
  level: number; // 0.0 to 1.0
  addEventListener(type: string, listener: EventListener): void;
  removeEventListener(type: string, listener: EventListener): void;
}

/**
 * Returns a polling interval multiplier based on battery state.
 * Progressive enhancement — returns 1 (normal) if Battery API unavailable.
 */
export function getPollingMultiplier(battery: BatteryManager | null): number {
  if (!battery) return 1;
  if (battery.charging) return 1;
  if (battery.level > 0.2) return 1; // > 20%: normal
  if (battery.level > 0.1) return 2; // 10-20%: half speed
  return 4; // < 10%: quarter speed
}

/**
 * Initialize battery monitoring. Calls onChange whenever battery state changes.
 * Returns cleanup function. No-op on unsupported browsers.
 */
export async function initBatteryMonitor(
  onChange: (multiplier: number) => void,
): Promise<() => void> {
  if (!('getBattery' in navigator)) {
    return () => {};
  }

  try {
    const battery = await (navigator as any).getBattery() as BatteryManager;

    const update = () => onChange(getPollingMultiplier(battery));

    battery.addEventListener('chargingchange', update);
    battery.addEventListener('levelchange', update);

    // Initial call
    update();

    return () => {
      battery.removeEventListener('chargingchange', update);
      battery.removeEventListener('levelchange', update);
    };
  } catch {
    return () => {};
  }
}

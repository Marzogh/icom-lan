<script lang="ts">
  import { radio } from '$lib/stores/radio.svelte';
  import { getAudioState } from '$lib/stores/audio.svelte';
  import { getCapabilities, hasCapability } from '$lib/stores/capabilities.svelte';
  import RxAudioPanel from '../panels/RxAudioPanel.svelte';
  import DspPanel from '../panels/DspPanel.svelte';
  import TxPanel from '../panels/TxPanel.svelte';
  import CwPanel from '../panels/CwPanel.svelte';
  import MemoryPanel from '../panels/MemoryPanel.svelte';
  import CollapsiblePanel from '../controls/CollapsiblePanel.svelte';
  import {
    toRxAudioProps,
    toDspProps,
    toTxProps,
    toCwProps,
  } from '../wiring/state-adapter';
  import {
    makeRxAudioHandlers,
    makeDspHandlers,
    makeTxHandlers,
    makeCwPanelHandlers,
    makeSystemHandlers,
  } from '../wiring/command-bus';

  // Reactive state + capabilities
  let radioState = $derived(radio.current);
  let audioState = $derived(getAudioState());
  let caps = $derived(getCapabilities());

  // Derived props via state adapter
  let rxAudio = $derived(toRxAudioProps(radioState, caps, audioState));
  let dsp = $derived(toDspProps(radioState, caps));
  let tx = $derived(toTxProps(radioState, caps));
  let cw = $derived(toCwProps(radioState, caps));

  // Command handlers via command-bus
  const rxAudioHandlers = makeRxAudioHandlers();
  const dspHandlers = makeDspHandlers();
  const txHandlers = makeTxHandlers();
  const cwHandlers = makeCwPanelHandlers();
  const systemHandlers = makeSystemHandlers();

  type RightSidebarMode = 'all' | 'rx' | 'tx';

  interface Props {
    mode?: RightSidebarMode;
  }

  let { mode = 'all' }: Props = $props();

  let showRx = $derived(mode === 'all' || mode === 'rx');
  let showTx = $derived(mode === 'all' || mode === 'tx');

  // --- Panel reorder ---
  const PANEL_ORDER_KEY = 'icom-lan:right-panel-order';
  const DEFAULT_ORDER = ['rx-audio', 'dsp', 'tx', 'cw', 'memory'];

  function loadPanelOrder(): string[] {
    try {
      const stored = localStorage.getItem(PANEL_ORDER_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length === DEFAULT_ORDER.length &&
            DEFAULT_ORDER.every((id) => parsed.includes(id))) {
          return parsed;
        }
      }
    } catch { /* ignore */ }
    return [...DEFAULT_ORDER];
  }

  let panelOrder = $state(loadPanelOrder());

  $effect(() => {
    try { localStorage.setItem(PANEL_ORDER_KEY, JSON.stringify(panelOrder)); }
    catch { /* ignore */ }
  });

  function orderOf(panelId: string): number {
    return panelOrder.indexOf(panelId);
  }

  // --- Drag state ---
  let dragPanelId = $state<string | null>(null);
  let dropTargetIndex = $state<number>(-1);

  function handleDragStart(panelId: string, event: PointerEvent) {
    const handle = event.currentTarget as HTMLElement;
    handle.setPointerCapture(event.pointerId);
    dragPanelId = panelId;
    dropTargetIndex = panelOrder.indexOf(panelId);

    const sidebar = handle.closest('.right-sidebar') as HTMLElement;
    if (!sidebar) return;

    const panels = Array.from(sidebar.querySelectorAll<HTMLElement>('[data-panel-id]'));
    const rects = new Map<string, DOMRect>();
    for (const p of panels) {
      rects.set(p.dataset.panelId!, p.getBoundingClientRect());
    }

    function onMove(e: PointerEvent) {
      let closest = 0;
      let minDist = Infinity;
      for (let i = 0; i < panelOrder.length; i++) {
        const rect = rects.get(panelOrder[i]);
        if (!rect) continue;
        const dist = Math.abs(e.clientY - (rect.top + rect.height / 2));
        if (dist < minDist) { minDist = dist; closest = i; }
      }
      dropTargetIndex = closest;
    }

    function onUp() {
      if (dragPanelId && dropTargetIndex >= 0) {
        const fromIndex = panelOrder.indexOf(dragPanelId);
        if (fromIndex !== dropTargetIndex) {
          const newOrder = [...panelOrder];
          const [moved] = newOrder.splice(fromIndex, 1);
          newOrder.splice(dropTargetIndex, 0, moved);
          panelOrder = newOrder;
        }
      }
      dragPanelId = null;
      dropTargetIndex = -1;
      handle.removeEventListener('pointermove', onMove);
      handle.removeEventListener('pointerup', onUp);
      handle.removeEventListener('pointercancel', onUp);
    }

    handle.addEventListener('pointermove', onMove);
    handle.addEventListener('pointerup', onUp);
    handle.addEventListener('pointercancel', onUp);
  }

  function dragStyle(panelId: string): string {
    const order = `order:${orderOf(panelId)};`;
    if (dragPanelId === panelId) return order + 'opacity:0.5;transform:scale(0.98);';
    if (dragPanelId && orderOf(panelId) === dropTargetIndex) return order + 'border-top:2px solid var(--v2-accent, #4af);';
    return order;
  }
</script>

<aside class="right-sidebar">
  {#if showRx}
    <CollapsiblePanel title="RX AUDIO" panelId="rx-audio" draggable onDragStart={handleDragStart} style={dragStyle('rx-audio')}>
      <RxAudioPanel
        monitorMode={rxAudio.monitorMode}
        afLevel={rxAudio.afLevel}
        hasLiveAudio={rxAudio.hasLiveAudio}
        onMonitorModeChange={rxAudioHandlers.onMonitorModeChange}
        onAfLevelChange={rxAudioHandlers.onAfLevelChange}
      />
    </CollapsiblePanel>

    <CollapsiblePanel title="DSP" panelId="dsp" draggable onDragStart={handleDragStart} style={dragStyle('dsp')}>
      <DspPanel
        nrMode={dsp.nrMode}
        nrLevel={dsp.nrLevel}
        nbActive={dsp.nbActive}
        nbLevel={dsp.nbLevel}
        nbDepth={dsp.nbDepth}
        nbWidth={dsp.nbWidth}
        notchMode={dsp.notchMode}
        notchFreq={dsp.notchFreq}
        manualNotchWidth={dsp.manualNotchWidth}
        agcTimeConstant={dsp.agcTimeConstant}
        onNrModeChange={dspHandlers.onNrModeChange}
        onNrLevelChange={dspHandlers.onNrLevelChange}
        onNbToggle={dspHandlers.onNbToggle}
        onNbLevelChange={dspHandlers.onNbLevelChange}
        onNbDepthChange={dspHandlers.onNbDepthChange}
        onNbWidthChange={dspHandlers.onNbWidthChange}
        onNotchModeChange={dspHandlers.onNotchModeChange}
        onNotchFreqChange={dspHandlers.onNotchFreqChange}
        onManualNotchWidthChange={dspHandlers.onManualNotchWidthChange}
        onAgcTimeChange={dspHandlers.onAgcTimeChange}
      />
    </CollapsiblePanel>
  {/if}

  {#if showTx}
    <CollapsiblePanel title="TX" panelId="tx" draggable onDragStart={handleDragStart} style={dragStyle('tx')}>
      <TxPanel
        txActive={tx.txActive}
        rfPower={tx.rfPower}
        micGain={tx.micGain}
        atuActive={tx.atuActive}
        atuTuning={tx.atuTuning}
        voxActive={tx.voxActive}
        compActive={tx.compActive}
        compLevel={tx.compLevel}
        monActive={tx.monActive}
        monLevel={tx.monLevel}
        driveGain={tx.driveGain}
        onRfPowerChange={txHandlers.onRfPowerChange}
        onMicGainChange={txHandlers.onMicGainChange}
        onAtuToggle={txHandlers.onAtuToggle}
        onAtuTune={txHandlers.onAtuTune}
        onVoxToggle={txHandlers.onVoxToggle}
        onCompToggle={txHandlers.onCompToggle}
        onCompLevelChange={txHandlers.onCompLevelChange}
        onMonToggle={txHandlers.onMonToggle}
        onMonLevelChange={txHandlers.onMonLevelChange}
        onDriveGainChange={txHandlers.onDriveGainChange}
        onPttOn={systemHandlers.onPttOn}
        onPttOff={systemHandlers.onPttOff}
      />
    </CollapsiblePanel>

    {#if hasCapability('cw')}
      <CollapsiblePanel title="CW" panelId="cw" draggable onDragStart={handleDragStart} style={dragStyle('cw')}>
        <CwPanel
          cwPitch={cw.cwPitch}
          keySpeed={cw.keySpeed}
          breakIn={cw.breakIn}
          breakInDelay={cw.breakInDelay}
          apfMode={cw.apfMode}
          twinPeak={cw.twinPeak}
          currentMode={cw.currentMode}
          onCwPitchChange={cwHandlers.onCwPitchChange}
          onKeySpeedChange={cwHandlers.onKeySpeedChange}
          onBreakInToggle={cwHandlers.onBreakInToggle}
          onBreakInModeChange={cwHandlers.onBreakInModeChange}
          onBreakInDelayChange={cwHandlers.onBreakInDelayChange}
          onApfChange={cwHandlers.onApfChange}
          onTwinPeakToggle={cwHandlers.onTwinPeakToggle}
          onAutoTune={cwHandlers.onAutoTune}
        />
      </CollapsiblePanel>
    {/if}
  {/if}

  <CollapsiblePanel title="MEMORY" panelId="memory" draggable onDragStart={handleDragStart} style={dragStyle('memory')}>
    <MemoryPanel />
  </CollapsiblePanel>
</aside>

<style>
  .right-sidebar {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
    padding: 6px 6px 16px;
    width: 100%;
    box-sizing: border-box;
  }
</style>

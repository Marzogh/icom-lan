<script lang="ts">
  import { radio } from '$lib/stores/radio.svelte';
  import { getCapabilities, hasTx, hasDualReceiver } from '$lib/stores/capabilities.svelte';
  import { getConnectionStatus, getRadioPowerOn } from '$lib/stores/connection.svelte';
  import { getAudioState } from '$lib/stores/audio.svelte';
  import SpectrumPanel from '../../components/spectrum/SpectrumPanel.svelte';
  import FrequencyDisplay from '../display/FrequencyDisplay.svelte';
  import LinearSMeter from '../meters/LinearSMeter.svelte';
  import CollapsiblePanel from '../controls/CollapsiblePanel.svelte';
  import BandSelector from '../controls/BandSelector.svelte';
  import ModePanel from '../panels/ModePanel.svelte';
  import FilterPanel from '../panels/FilterPanel.svelte';
  import RxAudioPanel from '../panels/RxAudioPanel.svelte';
  import TxPanel from '../panels/TxPanel.svelte';
  import DspPanel from '../panels/DspPanel.svelte';
  import AgcPanel from '../panels/AgcPanel.svelte';
  import RfFrontEnd from '../panels/RfFrontEnd.svelte';
  import RitXitPanel from '../panels/RitXitPanel.svelte';
  import CwPanel from '../panels/CwPanel.svelte';
  import DockMeterPanel from '../panels/DockMeterPanel.svelte';
  import StatusBar from './StatusBar.svelte';
  import KeyboardHandler from './KeyboardHandler.svelte';
  import VfoHeader from './VfoHeader.svelte';
  import {
    resolveVfoLayoutProfile,
    vfoLayoutStyleVars,
  } from './vfo-layout-tokens';
  import {
    toVfoProps, toVfoOpsProps, toMeterProps,
    toRfFrontEndProps, toModeProps, toFilterProps, toAgcProps, toRitXitProps,
    toBandSelectorProps, toRxAudioProps, toDspProps, toTxProps, toCwProps,
  } from '../wiring/state-adapter';
  import {
    makeVfoHandlers, makeMeterHandlers, makeKeyboardHandlers,
    makeRfFrontEndHandlers, makeModeHandlers, makeFilterHandlers,
    makeAgcHandlers, makeRitXitHandlers, makeBandHandlers, makePresetHandlers,
    makeRxAudioHandlers, makeDspHandlers, makeTxHandlers, makeCwPanelHandlers,
  } from '../wiring/command-bus';
  import { getKeyboardConfig } from '$lib/stores/capabilities.svelte';

  // ── State ──
  let radioState = $derived(radio.current);
  let caps = $derived(getCapabilities());
  let keyboardConfig = $derived(getKeyboardConfig());
  let audioState = $derived(getAudioState());
  let txCapable = $derived(hasTx());
  let dualReceiver = $derived(hasDualReceiver());

  // ── VFO props ──
  let mainVfo = $derived(toVfoProps(radioState, 'main'));
  let subVfo = $derived(toVfoProps(radioState, 'sub'));
  let vfoOps = $derived(toVfoOpsProps(radioState, caps));
  let meter = $derived(toMeterProps(radioState));
  let mode = $derived(toModeProps(radioState, caps));
  let filter = $derived(toFilterProps(radioState, caps));
  let band = $derived(toBandSelectorProps(radioState));
  let rxAudio = $derived(toRxAudioProps(radioState, caps, audioState));
  let tx = $derived(toTxProps(radioState, caps));
  let rfFrontEnd = $derived(toRfFrontEndProps(radioState, caps));
  let agc = $derived(toAgcProps(radioState, caps));
  let ritXit = $derived(toRitXitProps(radioState, caps));
  let dsp = $derived(toDspProps(radioState, caps));
  let cw = $derived(toCwProps(radioState, caps));

  // ── Handlers ──
  const vfoHandlers = makeVfoHandlers();
  const meterHandlers = makeMeterHandlers();
  const keyboardHandlers = makeKeyboardHandlers();
  const modeHandlers = makeModeHandlers();
  const filterHandlers = makeFilterHandlers();
  const bandHandlers = makeBandHandlers();
  const presetHandlers = makePresetHandlers();
  const rxAudioHandlers = makeRxAudioHandlers();
  const txHandlers = makeTxHandlers();
  const rfHandlers = makeRfFrontEndHandlers();
  const agcHandlers = makeAgcHandlers();
  const ritXitHandlers = makeRitXitHandlers();
  const dspHandlers = makeDspHandlers();
  const cwHandlers = makeCwPanelHandlers();

  // ── VFO layout ──
  let receiverDeckElement = $state<HTMLElement | null>(null);
  let receiverDeckWidth = $state<number | null>(null);
  let vfoLayoutProfile = $derived(resolveVfoLayoutProfile(receiverDeckWidth));
  let receiverDeckStyle = $derived(vfoLayoutStyleVars(vfoLayoutProfile, {
    width: receiverDeckWidth,
    overrides: {},
  }));

  // ── Settings modal ──
  let settingsOpen = $state(false);

  // ── Tuning strip ──
  let tuningStep = $state(1000); // Hz
  const STEPS = [10, 50, 100, 500, 1000, 5000, 10000, 100000];

  function tuneBy(delta: number) {
    const freq = mainVfo.freq + delta * tuningStep;
    vfoHandlers.onMainFreqChange(freq);
  }

  function cycleStep(direction: number) {
    const idx = STEPS.indexOf(tuningStep);
    const next = idx + direction;
    if (next >= 0 && next < STEPS.length) {
      tuningStep = STEPS[next];
    }
  }

  function formatStep(hz: number): string {
    if (hz >= 1000) return `${hz / 1000} kHz`;
    return `${hz} Hz`;
  }
</script>

<div class="m-layout">
  <KeyboardHandler config={keyboardConfig} onAction={keyboardHandlers.dispatch} />

  <!-- ═══ STICKY VFO HEADER ═══ -->
  <header class="m-vfo-bar" bind:this={receiverDeckElement} style={receiverDeckStyle}>
    <div class="m-vfo-freq">
      <FrequencyDisplay freq={mainVfo.freq} compact active />
    </div>
    <div class="m-vfo-meta">
      <span class="m-vfo-mode">{mainVfo.mode}</span>
      <span class="m-vfo-filter">{mainVfo.filter}</span>
      <span class="m-vfo-smeter-inline">
        <LinearSMeter value={mainVfo.sValue} compact label="" />
      </span>
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <span class="m-vfo-settings" onclick={() => (settingsOpen = true)}>⚙️</span>
    </div>
  </header>

  <!-- ═══ SCROLLABLE CONTENT ═══ -->
  <main class="m-content">

    <!-- Spectrum / Waterfall -->
    <section class="m-spectrum">
      <SpectrumPanel />
    </section>

    <!-- Band / Mode / Filter -->
    <section class="m-section">
      <CollapsiblePanel title="BAND" panelId="m-band" collapsible={true}>
        <BandSelector
          currentFreq={band.currentFreq}
          onBandSelect={bandHandlers.onBandSelect}
          onPresetSelect={presetHandlers.onPresetSelect}
        />
      </CollapsiblePanel>

      <CollapsiblePanel title="MODE" panelId="m-mode" collapsible={true}>
        <ModePanel
          currentMode={mode.currentMode}
          modes={mode.modes}
          dataMode={mode.dataMode}
          hasDataMode={mode.hasDataMode}
          dataModeCount={mode.dataModeCount}
          dataModeLabels={mode.dataModeLabels}
          onModeChange={modeHandlers.onModeChange}
          onDataModeChange={modeHandlers.onDataModeChange}
        />
      </CollapsiblePanel>

      <CollapsiblePanel title="FILTER" panelId="m-filter" collapsible={true}>
        <FilterPanel
          currentMode={filter.currentMode}
          currentFilter={filter.currentFilter}
          filterShape={filter.filterShape}
          filterLabels={filter.filterLabels}
          filterWidth={filter.filterWidth}
          filterWidthMin={filter.filterWidthMin}
          filterWidthMax={filter.filterWidthMax}
          filterConfig={filter.filterConfig}
          ifShift={filter.ifShift}
          hasPbt={filter.hasPbt}
          pbtInner={filter.pbtInner}
          pbtOuter={filter.pbtOuter}
          onFilterChange={filterHandlers.onFilterChange}
          onFilterWidthChange={filterHandlers.onFilterWidthChange}
          onFilterShapeChange={filterHandlers.onFilterShapeChange}
          onFilterPresetChange={filterHandlers.onFilterPresetChange}
          onFilterDefaults={filterHandlers.onFilterDefaults}
          onIfShiftChange={filterHandlers.onIfShiftChange}
          onPbtInnerChange={filterHandlers.onPbtInnerChange}
          onPbtOuterChange={filterHandlers.onPbtOuterChange}
          onPbtReset={filterHandlers.onPbtReset}
        />
      </CollapsiblePanel>
    </section>

    <!-- AF / RF -->
    <section class="m-section">
      <CollapsiblePanel title="AUDIO" panelId="m-audio" collapsible={true}>
        <RxAudioPanel
          monitorMode={rxAudio.monitorMode}
          afLevel={rxAudio.afLevel}
          hasLiveAudio={rxAudio.hasLiveAudio}
          onMonitorModeChange={rxAudioHandlers.onMonitorModeChange}
          onAfLevelChange={rxAudioHandlers.onAfLevelChange}
        />
      </CollapsiblePanel>
    </section>

    <!-- TX -->
    {#if txCapable}
      <section class="m-section">
        <CollapsiblePanel title="TX" panelId="m-tx" collapsible={true}>
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
          />
        </CollapsiblePanel>
      </section>
    {/if}

    <!-- Meters (compact) -->
    {#if txCapable}
      <section class="m-section">
        <CollapsiblePanel title="METERS" panelId="m-meters" collapsible={true}>
          <DockMeterPanel
            sValue={meter.sValue}
            rfPower={meter.rfPower}
            swr={meter.swr}
            alc={meter.alc}
            txActive={meter.txActive}
            meterSource={meter.meterSource as 'S' | 'SWR' | 'POWER'}
            onMeterSourceChange={meterHandlers.onMeterSourceChange}
          />
        </CollapsiblePanel>
      </section>
    {/if}

    <!-- Spacer for tuning strip -->
    <div class="m-bottom-spacer"></div>
  </main>

  <!-- ═══ TUNING STRIP (FIXED BOTTOM) ═══ -->
  <nav class="m-tuning-strip">
    <button class="m-tune-btn m-tune-fast" onclick={() => tuneBy(-10)}>◀◀</button>
    <button class="m-tune-btn" onclick={() => tuneBy(-1)}>◀</button>
    <button class="m-tune-step" onclick={() => cycleStep(1)} oncontextmenu={(e) => { e.preventDefault(); cycleStep(-1); }}>
      {formatStep(tuningStep)}
    </button>
    <button class="m-tune-btn" onclick={() => tuneBy(1)}>▶</button>
    <button class="m-tune-btn m-tune-fast" onclick={() => tuneBy(10)}>▶▶</button>
  </nav>

  <!-- ═══ SETTINGS BOTTOM SHEET ═══ -->
  {#if settingsOpen}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="m-sheet-backdrop" onclick={() => (settingsOpen = false)}>
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div class="m-sheet" onclick={(e) => e.stopPropagation()}>
        <div class="m-sheet-handle"></div>
        <div class="m-sheet-title">SETTINGS</div>
        <div class="m-sheet-content">
          <CollapsiblePanel title="DSP" panelId="m-dsp">
            <DspPanel
              nrActive={dsp.nrActive}
              nrLevel={dsp.nrLevel}
              nbActive={dsp.nbActive}
              nbLevel={dsp.nbLevel}
              nbDepth={dsp.nbDepth}
              nbWidth={dsp.nbWidth}
              notchActive={dsp.notchActive}
              notchWidth={dsp.notchWidth}
              notchPos={dsp.notchPos}
              hasNotchWidth={dsp.hasNotchWidth}
              hasNbDepth={dsp.hasNbDepth}
              hasNbWidth={dsp.hasNbWidth}
              onNrToggle={dspHandlers.onNrToggle}
              onNrLevelChange={dspHandlers.onNrLevelChange}
              onNbToggle={dspHandlers.onNbToggle}
              onNbLevelChange={dspHandlers.onNbLevelChange}
              onNbDepthChange={dspHandlers.onNbDepthChange}
              onNbWidthChange={dspHandlers.onNbWidthChange}
              onNotchToggle={dspHandlers.onNotchToggle}
              onNotchWidthChange={dspHandlers.onNotchWidthChange}
              onNotchPosChange={dspHandlers.onNotchPosChange}
            />
          </CollapsiblePanel>

          <CollapsiblePanel title="AGC" panelId="m-agc">
            <AgcPanel
              agcMode={agc.agcMode}
              onAgcModeChange={agcHandlers.onAgcModeChange}
            />
          </CollapsiblePanel>

          <CollapsiblePanel title="RF FRONT END" panelId="m-rf">
            <RfFrontEnd
              rfGain={rfFrontEnd.rfGain}
              squelch={rfFrontEnd.squelch}
              att={rfFrontEnd.att}
              pre={rfFrontEnd.pre}
              digiSel={rfFrontEnd.digiSel}
              ipPlus={rfFrontEnd.ipPlus}
              onRfGainChange={rfHandlers.onRfGainChange}
              onSquelchChange={rfHandlers.onSquelchChange}
              onAttChange={rfHandlers.onAttChange}
              onPreChange={rfHandlers.onPreChange}
              onDigiSelToggle={rfHandlers.onDigiSelToggle}
              onIpPlusToggle={rfHandlers.onIpPlusToggle}
            />
          </CollapsiblePanel>

          <CollapsiblePanel title="RIT / XIT" panelId="m-rit">
            <RitXitPanel
              ritActive={ritXit.ritActive}
              ritOffset={ritXit.ritOffset}
              xitActive={ritXit.xitActive}
              xitOffset={ritXit.xitOffset}
              hasRit={ritXit.hasRit}
              hasXit={ritXit.hasXit}
              onRitToggle={ritXitHandlers.onRitToggle}
              onXitToggle={ritXitHandlers.onXitToggle}
              onRitOffsetChange={ritXitHandlers.onRitOffsetChange}
              onXitOffsetChange={ritXitHandlers.onXitOffsetChange}
              onClear={ritXitHandlers.onClear}
            />
          </CollapsiblePanel>

          <CollapsiblePanel title="CW" panelId="m-cw">
            <CwPanel
              wpm={cw.wpm}
              breakInActive={cw.breakInActive}
              breakInDelay={cw.breakInDelay}
              sidetonePitch={cw.sidetonePitch}
              sidetoneLevel={cw.sidetoneLevel}
              reversePaddle={cw.reversePaddle}
              keyerType={cw.keyerType}
              hasCw={cw.hasCw}
              onWpmChange={cwHandlers.onWpmChange}
              onBreakInToggle={cwHandlers.onBreakInToggle}
              onBreakInDelayChange={cwHandlers.onBreakInDelayChange}
              onSidetonePitchChange={cwHandlers.onSidetonePitchChange}
              onSidetoneLevelChange={cwHandlers.onSidetoneLevelChange}
              onReversePaddleToggle={cwHandlers.onReversePaddleToggle}
              onKeyerTypeChange={cwHandlers.onKeyerTypeChange}
            />
          </CollapsiblePanel>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* ── Base layout ── */
  .m-layout {
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh; /* dynamic viewport height for mobile */
    background: linear-gradient(180deg, var(--v2-bg-gradient-start) 0%, var(--v2-bg-darkest) 100%);
    overflow: hidden;
    padding-top: env(safe-area-inset-top, 0px);
  }

  /* ── Sticky VFO header ── */
  .m-vfo-bar {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 6px 10px 4px;
    background: var(--v2-bg-card, #111);
    border-bottom: 1px solid var(--v2-border-panel, #333);
    z-index: 10;
  }

  .m-vfo-freq {
    line-height: 1;
  }

  .m-vfo-freq :global(.freq) {
    font-size: 28px;
  }

  .m-vfo-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Roboto Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--v2-text-muted, #888);
  }

  .m-vfo-mode {
    color: var(--v2-accent-cyan, #22d3ee);
    padding: 1px 6px;
    border: 1px solid var(--v2-accent-cyan, #22d3ee);
    border-radius: 3px;
    font-size: 10px;
  }

  .m-vfo-filter {
    color: var(--v2-text-secondary, #aaa);
    font-size: 10px;
  }

  .m-vfo-smeter-inline {
    flex: 1;
    min-width: 60px;
    max-width: 140px;
  }

  .m-vfo-settings {
    cursor: pointer;
    font-size: 16px;
    padding: 4px;
    -webkit-tap-highlight-color: transparent;
  }

  /* ── Scrollable content ── */
  .m-content {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }

  .m-content::-webkit-scrollbar {
    display: none;
  }

  /* ── Spectrum ── */
  .m-spectrum {
    height: 220px;
    min-height: 180px;
    border-bottom: 1px solid var(--v2-border-darker, #222);
  }

  .m-spectrum :global(.spectrum-panel) {
    height: 100%;
    border: none;
    border-radius: 0;
    box-shadow: none;
  }

  /* ── Accordion sections ── */
  .m-section {
    display: flex;
    flex-direction: column;
    gap: 0;
    border-bottom: 1px solid var(--v2-border-darker, #1a1a2e);
  }

  .m-section :global(.collapsible-panel) {
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  /* ── Bottom spacer (for tuning strip) ── */
  .m-bottom-spacer {
    height: calc(52px + env(safe-area-inset-bottom, 0px));
    flex-shrink: 0;
  }

  /* ── Tuning strip ── */
  .m-tuning-strip {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: stretch;
    height: 52px;
    padding-bottom: env(safe-area-inset-bottom, 0px);
    background: var(--v2-bg-card, #111);
    border-top: 1px solid var(--v2-border-panel, #333);
    z-index: 100;
    gap: 1px;
  }

  .m-tune-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--v2-bg-input, #1a1a2e);
    border: none;
    color: var(--v2-text-primary, #ddd);
    font-size: 18px;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    transition: background 0.1s;
    min-height: 44px; /* touch target */
  }

  .m-tune-btn:active {
    background: var(--v2-accent-cyan, #22d3ee);
    color: var(--v2-bg-darkest, #000);
  }

  .m-tune-fast {
    flex: 0.7;
    font-size: 14px;
    color: var(--v2-text-muted, #888);
  }

  .m-tune-fast:active {
    background: var(--v2-accent-cyan, #22d3ee);
    color: var(--v2-bg-darkest, #000);
  }

  .m-tune-step {
    flex: 1.2;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--v2-bg-darker, #0a0a14);
    border: 1px solid var(--v2-border-panel, #333);
    border-top: none;
    border-bottom: none;
    color: var(--v2-accent-cyan, #22d3ee);
    font-family: 'Roboto Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    min-height: 44px;
  }

  .m-tune-step:active {
    background: var(--v2-bg-input, #1a1a2e);
  }

  /* ── Settings bottom sheet ── */
  .m-sheet-backdrop {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
  }

  .m-sheet {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    max-height: 75vh;
    background: var(--v2-bg-primary, #0f0f1a);
    border-top: 1px solid var(--v2-border-panel, #333);
    border-radius: 16px 16px 0 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    z-index: 201;
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }

  .m-sheet-handle {
    width: 36px;
    height: 4px;
    background: var(--v2-text-dim, #444);
    border-radius: 2px;
    margin: 10px auto 6px;
  }

  .m-sheet-title {
    text-align: center;
    font-family: 'Roboto Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: var(--v2-text-secondary, #aaa);
    padding: 0 0 8px;
    border-bottom: 1px solid var(--v2-border-darker, #222);
  }

  .m-sheet-content {
    display: flex;
    flex-direction: column;
    gap: 0;
    padding: 4px 0;
  }

  .m-sheet-content :global(.collapsible-panel) {
    border-radius: 0;
    border-left: none;
    border-right: none;
  }
</style>

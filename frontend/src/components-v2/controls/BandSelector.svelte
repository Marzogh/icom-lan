<script lang="ts">
  import { HardwareButton } from '$lib/Button';
  import { getCapabilities } from '$lib/stores/capabilities.svelte';
  import { flattenBands, findActiveBand } from './band-utils';
  import { getShortcutHint } from '../layout/shortcut-hints';

  interface Props {
    currentFreq: number;
    onBandSelect: (bandName: string, freq: number, bsrCode?: number) => void;
  }

  let { currentFreq, onBandSelect }: Props = $props();

  let bands = $derived(flattenBands(getCapabilities()?.freqRanges ?? []));
  let activeBand = $derived(findActiveBand(currentFreq, getCapabilities()?.freqRanges ?? []));

  function handleClick(name: string, defaultFreq: number, bsrCode?: number) {
    onBandSelect(name, defaultFreq, bsrCode);
  }

  function bandShortcut(bsrCode?: number): string | null {
    if (bsrCode === undefined) {
      return null;
    }
    return getShortcutHint('band_select', (binding) => Number(binding.params?.index) === bsrCode);
  }

</script>

<div class="grid">
    {#each bands as band (band.name)}
      {@const isActive = activeBand === band.name}
      <HardwareButton
        active={isActive}
        indicator="edge-left"
        color="cyan"
        title={bandShortcut(band.bsrCode)}
        shortcutHint={bandShortcut(band.bsrCode)}
        onclick={() => handleClick(band.name, band.defaultFreq, band.bsrCode)}
      >
        {band.name}
      </HardwareButton>
    {/each}
  </div>

<style>
  .grid {
    padding: 6px 7px 7px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 3px;
  }

  .grid > :global(button) {
    min-width: 0;
  }
</style>

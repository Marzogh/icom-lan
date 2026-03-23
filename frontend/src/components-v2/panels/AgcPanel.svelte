<script lang="ts">
  import { HardwareButton } from '$lib/Button';
  import { getAgcModes, getAgcLabels } from '$lib/stores/capabilities.svelte';
  import { buildAgcOptions } from './agc-utils';

  interface Props {
    agcMode: number;
    onAgcModeChange: (v: number) => void;
  }

  let { agcMode, onAgcModeChange }: Props = $props();

  let options = $derived(buildAgcOptions(getAgcModes(), getAgcLabels()));
</script>

<div class="panel-body">
  <div class="button-grid">
    {#each options as option}
      <HardwareButton
        active={agcMode === option.value}
        indicator="edge-left"
        color="cyan"
        onclick={() => onAgcModeChange(option.value)}
      >
        {option.label}
      </HardwareButton>
    {/each}
  </div>
</div>

<style>
  .panel-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 7px 8px;
  }
</style>

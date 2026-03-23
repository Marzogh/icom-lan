<script lang="ts">
  import { SegmentedControl } from '$lib/SegmentedControl';
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
    <SegmentedControl
      options={options}
      selected={agcMode}
      onchange={(v) => onAgcModeChange(v as number)}
    />
  </div>

<style>
  .panel-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 7px 8px;
  }
</style>

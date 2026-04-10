<script lang="ts">
  import { onMount } from 'svelte';
  import {
    WaterfallRenderer,
    defaultWaterfallOptions,
    type WaterfallOptions,
  } from '../../lib/renderers/waterfall-renderer';

  interface Props {
    options?: WaterfallOptions;
    onRegisterPush?: (fn: (data: Uint8Array) => void) => void;
  }

  let { options = defaultWaterfallOptions, onRegisterPush }: Props = $props();

  let canvas: HTMLCanvasElement;
  let renderer = $state<WaterfallRenderer | null>(null);

  // Direct push function — called by parent SpectrumPanel for each scope frame.
  // Svelte 5 reactivity cannot reliably track Uint8Array prop changes at 100+ fps,
  // so we bypass it entirely with a direct function call.
  function directPush(pixels: Uint8Array): void {
    if (document.hidden) return; // skip when tab hidden
    renderer?.pushRow(pixels);
  }

  // Sync options changes (colorMap, centerHz, spanHz) to the renderer
  $effect(() => {
    if (renderer && options) {
      renderer.updateOptions(options);
    }
  });

  onMount(() => {
    renderer = new WaterfallRenderer(canvas, options);

    // Register direct push callback with parent
    onRegisterPush?.(directPush);

    const ro = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (!rect) return;
      const dpr = window.devicePixelRatio || 1;
      const w = Math.max(1, Math.floor(rect.width * dpr));
      const h = Math.max(1, Math.floor(rect.height * dpr));
      canvas.width = w;
      canvas.height = h;
      renderer?.resize(w, h);
    });
    ro.observe(canvas);

    return () => {
      ro.disconnect();
      renderer?.destroy();
      renderer = null;
    };
  });
</script>

<canvas bind:this={canvas}></canvas>

<style>
  canvas {
    display: block;
    width: 100%;
    height: 100%;
    cursor: crosshair;
    background: #001020;
  }
</style>

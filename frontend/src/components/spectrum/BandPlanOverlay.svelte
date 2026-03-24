<script lang="ts">
  import {
    getVisibleSegments,
    SEGMENT_COLORS,
    SEGMENT_BORDER_COLORS,
    SEGMENT_LABEL_COLORS,
    type BandSegmentMode,
  } from '../../lib/data/arrl-band-plan';

  interface Props {
    startFreq: number;
    endFreq: number;
    visible?: boolean;
  }

  let { startFreq, endFreq, visible = true }: Props = $props();

  let containerWidth = $state(0);

  // Remote segments from REST API
  interface RemoteSegment {
    start: number;
    end: number;
    mode: string;
    label: string;
    color: string;
    opacity: number;
    band: string;
    layer: string;
    priority: number;
    url?: string | null;
    notes?: string | null;
    station?: string | null;
  }

  let remoteSegments = $state<RemoteSegment[]>([]);
  let lastFetchRange = $state({ start: 0, end: 0 });
  let fetchTimeout: ReturnType<typeof setTimeout> | null = null;

  // Debounced fetch from REST API
  function fetchSegments(start: number, end: number) {
    // Skip if range hasn't changed significantly (< 1% shift)
    const span = end - start;
    if (
      lastFetchRange.start > 0 &&
      Math.abs(start - lastFetchRange.start) < span * 0.01 &&
      Math.abs(end - lastFetchRange.end) < span * 0.01
    ) {
      return;
    }

    if (fetchTimeout) clearTimeout(fetchTimeout);
    fetchTimeout = setTimeout(async () => {
      try {
        // Fetch wider range to avoid re-fetching on small pans
        const margin = Math.round(span * 0.5);
        const fetchStart = Math.max(0, start - margin);
        const fetchEnd = end + margin;
        const resp = await fetch(
          `/api/v1/band-plan/segments?start=${fetchStart}&end=${fetchEnd}`
        );
        if (resp.ok) {
          const data = await resp.json();
          remoteSegments = data.segments ?? [];
          lastFetchRange = { start: fetchStart, end: fetchEnd };
        }
      } catch {
        // Silently fall back to local data
      }
    }, 100);
  }

  // Trigger fetch when frequency range changes
  $effect(() => {
    if (visible && startFreq > 0 && endFreq > startFreq) {
      fetchSegments(startFreq, endFreq);
    }
  });

  // Use remote segments if available, fall back to local
  let segments = $derived(() => {
    if (!visible || endFreq <= startFreq) return [];
    const span = endFreq - startFreq;

    if (remoteSegments.length > 0) {
      // Filter to visible range and position
      return remoteSegments
        .filter((s) => s.end > startFreq && s.start < endFreq)
        .map((s) => {
          const rawLeft = ((s.start - startFreq) / span) * 100;
          const rawRight = ((s.end - startFreq) / span) * 100;
          const leftPct = Math.max(0, Math.min(100, rawLeft));
          const rightPct = Math.max(0, Math.min(100, rawRight));
          const widthPct = rightPct - leftPct;
          const widthPx = (widthPct / 100) * containerWidth;
          return {
            start: s.start,
            label: s.label,
            mode: s.mode,
            color: `rgba(${hexToRgb(s.color)}, ${s.opacity})`,
            borderColor: `rgba(${hexToRgb(s.color)}, ${Math.min(1, s.opacity + 0.3)})`,
            labelColor: s.color,
            leftPct,
            widthPct,
            widthPx,
            notes: s.notes,
            url: s.url,
          };
        });
    }

    // Fallback to local hardcoded data
    return getVisibleSegments(startFreq, endFreq).map(({ segment }) => {
      const rawLeft = ((segment.startHz - startFreq) / span) * 100;
      const rawRight = ((segment.endHz - startFreq) / span) * 100;
      const leftPct = Math.max(0, Math.min(100, rawLeft));
      const rightPct = Math.max(0, Math.min(100, rawRight));
      const widthPct = rightPct - leftPct;
      const widthPx = (widthPct / 100) * containerWidth;
      return {
        start: segment.startHz,
        label: segment.label,
        mode: segment.mode,
        color: SEGMENT_COLORS[segment.mode as BandSegmentMode] ?? 'rgba(156,163,175,0.20)',
        borderColor: SEGMENT_BORDER_COLORS[segment.mode as BandSegmentMode] ?? 'rgba(156,163,175,0.50)',
        labelColor: SEGMENT_LABEL_COLORS[segment.mode as BandSegmentMode] ?? 'rgb(156,163,175)',
        leftPct,
        widthPct,
        widthPx,
        notes: null as string | null,
        url: null as string | null,
      };
    });
  });

  function hexToRgb(hex: string): string {
    const h = hex.replace('#', '');
    const r = parseInt(h.substring(0, 2), 16);
    const g = parseInt(h.substring(2, 4), 16);
    const b = parseInt(h.substring(4, 6), 16);
    return `${r},${g},${b}`;
  }
</script>

{#if visible && segments().length > 0}
<div class="bandplan-overlay" aria-hidden="true" bind:clientWidth={containerWidth}>
  {#each segments() as seg (seg.start)}
    <div
      class="band-segment"
      style="left:{seg.leftPct}%;width:{seg.widthPct}%;background:{seg.color};border-left:1px solid {seg.borderColor}"
      title={seg.notes ?? seg.label}
    >
      {#if seg.widthPx > 40}
        <span class="segment-label" style="color:{seg.labelColor}">
          {seg.label}
        </span>
      {/if}
    </div>
  {/each}
</div>
{/if}

<style>
  .bandplan-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 16px;
    pointer-events: none;
    overflow: hidden;
    z-index: 2;
  }

  .band-segment {
    position: absolute;
    top: 0;
    bottom: 0;
  }

  .segment-label {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Roboto Mono', monospace;
    font-size: 8px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    opacity: 0.9;
    pointer-events: none;
  }
</style>

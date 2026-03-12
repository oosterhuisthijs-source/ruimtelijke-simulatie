<template>
  <div class="legend">
    <div class="legend-title">Gebiedstype</div>
    <div class="gradient-bar" :style="{ background: gradient }" />
    <div class="legend-labels">
      <span>Landelijk / natuur</span>
      <span>Stedelijk / dicht</span>
    </div>
    <div class="legend-note">Vergelijkbare kleur = vergelijkbaar gebiedstype</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Match the getFillColor logic in useMap.ts
function clusterColor(t: number): string {
  const r = Math.round(255 * t)
  const g = Math.round(100 + 100 * (1 - t))
  const b = Math.round(255 * (1 - t))
  return `rgb(${r},${g},${b})`
}

const gradient = computed(() => {
  const stops = Array.from({ length: 6 }, (_, i) => {
    const t = i / 5
    return `${clusterColor(t)} ${Math.round(t * 100)}%`
  }).join(', ')
  return `linear-gradient(to right, ${stops})`
})
</script>

<style scoped>
.legend {
  background: rgba(15, 15, 30, 0.88);
  border: 1px solid #333;
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  min-width: 180px;
}

.legend-title {
  font-size: 0.72rem;
  font-weight: 600;
  color: #a8d8ea;
  margin-bottom: 0.4rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.gradient-bar {
  height: 10px;
  border-radius: 3px;
  margin-bottom: 0.25rem;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
  color: #888;
}

.legend-note {
  font-size: 0.65rem;
  color: #555;
  margin-top: 0.35rem;
  font-style: italic;
}
</style>

<template>
  <div class="app">
    <aside class="sidebar">
      <h1>Ruimtelijke Simulatie</h1>

      <!-- Mode selector -->
      <div class="mode-selector">
        <button :class="{ active: mode === 'clusters' }" @click="mode = 'clusters'">
          Clusters
        </button>
        <button :class="{ active: mode === 'trajectory' }" @click="mode = 'trajectory'">
          Traject
        </button>
        <button :class="{ active: mode === 'scenario' }" @click="mode = 'scenario'">
          Scenario
        </button>
        <button :class="{ active: mode === 'trend' }" @click="mode = 'trend'">
          Trend
        </button>
      </div>

      <!-- Scenario controls -->
      <div v-if="mode === 'scenario'" class="controls">
        <label>Variabele</label>
        <select v-model="scenarioColumn">
          <option value="aantal_inwoners_sum">Inwoners</option>
          <option value="gemiddelde_woz_waarde_woning_area_weighted_average">WOZ waarde</option>
          <option value="aantal_huurwoningen_in_bezit_woningcorporaties_sum">Sociale huur</option>
          <option value="aantal_personen_met_uitkering_onder_aowlft_sum">Uitkeringen</option>
          <option value="loofbos_fraction">Loofbos</option>
          <option value="hitte">Hitte</option>
        </select>

        <label>Verandering: {{ Math.round((scenarioFactor - 1) * 100) }}%</label>
        <input
          type="range"
          min="0.5"
          max="1.5"
          step="0.05"
          v-model.number="scenarioFactor"
          @change="runScenario"
        />

        <button @click="runScenario">Simuleer</button>
      </div>

      <!-- Trend controls -->
      <div v-if="mode === 'trend'" class="controls">
        <label>Doeljaar: {{ trendYear }}</label>
        <input
          type="range"
          min="2024"
          max="2035"
          step="1"
          v-model.number="trendYear"
        />
        <button @click="runTrend">Projecteer trend</button>
      </div>

      <!-- Trajectory info -->
      <div v-if="selectedHex && trajectory.length" class="trajectory-info">
        <h3>Traject: {{ selectedHex.slice(0, 8) }}...</h3>
        <div v-for="step in trajectory" :key="step.year" class="trajectory-step">
          <span>{{ step.year }}</span>
          <span>Cluster {{ step.cluster_id }}</span>
        </div>
      </div>

      <!-- Ollama insight -->
      <div v-if="insight" class="insight-box">
        <div class="insight-label">🧠 Lokale AI</div>
        <p v-if="insightLoading" class="insight-loading">Analyseren...</p>
        <p v-else>{{ insight }}</p>
      </div>
    </aside>

    <!-- Map -->
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMap } from './composables/useMap'
import { useSOM } from './composables/useSOM'
import { useInsight } from './composables/useInsight'

const mapContainer = ref<HTMLElement>()
const mode = ref<'clusters' | 'trajectory' | 'scenario' | 'trend'>('clusters')
const scenarioColumn = ref('aantal_inwoners_sum')
const scenarioFactor = ref(1.0)
const trendYear = ref(2030)
const selectedHex = ref<string>('')
const trajectory = ref<any[]>([])
const insight = ref<string>('')
const insightLoading = ref(false)
let originalClusters: any[] = []

const { initMap, updateHexagons } = useMap(mapContainer)
const { fetchClusters, fetchTrajectory, runScenarioRequest, runTrendRequest } = useSOM()
const { getClusterInsight, getTrajectoryInsight, getScenarioInsight, getTrendInsight } = useInsight()

onMounted(async () => {
  await initMap()
  const clusters = await fetchClusters()
  originalClusters = clusters
  updateHexagons(clusters, 'cluster_id', onHexClick)
})

watch(mode, async (newMode) => {
  insight.value = ''
  if (newMode === 'clusters') {
    const clusters = await fetchClusters()
    originalClusters = clusters
    updateHexagons(clusters, 'cluster_id', onHexClick)
  }
})

async function onHexClick(h3: string, clusterId: number) {
  selectedHex.value = h3

  if (mode.value === 'trajectory') {
    trajectory.value = await fetchTrajectory(h3)
    insightLoading.value = true
    insight.value = '...'
    const result = await getTrajectoryInsight(h3)
    insight.value = result.insight
    insightLoading.value = false
  }

  if (mode.value === 'clusters') {
    insightLoading.value = true
    insight.value = '...'
    const result = await getClusterInsight(clusterId)
    insight.value = result.insight
    insightLoading.value = false
  }
}

async function runTrend() {
  const results = await runTrendRequest(trendYear.value)
  updateHexagons(results, 'cluster_id', onHexClick)
  insightLoading.value = true
  insight.value = '...'
  const result = await getTrendInsight(trendYear.value, originalClusters, results)
  insight.value = result.insight
  insightLoading.value = false
}

async function runScenario() {
  const results = await runScenarioRequest(scenarioColumn.value, scenarioFactor.value)
  updateHexagons(results, 'cluster_id', onHexClick)

  insightLoading.value = true
  insight.value = '...'
  const result = await getScenarioInsight(
    scenarioColumn.value,
    scenarioFactor.value,
    originalClusters,
    results
  )
  insight.value = result.insight
  insightLoading.value = false
}
</script>

<style scoped>
.app {
  display: flex;
  width: 100%;
  height: 100%;
}

.sidebar {
  width: 280px;
  background: #1a1a2e;
  color: #eee;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  z-index: 10;
}

h1 {
  font-size: 1rem;
  font-weight: 600;
  color: #a8d8ea;
}

.mode-selector {
  display: flex;
  gap: 0.5rem;
}

.mode-selector button {
  flex: 1;
  padding: 0.4rem;
  border: 1px solid #444;
  background: transparent;
  color: #ccc;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.8rem;
}

.mode-selector button.active {
  background: #a8d8ea;
  color: #1a1a2e;
  border-color: #a8d8ea;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.controls label {
  font-size: 0.8rem;
  color: #aaa;
}

.controls select,
.controls input[type="range"] {
  width: 100%;
}

.controls button {
  padding: 0.5rem;
  background: #a8d8ea;
  color: #1a1a2e;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.trajectory-info {
  font-size: 0.8rem;
}

.trajectory-step {
  display: flex;
  justify-content: space-between;
  padding: 0.2rem 0;
  border-bottom: 1px solid #333;
}

.insight-box {
  background: #0f3460;
  border-radius: 6px;
  padding: 0.75rem;
  font-size: 0.8rem;
  line-height: 1.5;
}

.insight-label {
  font-size: 0.7rem;
  color: #a8d8ea;
  margin-bottom: 0.4rem;
  font-weight: 600;
}

.insight-loading {
  color: #888;
  font-style: italic;
}

.map-container {
  flex: 1;
  position: relative;
}
</style>

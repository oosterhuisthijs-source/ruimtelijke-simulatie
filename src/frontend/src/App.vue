<template>
  <div class="app">
    <aside class="sidebar">
      <h1>Ruimtelijke Simulatie</h1>

      <!-- Mode selector -->
      <div class="mode-selector">
        <button :class="{ active: mode === 'clusters' }" @click="mode = 'clusters'">Clusters</button>
        <button :class="{ active: mode === 'trajectory' }" @click="mode = 'trajectory'">Traject</button>
        <button :class="{ active: mode === 'scenario' }" @click="mode = 'scenario'">Scenario</button>
        <button :class="{ active: mode === 'trend' }" @click="mode = 'trend'">Trend</button>
        <button :class="{ active: mode === 'chat' }" @click="mode = 'chat'">Chat</button>
      </div>

      <!-- Jaar slider (altijd zichtbaar in kaart-modi) -->
      <div v-if="mode !== 'scenario' && mode !== 'trend' && mode !== 'chat'" class="controls">
        <label>Jaar: {{ mapYear }}</label>
        <input type="range" min="2018" max="2023" step="1" v-model.number="mapYear" @change="loadYear" />
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
        <input type="range" min="0.5" max="1.5" step="0.05" v-model.number="scenarioFactor" @change="runScenario" />
        <button @click="runScenario">Simuleer</button>
        <div v-if="scenarioDone" class="diff-legend">
          <span class="dot shifted" /> Verschoven cluster
          <span class="dot stable" /> Stabiel
        </div>
      </div>

      <!-- Trend controls -->
      <div v-if="mode === 'trend'" class="controls">
        <label>Doeljaar: {{ trendYear }}</label>
        <input type="range" min="2024" max="2035" step="1" v-model.number="trendYear" />
        <button @click="runTrend">Projecteer trend</button>
        <div v-if="trendDone" class="diff-legend">
          <span class="dot shifted" /> Verschoven cluster
          <span class="dot stable" /> Stabiel
        </div>
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
    <div class="map-container">
      <div ref="mapContainer" class="map-inner" />

      <!-- Tooltip -->
      <div
        v-if="hoveredInfo"
        class="map-tooltip"
        :style="{ left: hoveredInfo.x + 'px', top: hoveredInfo.y + 'px' }"
      >
        <div class="tooltip-gemeente">{{ hoveredInfo.object.gemeentenaam }}</div>
        <div class="tooltip-wijk">{{ hoveredInfo.object.wijknaam }}</div>
        <div class="tooltip-row">
          <span>Cluster</span><span>{{ hoveredInfo.object.cluster_id }}</span>
        </div>
        <div v-if="hoveredInfo.object.aantal_inwoners_sum > 0" class="tooltip-row">
          <span>Inwoners</span><span>{{ hoveredInfo.object.aantal_inwoners_sum }}</span>
        </div>
        <div v-if="hoveredInfo.object.gemiddelde_woz_waarde_woning_area_weighted_average > 0" class="tooltip-row">
          <span>WOZ</span><span>{{ hoveredInfo.object.gemiddelde_woz_waarde_woning_area_weighted_average }}</span>
        </div>
        <div v-if="hoveredInfo.object.hitte > 0" class="tooltip-row">
          <span>Hitte</span><span>{{ hoveredInfo.object.hitte }}</span>
        </div>
      </div>

      <!-- Legend -->
      <MapLegend class="map-legend" />
    </div>

    <!-- Chat panel -->
    <div v-if="mode === 'chat'" class="chat-container">
      <ChatPanel @highlight="onHighlight" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMap } from './composables/useMap'
import { useSOM } from './composables/useSOM'
import { useInsight } from './composables/useInsight'
import ChatPanel from './components/chat/ChatPanel.vue'
import MapLegend from './components/map/MapLegend.vue'

const mapContainer = ref<HTMLElement>()
const mode = ref<'clusters' | 'trajectory' | 'scenario' | 'trend' | 'chat'>('clusters')
const scenarioColumn = ref('aantal_inwoners_sum')
const scenarioFactor = ref(1.0)
const trendYear = ref(2030)
const mapYear = ref(2023)
const selectedHex = ref<string>('')
const trajectory = ref<any[]>([])
const insight = ref<string>('')
const insightLoading = ref(false)
const scenarioDone = ref(false)
const trendDone = ref(false)
let originalClusters: any[] = []

const { initMap, updateHexagons, hoveredInfo } = useMap(mapContainer)
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
  scenarioDone.value = false
  trendDone.value = false
  if (newMode === 'clusters') {
    const clusters = await fetchClusters(mapYear.value)
    originalClusters = clusters
    updateHexagons(clusters, 'cluster_id', onHexClick)
  }
})

async function loadYear() {
  const clusters = await fetchClusters(mapYear.value)
  originalClusters = clusters
  updateHexagons(clusters, 'cluster_id', onHexClick)
}

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
  trendDone.value = false
  const results = await runTrendRequest(trendYear.value)
  updateHexagons(results, 'cluster_id', onHexClick, originalClusters)
  trendDone.value = true
  insightLoading.value = true
  insight.value = '...'
  const result = await getTrendInsight(trendYear.value, originalClusters, results)
  insight.value = result.insight
  insightLoading.value = false
}

async function runScenario() {
  scenarioDone.value = false
  const results = await runScenarioRequest(scenarioColumn.value, scenarioFactor.value)
  updateHexagons(results, 'cluster_id', onHexClick, originalClusters)
  scenarioDone.value = true
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

function onHighlight(h3Ids: string[], label: string) {
  if (!originalClusters.length) return
  const idSet = new Set(h3Ids)
  const filtered = originalClusters.filter((c) => idSet.has(c.h3))
  if (filtered.length > 0) {
    updateHexagons(filtered, 'cluster_id', onHexClick)
  }
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
  flex-shrink: 0;
}

h1 {
  font-size: 1rem;
  font-weight: 600;
  color: #a8d8ea;
}

.mode-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.mode-selector button {
  flex: 1;
  min-width: 60px;
  padding: 0.4rem;
  border: 1px solid #444;
  background: transparent;
  color: #ccc;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.78rem;
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

.diff-legend {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #aaa;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.dot.shifted { background: rgb(255, 120, 0); }
.dot.stable { background: rgb(80, 80, 80); }

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
  overflow: hidden;
}

.map-inner {
  width: 100%;
  height: 100%;
}

.map-tooltip {
  position: absolute;
  pointer-events: none;
  background: rgba(10, 10, 25, 0.92);
  border: 1px solid #444;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-size: 0.78rem;
  color: #eee;
  z-index: 20;
  transform: translate(14px, -50%);
  white-space: nowrap;
  min-width: 160px;
}

.tooltip-gemeente {
  font-weight: 600;
  color: #a8d8ea;
  margin-bottom: 0.1rem;
}

.tooltip-wijk {
  color: #888;
  font-size: 0.72rem;
  margin-bottom: 0.3rem;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.75rem;
  color: #ccc;
  border-top: 1px solid #2a2a3a;
  padding-top: 0.15rem;
  margin-top: 0.15rem;
}

.tooltip-row span:first-child { color: #888; }

.map-legend {
  position: absolute;
  bottom: 1.5rem;
  right: 1rem;
  z-index: 10;
}

.chat-container {
  width: 420px;
  border-left: 1px solid #222;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}
</style>

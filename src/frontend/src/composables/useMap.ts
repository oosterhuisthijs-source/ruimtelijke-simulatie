import { ref, type Ref } from 'vue'
import maplibregl from 'maplibre-gl'
import { MapboxOverlay } from '@deck.gl/mapbox'
import { H3HexagonLayer } from '@deck.gl/geo-layers'

export interface HoveredInfo {
  x: number
  y: number
  object: any
}

export function useMap(container: Ref<HTMLElement | undefined>) {
  let overlay: MapboxOverlay | null = null
  let map: maplibregl.Map | null = null

  const hoveredInfo = ref<HoveredInfo | null>(null)

  async function initMap() {
    if (!container.value) return

    map = new maplibregl.Map({
      container: container.value,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [4.9, 52.1],
      zoom: 7,
      interactive: true,
    })

    overlay = new MapboxOverlay({ interleaved: false, layers: [] })
    map.addControl(overlay as any)
  }

  function updateHexagons(
    data: any[],
    valueColumn: string,
    onClick?: (h3: string, value: number) => void,
    baseData?: any[]
  ) {
    if (!overlay) return

    const values = data.map((d) => d[valueColumn] ?? 0)
    const min = Math.min(...values)
    const max = Math.max(...values)

    // Build diff lookup if baseData provided
    const baseMap = baseData
      ? new Map(baseData.map((d) => [d.h3, d[valueColumn]]))
      : null

    const layer = new H3HexagonLayer({
      id: 'h3-layer',
      data,
      getHexagon: (d: any) => d.h3,
      getFillColor: (d: any) => {
        // Diff mode: orange = changed, grey = stable
        if (baseMap) {
          const changed = baseMap.get(d.h3) !== d[valueColumn]
          return changed ? [255, 120, 0, 220] : [80, 80, 80, 100]
        }
        // Normal mode: blue → red gradient
        const v = d[valueColumn] ?? 0
        const t = max === min ? 0.5 : (v - min) / (max - min)
        return [
          Math.round(255 * t),
          Math.round(100 + 100 * (1 - t)),
          Math.round(255 * (1 - t)),
          180,
        ]
      },
      extruded: false,
      pickable: true,
      onHover: (info: any) => {
        hoveredInfo.value = info.object
          ? { x: info.x, y: info.y, object: info.object }
          : null
      },
      onClick: onClick
        ? (info: any) => {
            if (info.object) {
              onClick(info.object.h3, info.object[valueColumn] ?? 0)
            }
          }
        : undefined,
    })

    overlay.setProps({ layers: [layer] })
  }

  return { initMap, updateHexagons, hoveredInfo }
}

import { type Ref } from 'vue'
import maplibregl from 'maplibre-gl'
import { MapboxOverlay } from '@deck.gl/mapbox'
import { H3HexagonLayer } from '@deck.gl/geo-layers'

export function useMap(container: Ref<HTMLElement | undefined>) {
  let overlay: MapboxOverlay | null = null
  let map: maplibregl.Map | null = null

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
    onClick?: (h3: string, value: number) => void
  ) {
    if (!overlay) return

    const values = data.map((d) => d[valueColumn] ?? 0)
    const min = Math.min(...values)
    const max = Math.max(...values)

    const layer = new H3HexagonLayer({
      id: 'h3-layer',
      data,
      getHexagon: (d: any) => d.h3,
      getFillColor: (d: any) => {
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

  return { initMap, updateHexagons }
}

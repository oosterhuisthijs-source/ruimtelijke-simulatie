const API = 'http://localhost:8002/api'

export function useInsight() {
  async function getClusterInsight(clusterId: number) {
    const res = await fetch(`${API}/insight/cluster/${clusterId}`)
    return res.json()
  }

  async function getTrajectoryInsight(h3Id: string) {
    const res = await fetch(`${API}/insight/trajectory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ h3_id: h3Id }),
    })
    return res.json()
  }

  async function getScenarioInsight(
    column: string,
    changeFactor: number,
    originalClusters: any[],
    newClusters: any[]
  ) {
    const res = await fetch(`${API}/insight/scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        column,
        change_factor: changeFactor,
        original_clusters: originalClusters,
        new_clusters: newClusters,
      }),
    })
    return res.json()
  }

  async function getTrendInsight(
    targetYear: number,
    originalClusters: any[],
    newClusters: any[]
  ) {
    const res = await fetch(`${API}/insight/trend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_year: targetYear,
        original_clusters: originalClusters,
        new_clusters: newClusters,
      }),
    })
    return res.json()
  }

  return { getClusterInsight, getTrajectoryInsight, getScenarioInsight, getTrendInsight }
}

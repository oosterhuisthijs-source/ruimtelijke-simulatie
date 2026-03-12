const API = 'http://localhost:8002/api'

export function useSOM() {
  async function fetchClusters(year: number = 2023) {
    const res = await fetch(`${API}/som/clusters?year=${year}`)
    return res.json()
  }

  async function fetchTrajectory(h3Id: string) {
    const res = await fetch(`${API}/trajectory/${h3Id}`)
    const data = await res.json()
    return data.trajectory ?? []
  }

  async function runScenarioRequest(column: string, changeFactor: number) {
    const res = await fetch(`${API}/scenario/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ column, change_factor: changeFactor, year: 2023 }),
    })
    const data = await res.json()
    return data.results ?? []
  }

  async function runTrendRequest(targetYear: number) {
    const res = await fetch(`${API}/trend/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_year: targetYear }),
    })
    const data = await res.json()
    return data.results ?? []
  }

  return { fetchClusters, fetchTrajectory, runScenarioRequest, runTrendRequest }
}

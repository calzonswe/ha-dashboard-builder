import { HAEntity, HAState, DashboardConfig } from '../types/api'

const API_BASE = '/api'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('auth_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const response = await fetch(url, {
    ...options,
    headers: { ...headers, ...(options?.headers || {}) },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<T>
}

export async function getStates(): Promise<HAState[]> {
  return fetchJSON<HAState[]>(`${API_BASE}/states`)
}

export async function getStateById(entityId: string): Promise<HAState> {
  return fetchJSON<HAState>(`${API_BASE}/states/${entityId}`)
}

export async function getEntities(): Promise<HAEntity[]> {
  const states = await getStates()
  return states.map((s) => ({
    entity_id: s.entity_id,
    object_id: s.entity_id.split('.')[1] || '',
    state: s.state,
    attributes: s.attributes,
    last_changed: s.last_changed,
    last_updated: s.last_updated,
  }))
}

export async function getDashboard(id: string): Promise<DashboardConfig> {
  return fetchJSON<DashboardConfig>(`${API_BASE}/dashboards/${id}`)
}

export async function createDashboard(config: Omit<DashboardConfig, 'id'>): Promise<DashboardConfig> {
  return fetchJSON<DashboardConfig>(`${API_BASE}/dashboards`, {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

export async function updateDashboard(
  id: string,
  config: Partial<DashboardConfig>,
): Promise<DashboardConfig> {
  return fetchJSON<DashboardConfig>(`${API_BASE}/dashboards/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(config),
  })
}

export async function deleteDashboard(id: string): Promise<void> {
  await fetch(`${API_BASE}/dashboards/${id}`, { method: 'DELETE' })
}

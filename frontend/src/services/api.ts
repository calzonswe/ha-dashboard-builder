import { HAEntity, HAState, DashboardConfig, DashboardCard } from '../types/api'

const API_BASE = '/api/v1'

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

// ─── Home Assistant States / Entities ────────────────────────────────

export async function getStates(): Promise<HAState[]> {
  const data = await fetchJSON<{ entities: HAEntity[]; count: number }>('/api/ha/entities')
  return data.entities.map((e) => ({
    entity_id: e.entity_id,
    state: e.state,
    attributes: {},
    last_changed: e.last_changed || '',
    last_updated: '',
  }))
}

export async function getStateById(entityId: string): Promise<HAState | null> {
  try {
    const data = await fetchJSON<{
      entity_id: string
      state: string
      domain?: string
      name?: string
      unit_of_measurement?: string
    }>(`/api/ha/entities/${entityId}`)
    return {
      entity_id: data.entity_id,
      state: data.state,
      attributes: {},
      last_changed: '',
      last_updated: '',
    }
  } catch {
    return null
  }
}

export async function getEntityState(entityId: string): Promise<HAState | null> {
  return getStateById(entityId)
}

export async function getEntities(): Promise<HAEntity[]> {
  const data = await fetchJSON<{
    entities: Array<{
      entity_id: string
      state: string
      name?: string
      domain?: string
      last_changed?: string
      area?: string | null
      unit_of_measurement?: string | null
    }>
    count: number
  }>('/api/ha/entities')
  return data.entities.map((e) => ({
    entity_id: e.entity_id,
    object_id: e.entity_id.split('.')[1] || e.entity_id,
    state: e.state,
    attributes: {},
    last_changed: e.last_changed || '',
    last_updated: '',
  }))
}

// ─── Dashboard CRUD ────────────────────────────────────────────────

interface BackendDashboard {
  id: number
  name: string
  description?: string | null
}

interface BackendWidget {
  id: number
  page_id: number
  card_type: string
  entity_id?: string | null
  title?: string | null
  config?: Record<string, unknown>
  x: number
  y: number
  width: number
  height: number
}

export async function getDashboards(): Promise<DashboardConfig[]> {
  const data = await fetchJSON<{ dashboards: BackendDashboard[]; count: number }>(`${API_BASE}/dashboards`)
  return data.dashboards.map((d) => ({
    id: String(d.id),
    name: d.name,
    description: d.description || undefined,
    cards: [],
  }))
}

export async function getHAStatus(): Promise<{ connected: boolean; host?: string; port?: number; entities?: number; error?: string }> {
  const res = await fetch('/api/ha/status')
  if (!res.ok) return { connected: false }
  return res.json()
}

export async function getDashboard(id: string): Promise<DashboardConfig> {
  const data = await fetchJSON<{
    id: number
    name: string
    description?: string | null
    cards: BackendWidget[]
  }>(`${API_BASE}/dashboards/${id}`)
  return {
    id: String(data.id),
    name: data.name,
    description: data.description || undefined,
    cards: data.cards.map(mapWidgetToCard),
  }
}

function mapWidgetToCard(w: BackendWidget): DashboardCard {
  return {
    id: String(w.id),
    entity_id: w.entity_id || '',
    x: w.x,
    y: w.y,
    width: w.width,
    height: w.height,
    card_type: w.card_type,
    title: w.title || undefined,
    config: {
      type: w.card_type,
      title: w.title || undefined,
      ...(w.config || {}),
    } as DashboardCard['config'],
  }
}

export async function createDashboard(config: { name: string; description?: string }): Promise<DashboardConfig> {
  const data = await fetchJSON<BackendDashboard>(`${API_BASE}/dashboards`, {
    method: 'POST',
    body: JSON.stringify(config),
  })
  return {
    id: String(data.id),
    name: data.name,
    description: data.description || undefined,
    cards: [],
  }
}

export async function updateDashboard(id: string, config: { name?: string; description?: string }): Promise<DashboardConfig> {
  const data = await fetchJSON<BackendDashboard>(`${API_BASE}/dashboards/${id}`, {
    method: 'PUT',
    body: JSON.stringify(config),
  })
  return {
    id: String(data.id),
    name: data.name,
    description: data.description || undefined,
    cards: [],
  }
}

export async function deleteDashboard(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/dashboards/${id}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(`Delete failed: ${response.status} ${response.statusText}`)
  }
}

export async function updateDashboardCards(
  id: string,
  cards: {
    id?: number | null
    card_type: string
    entity_id?: string | null
    title?: string | null
    config?: Record<string, unknown>
    x: number
    y: number
    width: number
    height: number
  }[],
): Promise<{ cards: { id: number; page_id: number; card_type: string }[] }> {
  return fetchJSON<{ cards: { id: number; page_id: number; card_type: string }[] }>(
    `${API_BASE}/dashboards/${id}/cards`,
    {
      method: 'PUT',
      body: JSON.stringify({ cards }),
    },
  )
}

export function getWebSocketUrl(): string {
  return `/api/ws/entities`
}

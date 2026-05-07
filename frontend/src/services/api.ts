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

// ─── Home Assistant States / Entities ────────────────────────────────

export async function getStates(): Promise<HAState[]> {
  return fetchJSON<HAState[]>(`${API_BASE}/states`)
}

export async function getStateById(entityId: string): Promise<HAState> {
  return fetchJSON<HAState>(`${API_BASE}/states/${entityId}`)
}

/** Get the current state of a single entity (returns null if not found) */
export async function getEntityState(entityId: string): Promise<HAState | null> {
  try {
    const result = await fetchJSON<{ entities?: HAState[] }>(`${API_BASE}/states`)
    const entity = result.entities?.find((e) => e.entity_id === entityId)
    return entity || null
  } catch {
    // Fall back to the single-entity endpoint
    try {
      const state = await getStateById(entityId)
      return state
    } catch {
      return null
    }
  }
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

// ─── Dashboard CRUD ────────────────────────────────────────────────

export async function getDashboards(): Promise<DashboardConfig[]> {
  return fetchJSON<DashboardConfig[]>(`${API_BASE}/dashboards`)
}

export async function getDashboard(id: string): Promise<DashboardConfig> {
  return fetchJSON<DashboardConfig>(`${API_BASE}/dashboards/${id}`)
}

export async function createDashboard(
  config: Omit<DashboardConfig, 'id'>,
): Promise<DashboardConfig> {
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
    method: 'PUT',
    body: JSON.stringify(config),
  })
}

export async function deleteDashboard(id: string): Promise<void> {
  await fetch(`${API_BASE}/dashboards/${id}`, { method: 'DELETE' })
}

/** Replace all cards (widgets) on a dashboard atomically. */
interface CardPayload {
  id?: number | null
  card_type: string
  entity_id?: string | null
  title?: string | null
  config?: Record<string, unknown>
  x: number
  y: number
  width: number
  height: number
}

export async function updateDashboardCards(
  id: string,
  cards: CardPayload[],
): Promise<{ cards: { id: number; page_id: number; card_type: string }[] }> {
  return fetchJSON<{ cards: { id: number; page_id: number; card_type: string }[] }>(
    `${API_BASE}/dashboards/${id}/cards`,
    {
      method: 'PUT',
      body: JSON.stringify({ cards }),
    },
  )
}

// ─── SSE / Real-time Events ────────────────────────────────────────

/** Returns the URL for the SSE events stream endpoint */
export function getEventsStreamUrl(): string {
  return `${API_BASE}/events/stream`
}

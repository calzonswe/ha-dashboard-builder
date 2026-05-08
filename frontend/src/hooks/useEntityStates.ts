import { useEntityStates as useWSEntityStates, useWebSocket } from './useWebSocket'

interface UseEntityStatesResult {
  entities: Record<string, { state: string; attributes: Record<string, unknown> }>
  loading: boolean
  error: Error | null
}

export function useEntityStates(): UseEntityStatesResult {
  const { states } = useWSEntityStates()
  return {
    entities: states,
    loading: false,
    error: null,
  }
}

/** @deprecated Use useEntityStates() and access the entity directly from the map. */
export function useEntityState(entityId: string): { state: string } | null {
  const result = useWebSocket(entityId)
  if (!result) return null
  return {
    state: result.state || '',
  }
}

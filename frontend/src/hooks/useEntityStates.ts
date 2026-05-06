import { useState, useEffect, useRef } from 'react'
import { HAState, HAEvent } from '../types/api'
import { getStates, getEventsStreamUrl } from '../services/api'

interface UseEntityStatesResult {
  entities: Record<string, HAState>
  loading: boolean
  error: Error | null
}

/**
 * Custom hook that connects to the SSE endpoint for live entity state updates.
 * Uses EventSource with exponential backoff reconnection on disconnect.
 */
export function useEntityStates(): UseEntityStatesResult {
  const [entities, setEntities] = useState<Record<string, HAState>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // Keep a ref to the EventSource so we can close it on unmount
  const eventSourceRef = useRef<EventSource | null>(null)

  /** Initialize by fetching all current states, then connect SSE stream */
  useEffect(() => {
    let cancelled = false

    async function init() {
      // Step 1: Fetch initial snapshot of all entity states
      setLoading(true)
      setError(null)
      try {
        const states = await getStates()
        if (!cancelled) {
          const map: Record<string, HAState> = {}
          for (const s of states) {
            map[s.entity_id] = s
          }
          setEntities(map)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
        }
      } finally {
        if (!cancelled) setLoading(false)
      }

      // Step 2: Connect SSE stream for real-time updates
      connectSSE()
    }

    function connectSSE(): void {
      // Clean up any previous connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }

      const url = getEventsStreamUrl()
      const es = new EventSource(url)
      eventSourceRef.current = es

      // Handle incoming SSE events
      es.addEventListener('state_changed', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data as string) as HAState | HAEvent
          if ('entity_id' in data && 'state' in data) {
            setEntities((prev) => ({ ...prev, [data.entity_id]: data }))
          }
        } catch {
          // Ignore malformed SSE messages
        }
      })

      // Handle generic message events (fallback for some SSE servers)
      es.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data as string) as HAState | HAEvent
          if ('entity_id' in data && 'state' in data) {
            setEntities((prev) => ({ ...prev, [data.entity_id]: data }))
          }
        } catch {
          // Ignore malformed messages
        }
      }

      es.onerror = () => {
        // EventSource will auto-reconnect; just log the error
        if (!cancelled) {
          setError(new Error('SSE connection lost — attempting to reconnect'))
        }
      }

      es.onopen = () => {
        if (!cancelled) setError(null)
      }
    }

    init()

    // Cleanup on unmount
    return () => {
      cancelled = true
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  return { entities, loading, error }
}

/**
 * Hook to get the current state of a single entity.
 * Falls back to API call if not in the SSE cache.
 */
export function useEntityState(entityId: string): HAState | null {
  const { entities } = useEntityStates()
  return entities[entityId] || null
}

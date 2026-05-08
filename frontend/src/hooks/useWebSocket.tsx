import { createContext, useContext, useEffect, useRef, useState } from 'react'

interface StateChange {
  entity_id: string
  state: string
  attributes: Record<string, unknown>
  last_changed?: string
}

interface WebSocketMessage {
  type: string
  message?: string
  entity_id?: string
  changes?: StateChange[]
}

interface HAState {
  [entityId: string]: {
    state: string
    attributes: Record<string, unknown>
  }
}

// Global state to track all entity states from WebSocket
const EntityStateContext = createContext<{
  states: HAState
  addStates: (changes: StateChange[]) => void
}>({
  states: {},
  addStates: () => {},
})

export function useEntityStates() {
  const { states, addStates } = useContext(EntityStateContext)
  return { states, addStates }
}

/**
 * Hook to get the current state and attributes for a specific entity.
 * Returns null if the entity is not connected or has no state data.
 */
export function useWebSocket(entityId: string) {
  const { states } = useContext(EntityStateContext)

  // Guard against invalid input — must be at top level before any hooks
  if (!entityId || !states[entityId]) return null

  const entityData = states[entityId]
  const attrs = (entityData?.attributes as Record<string, unknown>) ?? {}

  // Helper to safely access numeric attributes
  const getNumericAttr = (key: string): number | null => {
    const val = attrs[key]
    if (typeof val === 'number') return val
    if (typeof val === 'string') {
      const parsed = parseFloat(val)
      return isNaN(parsed) ? null : parsed
    }
    return null
  }

  return {
    state: entityData.state,
    current_temperature: getNumericAttr('current_temperature'),
    target_temperature: getNumericAttr('target_temp_high') ?? getNumericAttr('target_temp_low') ?? getNumericAttr('temperature'),
    hvac_mode: attrs['hvac_mode'] as string | undefined,
    fan_mode: attrs['fan_mode'] as string | undefined,
    swing_mode: attrs['swing_mode'] as string | undefined,
  }
}

export function EntityStateProvider({ children }: { children: React.ReactNode }) {
  const [states, setStates] = useState<HAState>({})
  const wsRef = useRef<WebSocket | null>(null)

  // Manage WebSocket connection
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/entities`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected to HA Dashboard')
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)

        if (message.type === 'state_changed' && message.changes) {
          const changes = message.changes // narrowed type
          // Update local state with new entity states
          setStates((prev) => {
            const next = { ...prev }
            for (const change of changes) {
              next[change.entity_id] = {
                state: change.state,
                attributes: change.attributes || {},
              }
            }
            return next
          })
        } else if (message.type === 'connected') {
          console.log('WebSocket ready:', message.message)
        }
      } catch (e) {
        // Ignore parse errors for non-JSON messages
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting in 5s...')
      reconnectTimeoutRef.current = setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          const retryWs = new WebSocket(wsUrl)
          wsRef.current = retryWs
        }
      }, 5000)
    }

    ws.onerror = () => {
      console.error('WebSocket error')
    }

    return () => {
      ws.close()
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }
  }, [])

  const addStates = (changes: StateChange[]) => {
    setStates((prev) => {
      const next = { ...prev }
      for (const change of changes) {
        next[change.entity_id] = {
          state: change.state,
          attributes: change.attributes || {},
        }
      }
      return next
    })
  }

  return (
    <EntityStateContext.Provider value={{ states, addStates }}>
      {children}
    </EntityStateContext.Provider>
  )
}

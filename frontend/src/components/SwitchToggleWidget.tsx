import { useState, useEffect } from 'react'
import { useEntityStates } from '../hooks/useWebSocket'
import { useToast } from '../hooks/useToast'

interface Widget {
  id: number
  card_type: string
  entity_id?: string | null
  title?: string | null
  config: Record<string, unknown>
  x: number
  y: number
  width: number
  height: number
}

export default function SwitchToggleWidget({ widget, onDelete }: { widget: Widget; onDelete: () => void }) {
  const { states } = useEntityStates()
  const { addToast } = useToast()
  
  // Get the current state from WebSocket context
  const entityData = widget.entity_id ? (states[widget.entity_id] || null) : null
  const currentState = entityData?.state || 'off'
  const [state, setState] = useState<'on' | 'off'>(currentState === 'on' ? 'on' : 'off')
  const [isToggling, setIsToggling] = useState(false)

  // Sync local state when WebSocket reports a change
  useEffect(() => {
    if (widget.entity_id && states[widget.entity_id]) {
      setState(states[widget.entity_id].state as 'on' | 'off')
    }
  }, [states, widget.entity_id])

  const toggleState = async () => {
    if (!widget.entity_id) return

    setIsToggling(true)
    try {
      await fetch('/api/api/ha/service', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: widget.card_type === 'light' ? 'light' : 'switch',
          service: widget.card_type === 'light' ? 'toggle' : 'turn_on',
          target: { entity_id: widget.entity_id },
        }),
      })

      setState((prev) => (prev === 'on' ? 'off' : 'on'))
    } catch {
      addToast(`Failed to toggle ${widget.title || widget.entity_id}`, 'error')
    } finally {
      setIsToggling(false)
    }
  }

  return (
    <div className="bg-white p-3 sm:p-4 rounded-lg shadow hover:shadow-md transition border border-gray-100">
      <div className="flex justify-between items-start mb-2 sm:mb-3 gap-2">
        <h3 className="font-medium text-sm sm:text-base truncate">{widget.title || widget.entity_id}</h3>
        <button onClick={onDelete} className="text-red-400 text-xs hover:text-red-600 transition shrink-0" aria-label={`Delete ${widget.title}`}>
          ✕
        </button>
      </div>

      <button
        onClick={toggleState}
        disabled={!widget.entity_id || isToggling}
        className={`w-full py-2 px-3 rounded font-medium transition text-sm sm:text-base ${
          state === 'on' ? 'bg-green-500 text-white hover:bg-green-600' : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
        }`}
      >
        {isToggling ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-3 h-3 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
              <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" className="opacity-75" />
            </svg>
            ...
          </span>
        ) : (
          state.toUpperCase()
        )}
      </button>

      <p className="text-xs text-gray-500 mt-1.5 sm:mt-2 truncate">{widget.entity_id}</p>
    </div>
  )
}

import { useWebSocket } from '../hooks/useWebSocket'

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

interface ClimateWidgetProps {
  widget: Widget
  onDelete: () => void
}

export default function ClimateControlWidget({ widget, onDelete }: ClimateWidgetProps) {
  const entityState = useWebSocket(widget.entity_id || '')
  const state = entityState?.state || 'unknown'

  // Helper to safely convert numeric values
  const safeNum = (val: number | string | null | undefined): number => {
    if (val === null || val === undefined) return 0
    return typeof val === 'number' ? val : parseFloat(val as string) || 0
  }

  const currentTemp = safeNum(entityState?.current_temperature ?? (entityState as any)?.attributes?.current_temperature)
  const targetTemp = safeNum(
    entityState?.target_temperature ?? 
    ((entityState as any)?.attributes?.target_temp_high as number | undefined) ?? 
    ((entityState as any)?.attributes?.target_temp_low as number | undefined) ?? 
    ((entityState as any)?.attributes?.temperature as number | undefined)
  )

  const title = widget.title || widget.entity_id?.split('.').pop() || 'Climate'

  const handleTempChange = async (delta: number) => {
    if (!widget.entity_id) return
    const newTemp = Math.max(10, Math.min(35, targetTemp + delta))

    try {
      const token = localStorage.getItem('auth_token') || ''
      await fetch('/api/ha/services/call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          domain: 'climate',
          service: 'set_temperature',
          service_data: { entity_id: widget.entity_id, temperature: newTemp },
        }),
      })
    } catch (err) {
      console.error('Failed to adjust temperature:', err)
    }
  }

  const handleModeChange = async (mode: string) => {
    if (!widget.entity_id) return

    try {
      const token = localStorage.getItem('auth_token') || ''
      await fetch('/api/ha/services/call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          domain: 'climate',
          service: 'set_hvac_mode',
          service_data: { entity_id: widget.entity_id, hvac_mode: mode },
        }),
      })
    } catch (err) {
      console.error('Failed to change climate mode:', err)
    }
  }

  const modes = ['off', 'heat', 'cool', 'auto', 'dry', 'fan_only'] as const
  const activeMode = state === 'on' ? ((entityState?.hvac_mode as string) || 'auto') : 'off'

  return (
    <div className="bg-white p-3 sm:p-4 rounded-lg shadow border border-gray-100 hover:shadow-md transition group relative">
      {/* Delete button */}
      <button
        onClick={onDelete}
        className="absolute top-2 right-2 text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition"
        aria-label={`Delete ${title}`}
      >
        &times;
      </button>

      <div className="text-center">
        {/* Title */}
        <p className="text-sm font-medium text-gray-700 truncate mb-2">{title}</p>

        {/* Temperature display */}
        <div className="flex items-center justify-center gap-4 my-3">
          {/* Decrease button */}
          <button
            onClick={() => handleTempChange(-1)}
            className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full hover:bg-gray-200 transition text-lg font-bold"
            aria-label="Decrease temperature"
          >
            −
          </button>

          {/* Current temp */}
          <div className="text-center">
            <p className={`text-3xl sm:text-4xl font-bold ${state === 'on' ? 'text-orange-500' : 'text-gray-400'}`}>
              {isNaN(currentTemp) ? '--' : currentTemp}°
            </p>
            <p className="text-xs text-gray-500">Current</p>
          </div>

          {/* Target temp */}
          <div className="text-center">
            <p className={`text-3xl sm:text-4xl font-bold ${state === 'on' ? 'text-blue-500' : 'text-gray-400'}`}>
              {isNaN(targetTemp) ? '--' : targetTemp}°
            </p>
            <p className="text-xs text-gray-500">Target</p>
          </div>

          {/* Increase button */}
          <button
            onClick={() => handleTempChange(1)}
            className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full hover:bg-gray-200 transition text-lg font-bold"
            aria-label="Increase temperature"
          >
            +
          </button>
        </div>

        {/* Mode selector */}
        <div className="flex flex-wrap gap-1 justify-center">
          {modes.map((mode) => (
            <button
              key={mode}
              onClick={() => handleModeChange(mode)}
              className={`px-2 py-1 text-xs rounded transition ${
                mode === activeMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>

        {/* Status */}
        <p className="text-xs text-gray-400 mt-2 truncate">{widget.entity_id}</p>
      </div>
    </div>
  )
}

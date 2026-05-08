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

interface SensorWidgetProps {
  widget: Widget
  onDelete: () => void
}

export default function SensorWidget({ widget, onDelete }: SensorWidgetProps) {
  const entityState = useWebSocket(widget.entity_id || '')
  const state = entityState?.state || 'unknown'
  const unit = (widget.config.unit as string) || ''

  // Determine icon based on domain/type
  const getIcon = () => {
    switch (widget.card_type) {
      case 'temperature': return '🌡️'
      case 'humidity': return '💧'
      case 'pressure': return '🔵'
      case 'battery': return '🔋'
      case 'power': return '⚡'
      case 'energy': return '📊'
      default: return '📈'
    }
  }

  // Color based on state value for numeric sensors
  const getStateColor = () => {
    const numState = parseFloat(state)
    if (isNaN(numState)) return 'text-gray-700'

    switch (widget.card_type) {
      case 'temperature':
        return numState < 15 ? 'text-blue-600' : numState > 25 ? 'text-red-600' : 'text-green-600'
      case 'humidity':
        return numState < 30 ? 'text-red-600' : numState > 70 ? 'text-blue-600' : 'text-green-600'
      case 'battery':
        return numState < 20 ? 'text-red-600' : numState < 50 ? 'text-yellow-600' : 'text-green-600'
      default:
        return 'text-gray-700'
    }
  }

  const title = widget.title || widget.entity_id?.split('.').pop() || 'Sensor'

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

      <div className="flex items-start gap-3">
        {/* Icon */}
        <span className="text-2xl sm:text-3xl mt-0.5">{getIcon()}</span>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-700 truncate mb-1">{title}</p>
          <p className={`text-xl sm:text-2xl font-bold ${getStateColor()}`}>
            {state}
            {unit && <span className="text-sm ml-1 font-normal">{unit}</span>}
          </p>
        </div>

        {/* State badge */}
        <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
          state === 'on' || state === 'home' ? 'bg-green-100 text-green-700' :
          state === 'off' || state === 'away' ? 'bg-gray-200 text-gray-600' :
          'bg-yellow-100 text-yellow-700'
        }`}>
          {state}
        </span>
      </div>

      {/* Entity ID */}
      <p className="text-xs text-gray-400 mt-2 truncate">{widget.entity_id}</p>
    </div>
  )
}

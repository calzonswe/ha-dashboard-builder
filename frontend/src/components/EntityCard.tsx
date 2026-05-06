import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { DashboardCard } from '../types/api'

interface EntityCardProps {
  card: DashboardCard
  entityState?: string
  onConfigure: (cardId: string) => void
}

const DOMAIN_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  light: { bg: 'bg-yellow-50', border: 'border-yellow-300', text: 'text-yellow-700' },
  sensor: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-700' },
  switch: { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-700' },
  cover: { bg: 'bg-purple-50', border: 'border-purple-300', text: 'text-purple-700' },
  fan: { bg: 'bg-teal-50', border: 'border-teal-300', text: 'text-teal-700' },
  climate: { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-700' },
  media_player: { bg: 'bg-indigo-50', border: 'border-indigo-300', text: 'text-indigo-700' },
  camera: { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-700' },
}

const DOMAIN_ICONS: Record<string, string> = {
  light: '💡',
  sensor: '📊',
  switch: '🔘',
  cover: '🪟',
  fan: '🌀',
  climate: '🌡️',
  media_player: '🎵',
  camera: '📷',
}

const getDomain = (entityId: string): string => {
  return entityId.split('.')[0] || ''
}

const EntityCard: React.FC<EntityCardProps> = ({ card, entityState, onConfigure }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id, data: card })

  const domain = getDomain(card.entity_id)
  const colors = DOMAIN_COLORS[domain] || DOMAIN_COLORS.sensor
  const icon = DOMAIN_ICONS[domain] || '📦'

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 1000 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`relative rounded-lg border-2 ${colors.border} ${colors.bg} shadow-md hover:shadow-xl transition-all duration-200 cursor-grab active:cursor-grabbing`}
      data-entity-id={card.entity_id}
    >
      {/* Drag handle */}
      <div
        {...listeners}
        {...attributes}
        className="absolute top-1 left-1 w-6 h-6 flex items-center justify-center rounded-full bg-white/80 hover:bg-white cursor-grab z-10"
        style={{ touchAction: 'none' }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
          <path d="M7 4a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM7 8.5a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM7 12a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM13 4a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM13 8.5a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM13 12a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5z" />
        </svg>
      </div>

      {/* Card content */}
      <div className="p-3">
        {/* Header with icon and title */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">{icon}</span>
          <h3 className="font-medium text-sm truncate flex-1" title={card.entity_id}>
            {card.config?.title || card.entity_id.split('.').slice(1).join('.')}
          </h3>
        </div>

        {/* State display */}
        <div className={`text-lg font-semibold ${colors.text}`}>
          {entityState !== undefined ? entityState : '—'}
        </div>

        {/* Entity ID (truncated) */}
        <p className="text-xs text-gray-500 mt-1 truncate" title={card.entity_id}>
          {card.entity_id}
        </p>

        {/* Card type badge */}
        <span className="inline-block mt-2 px-2 py-0.5 text-xs rounded-full bg-white/60 border border-gray-200">
          {(card.config?.type || 'state').charAt(0).toUpperCase() + (card.config?.type || 'state').slice(1)}
        </span>

        {/* Configure button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onConfigure(card.id)
          }}
          className="absolute bottom-2 right-2 p-1 rounded-full hover:bg-white/60 transition-colors"
          title="Configure card"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M5.75 12a1.75 1.75 0 113.5 0 1.75 1.75 0 01-3.5 0zM10.75 8a1.75 1.75 0 103.5 0 1.75 1.75 0 00-3.5 0zM12.25 14.25a1.75 1.75 0 103.5 0 1.75 1.75 0 00-3.5 0z" />
          </svg>
        </button>

        {/* Dragging overlay */}
        {isDragging && (
          <div className="absolute inset-0 rounded-lg border-2 border-dashed border-blue-400 bg-blue-50/50 pointer-events-none" />
        )}
      </div>
    </div>
  )
}

export default EntityCard

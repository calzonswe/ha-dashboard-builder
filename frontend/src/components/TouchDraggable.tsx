import React, { useState, useRef, useCallback } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { HAEntity } from '../types/api'

interface TouchDraggableProps {
  entity: HAEntity
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

const TouchDraggable: React.FC<TouchDraggableProps> = ({ entity }) => {
  const [isLongPress, setIsLongPress] = useState(false)
  const longPressTimerRef = useRef<number | undefined>(undefined)
  const touchStartPos = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null)

  // Long press activation (500ms hold) for touch devices
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0]
    touchStartPos.current = { x: touch.clientX, y: touch.clientY }

    longPressTimerRef.current = window.setTimeout(() => {
      setIsLongPress(true)
      // Haptic feedback if available
      if (navigator.vibrate) navigator.vibrate(50)
    }, 500)
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    // Cancel long press if user moves significantly
    const touch = e.touches[0]
    const dx = Math.abs(touch.clientX - touchStartPos.current.x)
    const dy = Math.abs(touch.clientY - touchStartPos.current.y)

    if (dx > 10 || dy > 10) {
      if (longPressTimerRef.current !== undefined) {
        window.clearTimeout(longPressTimerRef.current)
        longPressTimerRef.current = undefined
      }

      // Detect swipe direction for card reordering feedback
      if (dx > dy && dx > 30) {
        setSwipeDirection(touch.clientX > touchStartPos.current.x ? 'right' : 'left')
      } else {
        setSwipeDirection(null)
      }
    }
  }, [])

  const handleTouchEnd = useCallback(() => {
    if (longPressTimerRef.current !== undefined) {
      window.clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = undefined
    }

    // Reset swipe direction after a short delay for visual feedback
    if (swipeDirection) {
      window.setTimeout(() => setSwipeDirection(null), 300)
    }

    setIsLongPress(false)
  }, [swipeDirection])

  const handleTouchCancel = useCallback(() => {
    if (longPressTimerRef.current !== undefined) {
      window.clearTimeout(longPressTimerRef.current)
      longPressTimerRef.current = undefined
    }
    setIsLongPress(false)
    setSwipeDirection(null)
  }, [])

  // useSortable for drag functionality
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: `touch-${entity.entity_id}`, data: entity })

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 1000 : 1,
  }

  const icon = DOMAIN_ICONS[entity.entity_id.split('.')[0] || ''] || '📦'

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`relative rounded-lg border-2 border-gray-300 bg-white shadow-sm hover:shadow-md transition-all duration-200 ${
        isDragging ? 'opacity-80 scale-[1.02]' : ''
      }`}
      data-entity-id={entity.entity_id}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchCancel}
    >
      {/* Swipe feedback indicator */}
      {swipeDirection && (
        <div className={`absolute inset-0 rounded-lg pointer-events-none transition-opacity duration-200 ${
          swipeDirection === 'left' ? 'bg-blue-100/30 opacity-100' : 'bg-green-100/30 opacity-100'
        }`} />
      )}

      {/* Long press visual feedback */}
      {isLongPress && (
        <div className="absolute inset-0 rounded-lg border-2 border-dashed border-blue-400 bg-blue-50/60 pointer-events-none" />
      )}

      {/* Touch target - min 44px for accessibility */}
      <button
        {...listeners}
        {...attributes}
        className="w-full h-[48px] flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 active:bg-gray-100 transition-colors cursor-grab active:cursor-grabbing"
        style={{ touchAction: 'none' }}
        aria-label={`Drag ${entity.object_id}`}
      >
        <span className="text-xl flex-shrink-0">{icon}</span>
        <span className="flex-1 text-sm font-medium text-gray-800 truncate">
          {entity.object_id}
        </span>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full flex-shrink-0 min-w-[36px] text-center">
          {entity.state || '—'}
        </span>
      </button>

      {/* Drag handle for desktop (hidden on touch) */}
      <div
        className="absolute top-2 left-2 w-7 h-7 flex items-center justify-center rounded-full bg-white/80 hover:bg-white cursor-grab z-10 sm:hidden"
        style={{ touchAction: 'none' }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
          <path d="M7 4a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM7 8.5a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM7 12a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM13 4a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM13 8.5a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5zM13 12a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5z" />
        </svg>
      </div>

      {/* Touch hint on first load */}
      {!isLongPress && !isDragging && (
        <span className="absolute bottom-1 right-2 text-[10px] text-gray-300 sm:hidden">
          Hold to drag
        </span>
      )}
    </div>
  )
}

export default TouchDraggable

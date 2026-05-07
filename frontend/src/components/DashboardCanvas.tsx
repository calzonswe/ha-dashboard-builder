import React, { useCallback } from 'react'
import {
  DndContext,
  DragOverlay,
  useSensor,
  useSensors,
  PointerSensor,
  TouchSensor,
} from '@dnd-kit/core'
import type {
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  rectSortingStrategy,
} from '@dnd-kit/sortable'
import EntityCard from './EntityCard'
import type { DashboardCard } from '../types/api'

interface DashboardCanvasProps {
  cards: DashboardCard[]
  entityStates: Record<string, string>
  onCardsChange: (cards: DashboardCard[]) => void
  onConfigureCard: (cardId: string) => void
}

const GRID_SIZE = 16 // pixels per grid cell

/** Snap a coordinate to the nearest grid position */
function snapToGrid(value: number): number {
  return Math.round(value / GRID_SIZE) * GRID_SIZE
}

const DashboardCanvas: React.FC<DashboardCanvasProps> = ({
  cards,
  entityStates,
  onCardsChange,
  onConfigureCard,
}) => {
  const [activeId, setActiveId] = React.useState<string | null>(null)
  const [dragPosition, setDragPosition] = React.useState<{ x: number; y: number }>({ x: 0, y: 0 })

  // Detect if device supports touch for appropriate sensor configuration
  const isTouchDevice = React.useMemo(() => {
    return ('ontouchstart' in window || navigator.maxTouchPoints > 0)
  }, [])

  // Sensors for drag interaction - TouchSensor on touch devices, PointerSensor on desktop
  const pointerSensor = useSensor(PointerSensor, {
    activationConstraint: { distance: 5 }, // require 5px movement before dragging starts
  })

  const sensors = isTouchDevice
    ? useSensors(useSensor(TouchSensor))
    : useSensors(pointerSensor)

  /** Find the grid cell (x,y in grid units) from an activator event */
  function getGridPosition(activatorEvent: Event | null): { x: number; y: number } {
    if (!activatorEvent || !('target' in activatorEvent)) return { x: 0, y: 0 }
    const target = (activatorEvent as unknown as { target: HTMLElement }).target
    if (!target || !('getBoundingClientRect' in target)) return { x: 0, y: 0 }
    const rect = target.getBoundingClientRect()
    return {
      x: snapToGrid(rect.left),
      y: snapToGrid(rect.top),
    }
  }

  // ─── Drag handlers ──────────────────────────────────────────────

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      setActiveId(String(event.active.id))
    },
    [],
  )

  const handleDragOver = useCallback(
    (event: DragOverEvent) => {
      if (!event.over || !activeId) return

      // Get the current active card and its new position from drag event
      const pointerEvent = event.activatorEvent as Event | null
      if (pointerEvent) {
        const pos = getGridPosition(pointerEvent)
        setDragPosition(pos)
      }
    },
    [activeId],
  )

  const handleDragEnd = useCallback(
    (_event: DragEndEvent) => {
      setActiveId(null)
      setDragPosition({ x: 0, y: 0 })

      if (!cards.length || !activeId) return

      // Find the dragged card and update its position
      const draggedCard = cards.find((c) => c.id === activeId)
      if (!draggedCard) return

      // Calculate new grid-aligned position from drag offset
      let newX = snapToGrid(dragPosition.x)
      let newY = snapToGrid(dragPosition.y)

      const updatedCards = cards.map((c) =>
        c.id === activeId ? { ...c, x: newX, y: newY } : c,
      )
      onCardsChange(updatedCards)
    },
    [cards, activeId, dragPosition, onCardsChange],
  )

  // ─── Canvas dimensions ──────────────────────────────────────────

  const canvasWidth = React.useMemo(() => {
    if (cards.length === 0) return 640
    const maxX = Math.max(...cards.map((c) => c.x + c.width * GRID_SIZE))
    return Math.max(640, maxX)
  }, [cards])

  const canvasHeight = React.useMemo(() => {
    if (cards.length === 0) return 480
    const maxY = Math.max(...cards.map((c) => c.y + c.height * GRID_SIZE))
    return Math.max(480, maxY)
  }, [cards])

  // ─── Render ─────────────────────────────────────────────────────

  const activeCard = cards.find((c) => c.id === activeId) || null

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      {/* Canvas container - responsive with scroll support */}
      <div className="relative w-full overflow-auto bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 min-h-[480px] touch-pan-x touch-pan-y">
        {/* Grid background pattern */}
        <div
          className="relative"
          style={{ width: canvasWidth, height: canvasHeight }}
          data-testid="dashboard-canvas"
        >
          {/* Dot grid background */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none opacity-20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <pattern id="grid-pattern" width={GRID_SIZE * 4} height={GRID_SIZE * 4} patternUnits="userSpaceOnUse">
                <circle cx={GRID_SIZE * 2} cy={GRID_SIZE * 2} r={1.5} fill="#9CA3AF" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid-pattern)" />
          </svg>

          {/* Sortable card list */}
          <SortableContext items={cards.map((c) => c.id)} strategy={rectSortingStrategy}>
            {cards.map((card) => (
              <div
                key={card.id}
                className="absolute"
                style={{
                  left: card.x,
                  top: card.y,
                  width: card.width * GRID_SIZE,
                  height: card.height * GRID_SIZE,
                }}
              >
                <EntityCard
                  card={card}
                  entityState={entityStates[card.entity_id]}
                  onConfigure={onConfigureCard}
                />
              </div>
            ))}

            {/* Empty state */}
            {cards.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center p-8 sm:p-12">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4 text-gray-300" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M5.5 16a3.5 3.5 0 110-7 3.5 3.5 0 010 7zM15 16a3.5 3.5 0 110-7 3.5 3.5 0 010 7z" />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-500 mb-2">No cards yet</h3>
                  <p className="text-sm text-gray-400 max-w-xs mx-auto">
                    {isTouchDevice
                      ? 'Open the sidebar drawer and hold an entity to drag it onto this canvas.'
                      : 'Drag entities from the sidebar onto this canvas to start building your dashboard.'}
                  </p>
                </div>
              </div>
            )}
          </SortableContext>

          {/* Active drag overlay */}
          <DragOverlay dropAnimation={null}>
            {activeCard ? (
              <div
                className="opacity-80"
                style={{
                  left: dragPosition.x,
                  top: dragPosition.y,
                  width: activeCard.width * GRID_SIZE,
                  height: activeCard.height * GRID_SIZE,
                }}
              >
                <EntityCard card={activeCard} entityState={entityStates[activeCard.entity_id]} onConfigure={() => {}} />
              </div>
            ) : null}
          </DragOverlay>
        </div>
      </div>
    </DndContext>
  )
}

export default DashboardCanvas

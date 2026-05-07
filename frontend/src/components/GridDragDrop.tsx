import { useState, useRef } from 'react'
import React from 'react'

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

interface GridDragDropProps {
  widgets: Widget[]
  onReorder: (widgets: Widget[]) => void
  children: React.ReactNode
}

export default function GridDragDrop({ widgets, onReorder, children }: GridDragDropProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const dragRef = useRef<{ id: number; offsetX: number; offsetY: number } | null>(null)

  // Handle click to select/deselect widget
  const handleWidgetClick = (widgetId: number) => {
    if (selectedId === widgetId) {
      setSelectedId(null)
    } else {
      setSelectedId(widgetId)
    }
  }

  // Handle drag start - record which widget is being dragged and mouse offset
  const handleDragStart = (e: React.DragEvent, widgetId: number) => {
    e.preventDefault()
    const widget = widgets.find((w) => w.id === widgetId)
    if (!widget) return

    dragRef.current = {
      id: widgetId,
      offsetX: e.clientX - (e.currentTarget as HTMLElement).getBoundingClientRect().left,
      offsetY: e.clientY - (e.currentTarget as HTMLElement).getBoundingClientRect().top,
    }
    setSelectedId(widgetId)
  }

  // Handle drag over a drop target - calculate new position based on grid
  const handleDragOver = (e: React.DragEvent, targetWidget: Widget) => {
    e.preventDefault()
    if (!dragRef.current || dragRef.current.id === targetWidget.id) return

    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    const x = Math.floor((e.clientX - rect.left) / (rect.width / 4)) // 4-column grid
    const y = Math.floor((e.clientY - rect.top) / (rect.height / 2)) // 2-row zones

    // Snap to nearest grid position within bounds
    const newX = Math.max(0, Math.min(targetWidget.x + x, 12))
    const newY = Math.max(0, targetWidget.y + y)

    // Create updated widgets array with the dragged widget moved to new position
    const updatedWidgets = widgets.map((w) => {
      if (w.id === dragRef.current!.id) {
        return { ...w, x: newX, y: newY }
      }
      return w
    })

    onReorder(updatedWidgets)
  }

  // Handle drop - finalize position and clear drag state
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    dragRef.current = null
  }

  // Keyboard navigation for selected widget
  const handleKeyDown = (e: React.KeyboardEvent, widgetId: number) => {
    if (!selectedId || selectedId !== widgetId) return

    const step = e.shiftKey ? 2 : 1
    let moved = false

    const updatedWidgets = widgets.map((w) => {
      if (w.id === widgetId) {
        switch (e.key) {
          case 'ArrowUp':
            return { ...w, y: Math.max(0, w.y - step) }
          case 'ArrowDown':
            return { ...w, y: w.y + step }
          case 'ArrowLeft':
            return { ...w, x: Math.max(0, w.x - step) }
          case 'ArrowRight':
            return { ...w, x: Math.min(12, w.x + step) }
          default:
            return w
        }
      }
      return w
    })

    if (updatedWidgets.find((w) => w.id === widgetId)?.x !== widgets.find((w) => w.id === widgetId)?.x ||
        updatedWidgets.find((w) => w.id === widgetId)?.y !== widgets.find((w) => w.id === widgetId)?.y) {
      moved = true
      onReorder(updatedWidgets)
    }

    if (e.key === 'Escape') {
      setSelectedId(null)
    }
  }

  return (
    <div className="relative">
      {/* Grid background */}
      <div className="absolute inset-0 grid grid-cols-4 gap-3 sm:gap-4 pointer-events-none opacity-5">
        {Array.from({ length: 16 }).map((_, i) => (
          <div key={i} className="border border-gray-200 rounded" />
        ))}
      </div>

      {/* Widget grid with drag support */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 relative">
        {React.Children.map(children, (child) => {
          if (!React.isValidElement(child)) return child

          const widgetId = child.props.widget?.id
          const isSelected = selectedId === widgetId
          const isDragging = dragRef.current?.id === widgetId

          // Wrap each widget with drag handlers
          return React.cloneElement(child as React.ReactElement, {
            ...child.props,
            'data-widget-id': widgetId,
            draggable: true,
            onDragStart: (e: React.DragEvent) => handleDragStart(e, widgetId),
            onDragOver: (e: React.DragEvent) => handleDragOver(e, child.props.widget),
            onDrop: handleDrop,
            onClick: () => handleWidgetClick(widgetId),
            onKeyDown: (e: React.KeyboardEvent) => handleKeyDown(e, widgetId),
            className: `${child.props.className || ''} ${isSelected ? 'ring-2 ring-blue-400 shadow-lg' : ''} ${isDragging ? 'opacity-50 scale-95' : ''}`,
          })
        })}
      </div>

      {/* Selection info */}
      {selectedId && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg text-sm z-50">
          <span>Selected: Widget #{selectedId}</span>
          <span className="mx-3 text-gray-400">|</span>
          <span className="text-gray-300">Use arrow keys to move, Esc to deselect</span>
        </div>
      )}
    </div>
  )
}

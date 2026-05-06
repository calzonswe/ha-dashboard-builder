import React, { useState } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { HAEntity } from '../types/api'

interface EntitySidebarProps {
  entities: HAEntity[]
}

const DOMAIN_GROUPS = ['light', 'sensor', 'switch', 'cover', 'fan', 'climate', 'media_player', 'camera'] as const

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

const EntitySidebar: React.FC<EntitySidebarProps> = ({ entities }) => {
  const [search, setSearch] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})

  // Group entities by domain
  const grouped = React.useMemo(() => {
    const groups: Record<string, HAEntity[]> = {}
    for (const entity of entities) {
      const domain = entity.entity_id.split('.')[0] || 'other'
      if (!groups[domain]) groups[domain] = []
      groups[domain].push(entity)
    }
    return groups
  }, [entities])

  // Filter by search
  const filteredGroups = React.useMemo(() => {
    if (!search.trim()) return grouped
    const q = search.toLowerCase()
    const result: Record<string, HAEntity[]> = {}
    for (const [domain, ents] of Object.entries(grouped)) {
      const filtered = ents.filter(
        (e) => e.entity_id.toLowerCase().includes(q) || e.object_id?.toLowerCase().includes(q),
      )
      if (filtered.length > 0) result[domain] = filtered
    }
    return result
  }, [grouped, search])

  const toggleGroup = (domain: string) => {
    setExpandedGroups((prev) => ({ ...prev, [domain]: !prev[domain] }))
  }

  // Drag preview item for dnd-kit
  const DragPreviewItem: React.FC<{ entity: HAEntity }> = ({ entity }) => {
    const { setNodeRef, transform, transition } = useSortable({
      id: `preview-${entity.entity_id}`,
      data: entity,
      disabled: true, // Only for visual preview during drag from sidebar
    })

    const style: React.CSSProperties = {
      transform: CSS.Transform.toString(transform),
      transition,
    }

    return (
      <div ref={setNodeRef} style={style} className="mb-1">
        <SidebarEntityItem entity={entity} />
      </div>
    )
  }

  const totalEntities = entities.length

  return (
    <aside className="w-72 bg-white border-r border-gray-200 flex flex-col h-full overflow-hidden">
      {/* Sidebar header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2 4a1 1 0 012 0v2.586l1.707 1.707A1 1 0 014.122 9H3V4zm10 0a1 1 0 012 0v2.586l1.707 1.707A1 1 0 0116.122 9h-1.122V4zM3 10v6a1 1 0 001 1h12a1 1 0 001-1v-6H3zm7-1a1 1 0 100 2 1 1 0 000-2z" />
          </svg>
          Entities ({totalEntities})
        </h2>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search entities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
          />
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 absolute left-2.5 top-2.5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.415l-4.817-4.817A6 6 0 012 8z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {/* Entity groups */}
      <div className="flex-1 overflow-y-auto">
        {DOMAIN_GROUPS.map((domain) => {
          const ents = filteredGroups[domain] || []
          if (ents.length === 0 && !search.trim()) return null

          const isExpanded = expandedGroups[domain] !== false // default true unless explicitly collapsed
          const icon = DOMAIN_ICONS[domain] || '📦'

          return (
            <div key={domain} className="border-b border-gray-100">
              {/* Group header */}
              <button
                onClick={() => toggleGroup(domain)}
                className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
              >
                <span className="text-sm font-medium text-gray-700">
                  {icon} {domain.charAt(0).toUpperCase() + domain.slice(1)} ({ents.length})
                </span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className={`h-4 w-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : '-rotate-90'}`}
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>

              {/* Entity items */}
              {isExpanded && (
                <div className="px-2 pb-2">
                  {ents.map((entity) => (
                    <DragPreviewItem key={entity.entity_id} entity={entity} />
                  ))}
                </div>
              )}
            </div>
          )
        })}

        {/* No results */}
        {search.trim() && Object.keys(filteredGroups).length === 0 && (
          <div className="p-8 text-center text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-2 opacity-50" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.415l-4.817-4.817A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
            <p className="text-sm">No entities match your search</p>
          </div>
        )}
      </div>

      {/* Footer hint */}
      <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-400 text-center">
        Drag entities onto the canvas to add cards
      </div>
    </aside>
  )
}

// Standalone entity item (used inside sidebar)
const SidebarEntityItem: React.FC<{ entity: HAEntity }> = ({ entity }) => {
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Dispatch custom drag event for dnd-kit integration
    window.dispatchEvent(
      new CustomEvent('ha-entity-drag-start', { detail: { entityId: entity.entity_id } }),
    )
  }

  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-blue-50 cursor-grab transition-colors group"
      onMouseDown={handleMouseDown}
      data-entity-id={entity.entity_id}
    >
      <span className="text-sm flex-1 truncate">{entity.object_id}</span>
      <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
        {entity.state}
      </span>
    </div>
  )
}

export default EntitySidebar

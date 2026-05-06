import React, { useState, useRef, useEffect } from 'react'
import TouchDraggable from './TouchDraggable'
import type { HAEntity } from '../types/api'

interface MobileSidebarProps {
  isOpen: boolean
  onClose: () => void
  entities?: HAEntity[]
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

const MobileSidebar: React.FC<MobileSidebarProps> = ({ isOpen, onClose, entities }) => {
  const [search, setSearch] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})
  const drawerRef = useRef<HTMLDivElement>(null)

  // Default all groups to expanded on first open
  useEffect(() => {
    if (isOpen && Object.keys(expandedGroups).length === 0) {
      const initial: Record<string, boolean> = {}
      DOMAIN_GROUPS.forEach((g) => (initial[g] = true))
      setExpandedGroups(initial)
    }
  }, [isOpen])

  // Swipe down to close gesture
  const handleTouchStart = (e: React.TouchEvent) => {
    drawerRef.current && (touchStartY.current = e.touches[0].clientY)
  }
  const touchStartY = useRef<number>(0)

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!drawerRef.current) return
    const deltaY = e.touches[0].clientY - touchStartY.current
    
    // If swiping down significantly and we're near the top, allow close
    if (deltaY > 100 && drawerRef.current.style.transform !== 'translateY(0px)') {
      onClose()
    }
  }

  const toggleGroup = (domain: string) => {
    setExpandedGroups((prev) => ({ ...prev, [domain]: !prev[domain] }))
  }

  // Group entities by domain
  const grouped = React.useMemo(() => {
    const groups: Record<string, HAEntity[]> = {}
    for (const entity of entities || []) {
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

  const totalEntities = entities?.length || 0

  return (
    <>
      {/* Backdrop overlay */}
      <div
        className={`fixed inset-0 bg-black/40 z-[55] transition-opacity duration-300 sm:hidden ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Bottom drawer */}
      <div
        ref={drawerRef}
        className={`fixed bottom-0 left-0 right-0 z-[56] sm:hidden transition-transform duration-300 ease-out ${
          isOpen ? 'translate-y-0' : 'translate-y-full'
        }`}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
      >
        {/* Drawer handle for swipe gesture */}
        <div className="flex justify-center pt-2 pb-1">
          <div className="w-10 h-1.5 bg-gray-300 rounded-full" />
        </div>

        {/* Drawer content */}
        <div className="bg-white rounded-t-2xl shadow-2xl max-h-[70vh] overflow-hidden flex flex-col">
          {/* Header with search */}
          <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-gray-800 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 4a1 1 0 012 0v2.586l1.707 1.707A1 1 0 014.122 9H3V4zm10 0a1 1 0 012 0v2.586l1.707 1.707A1 1 0 0116.122 9h-1.122V4zM3 10v6a1 1 0 001 1h12a1 1 0 001-1v-6H3zm7-1a1 1 0 100 2 1 1 0 000-2z" />
                </svg>
                Entities ({totalEntities})
              </h2>
              <button
                onClick={onClose}
                className="p-1.5 rounded-full hover:bg-gray-200 transition-colors"
                aria-label="Close sidebar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>

            {/* Search input */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search entities..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent bg-white shadow-sm"
              />
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.415l-4.817-4.817A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
          </div>

          {/* Entity groups - scrollable */}
          <div className="flex-1 overflow-y-auto">
            {DOMAIN_GROUPS.map((domain) => {
              const ents = filteredGroups[domain] || []
              if (ents.length === 0 && !search.trim()) return null

              const isExpanded = expandedGroups[domain] !== false
              const icon = DOMAIN_ICONS[domain] || '📦'

              return (
                <div key={domain} className="border-b border-gray-100">
                  {/* Group header - accordion */}
                  <button
                    onClick={() => toggleGroup(domain)}
                    className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left active:bg-gray-200"
                  >
                    <span className="text-sm font-medium text-gray-700">
                      {icon} {domain.charAt(0).toUpperCase() + domain.slice(1)} ({ents.length})
                    </span>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className={`h-5 w-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : '-rotate-90'}`}
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>

                  {/* Entity items */}
                  {isExpanded && (
                    <div className="px-2 pb-3">
                      {ents.map((entity) => (
                        <TouchDraggable key={entity.entity_id} entity={entity} />
                      ))}
                    </div>
                  )}
                </div>
              )
            })}

            {/* No results */}
            {search.trim() && Object.keys(filteredGroups).length === 0 && (
              <div className="p-8 text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-2 opacity-50" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.415l-4.817-4.817A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-gray-500">No entities match your search</p>
              </div>
            )}
          </div>

          {/* Footer hint */}
          <div className="px-4 py-3 border-t border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 text-xs text-gray-500 text-center rounded-b-2xl">
            📱 Hold an entity to drag it onto the canvas
          </div>
        </div>
      </div>
    </>
  )
}

export default MobileSidebar

import { useState, useEffect } from 'react'
import { useToast } from '../hooks/useToast'

interface CachedEntity {
  entity_id: string
  domain: string
  name: string
  state?: string
  area?: string | null
}

interface EntityPickerModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (entityId: string, cardType: string) => void
}

export default function EntityPickerModal({
  isOpen,
  onClose,
  onSelect,
}: EntityPickerModalProps) {
  const { addToast } = useToast()
  const [searchQuery, setSearchQuery] = useState('')
  const [domainFilter, setDomainFilter] = useState('all')
  const [areaFilter, setAreaFilter] = useState('all')
  const [entities, setEntities] = useState<CachedEntity[]>([])
  const [loading, setLoading] = useState(false)
  const [areas, setAreas] = useState<string[]>(['all'])

  useEffect(() => {
    if (!isOpen) return
    fetchEntities()
    fetchAreas()
  }, [isOpen])

  useEffect(() => {
    if (!isOpen || !searchQuery.trim()) return

    const timeout = setTimeout(async () => {
      try {
        const res = await fetch('/api/ha/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: searchQuery }),
        })
        if (res.ok) {
          const data = await res.json()
          setEntities(data.entities || [])
        }
      } catch {
        addToast('Could not search entities', 'error')
      }
    }, 300)

    return () => clearTimeout(timeout)
  }, [isOpen, searchQuery])

  const fetchAreas = async () => {
    try {
      const res = await fetch('/api/ha/entities')
      if (res.ok) {
        const data = await res.json()
        const uniqueAreas = [...new Set(data.entities.map((e: CachedEntity) => e.area).filter(Boolean))] as string[]
        setAreas(['all', ...uniqueAreas])
      }
    } catch {
      // Non-critical - areas will just not be filterable
    }
  }

  const fetchEntities = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/ha/entities')
      if (res.ok) {
        const data = await res.json()
        setEntities(data.entities || [])
      }
    } catch {
      addToast('Could not load entities', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Filter entities by domain and area
  const filteredEntities = entities.filter((e) => {
    const matchesDomain = domainFilter === 'all' || e.domain === domainFilter
    const matchesArea = areaFilter === 'all' || e.area === areaFilter
    return matchesDomain && matchesArea
  })

  // Get unique domains for filter dropdown
  const domains = [...new Set(entities.map((e) => e.domain))]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-100 shrink-0">
          <h2 className="text-lg font-semibold">Add Widget</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none" aria-label="Close">
            &times;
          </button>
        </div>

        {/* Search and filters */}
        <div className="px-6 py-4 border-b border-gray-100 space-y-3 shrink-0">
          {/* Search input */}
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search entities by name or ID..."
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition"
          />

          {/* Filters row */}
          <div className="flex flex-wrap gap-3">
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Domains</option>
              {domains.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>

            <select
              value={areaFilter}
              onChange={(e) => setAreaFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Areas</option>
              {areas.map((a) => (
                <option key={a} value={a}>{a === 'all' ? 'All Areas' : a}</option>
              ))}
            </select>

            <button
              onClick={fetchEntities}
              className="px-3 py-2 text-sm font-medium text-blue-600 border border-gray-300 rounded-lg hover:bg-blue-50 transition"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="overflow-y-auto flex-1 p-4 space-y-2">
          {loading ? (
            <p className="text-gray-500 text-center py-8">Loading entities...</p>
          ) : filteredEntities.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              {searchQuery ? 'No matching entities found' : 'No entities available. Connect to HA and discover entities first.'}
            </p>
          ) : (
            filteredEntities.map((entity) => (
              <EntityRow key={entity.entity_id} entity={entity} onSelect={onSelect} />
            ))
          )}
        </div>

        {/* Footer with count */}
        <div className="px-6 py-3 border-t border-gray-100 text-sm text-gray-500 shrink-0">
          {filteredEntities.length} entity{filteredEntities.length !== 1 ? 'ies' : 'y'} found
        </div>
      </div>
    </div>
  )
}

function EntityRow({ entity, onSelect }: { entity: CachedEntity; onSelect: (entityId: string, cardType: string) => void }) {
  const showActions = false

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition group">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium truncate">{entity.name}</p>
        <p className="text-xs text-gray-500 truncate">
          {entity.entity_id}
          {entity.area && <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">{entity.area}</span>}
        </p>
      </div>

      {/* State badge */}
      <span className={`text-xs font-medium px-2 py-1 rounded-full ml-3 shrink-0 ${
        entity.state === 'on' || entity.state === 'home' || entity.state === 'open' ? 'bg-green-100 text-green-700' :
        entity.state === 'off' || entity.state === 'away' || entity.state === 'closed' ? 'bg-gray-200 text-gray-600' :
        'bg-yellow-100 text-yellow-700'
      }`}>
        {entity.state}
      </span>

      {/* Action buttons */}
      <div className={`flex gap-1 ml-3 ${showActions ? '' : 'opacity-0 group-hover:opacity-100'} transition-opacity`}>
        <button
          onClick={() => onSelect(entity.entity_id, 'switch')}
          className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
          title="Add as switch widget"
        >
          Switch
        </button>
        <button
          onClick={() => onSelect(entity.entity_id, 'light')}
          className="px-2 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700"
          title="Add as light widget"
        >
          Light
        </button>
      </div>
    </div>
  )
}

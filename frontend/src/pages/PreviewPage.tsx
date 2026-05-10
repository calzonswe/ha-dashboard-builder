import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { DashboardConfig, DashboardCard } from '../types/api'
import { getDashboard, getEntities } from '../services/api'

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

const PreviewCard: React.FC<{ card: DashboardCard; entityState?: string }> = ({ card, entityState }) => {
  const domain = card.entity_id?.split('.')[0] || ''
  const colors = DOMAIN_COLORS[domain] || { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-700' }

  const isUnavailable = !entityState || entityState === 'unavailable' || entityState === 'unknown'
  const isOff = entityState === 'off'

  return (
    <div
      className={`rounded-lg border-2 ${colors.border} ${colors.bg} shadow-md p-4 min-h-[100px] ${
        isUnavailable ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-sm truncate">
          {card.config?.title || card.entity_id?.split('.').slice(1).join('.') || 'Untitled'}
        </h3>
        {isUnavailable && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 text-gray-500">Unavailable</span>
        )}
        {isOff && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 text-gray-500">Off</span>
        )}
      </div>
      <div className={`text-xl font-semibold ${colors.text}`}>
        {entityState !== undefined ? entityState : '—'}
      </div>
      {card.entity_id && (
        <p className="text-xs text-gray-500 mt-1 truncate">{card.entity_id}</p>
      )}
    </div>
  )
}

const PreviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [dashboard, setDashboard] = useState<DashboardConfig | null>(null)
  const [cards, setCards] = useState<DashboardCard[]>([])
  const [entityStates, setEntityStates] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      if (!id) return
      setLoading(true)
      try {
        const [dashData, entityData] = await Promise.all([
          getDashboard(id),
          getEntities(),
        ])
        setDashboard(dashData)
        setCards(dashData.cards || [])

        const stateMap: Record<string, string> = {}
        for (const entity of entityData || []) {
          stateMap[entity.entity_id] = entity.state
        }
        setEntityStates(stateMap)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error || !dashboard) {
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center gap-4">
        <p className="text-gray-500">{error || 'Dashboard not found'}</p>
        <Link to="/" className="text-blue-500 hover:underline">← Back to dashboards</Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4 flex items-center gap-4">
        <Link to={`/dashboard/${id}`} className="text-gray-500 hover:text-gray-700" title="Back to editor">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M17 10a1 1 0 01-1 1H5.414l4.293 4.293a1 1 0 01-1.414 1.414l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 9H16a1 1 0 011 1z" clipRule="evenodd" />
          </svg>
        </Link>
        <div>
          <h1 className="text-lg font-semibold text-gray-900">{dashboard.name}</h1>
          {dashboard.description && (
            <p className="text-sm text-gray-500">{dashboard.description}</p>
          )}
        </div>
        <span className="ml-auto text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
          Preview Mode
        </span>
      </div>

      {/* Card grid */}
      <div className="p-6">
        {cards.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No cards in this dashboard.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {cards.map((card) => (
              <PreviewCard
                key={card.id}
                card={card}
                entityState={entityStates[card.entity_id || '']}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default PreviewPage
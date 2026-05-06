import React, { useState, useCallback, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { HAEntity, DashboardCard, CardConfig } from '../types/api'
import { getDashboard, updateDashboard, getEntities, getStateById } from '../services/api'
import DashboardHeader from '../components/DashboardHeader'
import EntitySidebar from '../components/EntitySidebar'
import DashboardCanvas from '../components/DashboardCanvas'
import CardConfigModal from '../components/CardConfigModal'

const DashboardView: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  // State management
  const [dashboard, setDashboard] = useState<any>(null)
  const [cards, setCards] = useState<DashboardCard[]>([])
  const [entities, setEntities] = useState<HAEntity[]>([])
  const [entityStates, setEntityStates] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [configModalOpen, setConfigModalOpen] = useState(false)
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null)

  // ─── Load dashboard and entities on mount ────────────────────────

  useEffect(() => {
    async function loadData() {
      if (!id) return
      setLoading(true)
      try {
        const [dash, ents] = await Promise.all([getDashboard(id), getEntities()])
        setDashboard(dash)
        setCards(dash.cards || [])
        setEntities(ents)

        // Fetch states for each card's entity
        const states: Record<string, string> = {}
        for (const card of dash.cards || []) {
          try {
            const stateData = await getStateById(card.entity_id)
            states[card.entity_id] = stateData.state
          } catch {
            // Entity may not have a current state; skip gracefully
          }
        }
        setEntityStates(states)
      } catch (err) {
        console.error('Failed to load dashboard:', err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [id])

  // ─── Save handler ────────────────────────────────────────────────

  const handleSave = useCallback(async () => {
    if (!dashboard || !id) return
    setSaving(true)
    try {
      await updateDashboard(id, { cards })
      setDashboard((prev: any) => ({ ...prev, cards }))
    } catch (err) {
      console.error('Failed to save dashboard:', err)
    } finally {
      setSaving(false)
    }
  }, [dashboard, id, cards])

  // ─── Preview handler ─────────────────────────────────────────────

  const handlePreview = useCallback(() => {
    if (!id) return
    window.open(`/preview/${id}`, '_blank')
  }, [id])

  // ─── Card management ─────────────────────────────────────────────

  const handleCardsChange = useCallback((newCards: DashboardCard[]) => {
    setCards(newCards)
  }, [])

  const handleConfigureCard = useCallback(
    (cardId: string) => {
      setSelectedCardId(cardId)
      setConfigModalOpen(true)
    },
    [],
  )

  const handleSaveCardConfig = useCallback(
    (_cardId: string, config: Partial<CardConfig>) => {
      setCards((prev) =>
        prev.map((c) => ({ ...c, config: { ...(c.config || {}), ...config } as CardConfig })),
      )
    },
    [],
  )

  // ─── Render ──────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <DashboardHeader
        dashboard={dashboard}
        loading={loading || saving}
        onSave={handleSave}
        onPreview={handlePreview}
      />

      {/* Main content: sidebar + canvas */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      ) : (
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <EntitySidebar entities={entities} />

          {/* Canvas area */}
          <main className="flex-1 p-4 overflow-auto bg-gray-50">
            <DashboardCanvas
              cards={cards}
              entityStates={entityStates}
              onCardsChange={handleCardsChange}
              onConfigureCard={handleConfigureCard}
            />
          </main>
        </div>
      )}

      {/* Config modal */}
      <CardConfigModal
        isOpen={configModalOpen}
        onClose={() => setConfigModalOpen(false)}
        card={cards.find((c) => c.id === selectedCardId) || null}
        entities={entities}
        onSave={handleSaveCardConfig}
      />
    </div>
  )
}

export default DashboardView

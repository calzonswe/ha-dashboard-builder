import { useState, useEffect, useCallback } from 'react'
import { DashboardConfig, DashboardCard, CardConfig } from '../types/api'
import {
  getDashboard as apiGetDashboard,
  updateDashboardCards,
} from '../services/api'

interface UseDashboardResult {
  dashboard: DashboardConfig | null
  cards: DashboardCard[]
  loading: boolean
  saving: boolean
  error: Error | null
  saveCards: (newCards: DashboardCard[]) => Promise<void>
  addCard: (card: Omit<DashboardCard, 'id'>) => void
  removeCard: (cardId: string) => void
  updateCardConfig: (cardId: string, config: Partial<CardConfig>) => void
}

/**
 * Hook that manages dashboard lifecycle and state.
 * Fetches dashboard config from API on mount, handles save operations.
 */
export function useDashboard(dashboardId: string): UseDashboardResult {
  const [dashboard, setDashboard] = useState<DashboardConfig | null>(null)
  const [cards, setCards] = useState<DashboardCard[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  /** Load dashboard config from API */
  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiGetDashboard(dashboardId)
      setDashboard(data)
      setCards(data.cards || [])
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setLoading(false)
    }
  }, [dashboardId])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  /** Save current cards to the server via bulk card update endpoint */
  const saveCards = useCallback(
    async (newCards: DashboardCard[]) => {
      setSaving(true)
      setError(null)
      try {
        // Map frontend DashboardCard[] → backend CardPayload[]
        const payload = newCards.map((c) => ({
          id: c.id.startsWith('card-') ? null : parseInt(c.id, 10),
          card_type: c.config?.type || 'state',
          entity_id: c.entity_id || undefined,
          title: c.config?.title || undefined,
          config: { ...c.config } as Record<string, unknown>,
          x: c.x,
          y: c.y,
          width: c.width,
          height: c.height,
        }))

        const result = await updateDashboardCards(dashboardId, payload)

        // Merge server-assigned IDs back into local state
        setCards((prev) => {
          const updated = prev.map((c) => {
            const serverCard = result.cards.find(
              (sc) => sc.id === c.id || sc.id === parseInt(c.id, 10),
            )
            return serverCard ? { ...c, id: String(serverCard.id) } : c
          })
          // Add newly created cards that don't exist locally yet
          const localIds = new Set(updated.map((u) => u.id))
          result.cards.forEach((sc) => {
            if (!localIds.has(String(sc.id))) {
              updated.push({
                id: String(sc.id),
                entity_id: '',
                x: 0,
                y: 0,
                width: 1,
                height: 1,
              } as DashboardCard)
            }
          })
          return updated
        })
        setDashboard((prev) => (prev ? { ...prev, cards: newCards } : null))
      } catch (err) {
        const errObj = err instanceof Error ? err : new Error(String(err))
        setError(errObj)
        throw errObj
      } finally {
        setSaving(false)
      }
    },
    [dashboardId],
  )

  /** Add a card to the dashboard (optimistic update, no server call yet) */
  const addCard = useCallback(
    (card: Omit<DashboardCard, 'id'>) => {
      const newCard: DashboardCard = { ...card, id: `card-${Date.now()}` }
      setCards((prev) => [...prev, newCard])
    },
    [],
  )

  /** Remove a card from the dashboard */
  const removeCard = useCallback(
    (cardId: string) => {
      setCards((prev) => prev.filter((c) => c.id !== cardId))
    },
    [],
  )

  /** Update configuration for an existing card */
  const updateCardConfig = useCallback(
    (cardId: string, config: Partial<CardConfig>) => {
      setCards((prev) =>
        prev.map((c) =>
          c.id === cardId ? { ...c, config: { ...(c.config || {}), ...config } as CardConfig } : c,
        ),
      )
    },
    [],
  )

  return {
    dashboard,
    cards,
    loading,
    saving,
    error,
    saveCards,
    addCard,
    removeCard,
    updateCardConfig,
  }
}

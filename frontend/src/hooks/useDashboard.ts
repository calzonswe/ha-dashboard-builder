import { useState, useEffect, useCallback } from 'react'
import { DashboardConfig, DashboardCard, CardConfig } from '../types/api'
import { getDashboard, updateDashboard } from '../services/api'

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
      const data = await getDashboard(dashboardId)
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

  /** Save current cards to the server */
  const saveCards = useCallback(
    async (newCards: DashboardCard[]) => {
      setSaving(true)
      setError(null)
      try {
        await updateDashboard(dashboardId, { cards: newCards })
        setCards(newCards)
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

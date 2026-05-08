import React, { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { HAEntity, DashboardCard, CardConfig, DashboardConfig } from '../types/api'
import { useDashboard } from '../hooks/useDashboard'
import { useEntityStates } from '../hooks/useEntityStates'
import { useEntities } from '../hooks/useEntities'
import { getHAStatus } from '../services/api'
import ResponsiveLayout from '../components/ResponsiveLayout'
import MobileSidebar from '../components/MobileSidebar'
import DashboardHeader from '../components/DashboardHeader'
import EntitySidebar from '../components/EntitySidebar'
import DashboardCanvas from '../components/DashboardCanvas'
import CardConfigModal from '../components/CardConfigModal'
import ExportModal from '../components/ExportModal'
import ImportModal from '../components/ImportModal'
import SettingsModal from '../components/SettingsModal'

const DashboardView: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const dashboardId = id || ''

  // Dashboard state management hook
  const {
    dashboard,
    cards,
    loading: dashboardLoading,
    saving,
    error: dashboardError,
    saveCards,
    updateCardConfig,
  } = useDashboard(dashboardId)

  // Real-time entity states via SSE
  const { entities: liveStates } = useEntityStates()

  // Entity list for sidebar (available entities from Home Assistant)
  const { entities: availableEntities, loading: entitiesLoading } = useEntities()

  // Local UI state
  const [configModalOpen, setConfigModalOpen] = useState(false)
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<Error | null>(null)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [haConnected, setHaConnected] = useState(true)

  // Check HA connection on mount
  React.useEffect(() => {
    getHAStatus().then((status) => setHaConnected(status.connected)).catch(() => {})
  }, [])

  // Export/Import modal state
  const [exportModalOpen, setExportModalOpen] = useState(false)
  const [importModalOpen, setImportModalOpen] = useState(false)

  // Settings modal state
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)

  // ─── Save handler ────────────────────────────────────────────────

  const handleSave = useCallback(async () => {
    if (!dashboard || !dashboardId) return
    setSaveError(null)
    try {
      await saveCards(cards)
    } catch (err) {
      setSaveError(err instanceof Error ? err : new Error(String(err)))
    }
  }, [dashboard, dashboardId, cards, saveCards])

  // ─── Preview handler ─────────────────────────────────────────────

  const handlePreview = useCallback(() => {
    if (!id) return
    window.open(`/preview/${id}`, '_blank')
  }, [id])

  // ─── Export/Import handlers ──────────────────────────────────────

  const handleExport = useCallback(() => {
    setExportModalOpen(true)
  }, [])

  const handleImport = useCallback(() => {
    setImportModalOpen(true)
  }, [])

  const handleConfirmImport = useCallback(
    (importedDashboard: DashboardConfig) => {
      // Create a new dashboard from the imported config
      // The backend will assign an ID when saved
      const newDashboard: DashboardConfig = {
        ...importedDashboard,
        id: undefined,
      }

      // Save cards to the server (creates a new dashboard)
      if (newDashboard.cards.length > 0) {
        saveCards(newDashboard.cards).then(() => {
          // The hook will refetch and update dashboard state automatically
        })
      }

      setImportModalOpen(false)
    },
    [saveCards],
  )

  // ─── Card management ─────────────────────────────────────────────

  const handleCardsChange = useCallback(
    (newCards: DashboardCard[]) => {
      saveCards(newCards).catch(() => {
        // Error is already handled in the hook; just refresh UI state
      })
    },
    [saveCards],
  )

  const handleConfigureCard = useCallback(
    (cardId: string) => {
      setSelectedCardId(cardId)
      setConfigModalOpen(true)
    },
    [],
  )

  const handleSaveCardConfig = useCallback(
    (_cardId: string, config: Partial<CardConfig>) => {
      updateCardConfig(_cardId, config)
    },
    [updateCardConfig],
  )

  // ─── Build entity states map for canvas (merge live SSE + initial fetch) ──

  const entityStatesMap = React.useMemo(() => {
    const map: Record<string, string> = {}
    for (const card of cards) {
      const state = liveStates[card.entity_id]
      if (state && 'state' in state) {
        map[card.entity_id] = String(state.state)
      } else {
        // Fallback: try to find from available entities list
        const found = availableEntities.find((e: HAEntity) => e.entity_id === card.entity_id)
        if (found) {
          map[card.entity_id] = found.state
        }
      }
    }
    return map
  }, [cards, liveStates, availableEntities])

  // ─── Loading / error states ──────────────────────────────────────

  const isLoading = dashboardLoading || entitiesLoading
  const hasError = dashboardError || saveError

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (!dashboard) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[200px] gap-4">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-gray-300" viewBox="0 0 20 20" fill="currentColor">
          <path d="M5.5 16a3.5 3.5 0 110-7 3.5 3.5 0 010 7zM15 16a3.5 3.5 0 110-7 3.5 3.5 0 010 7z" />
        </svg>
        <p className="text-gray-500">Dashboard not found</p>
      </div>
    )
  }

  return (
    <ResponsiveLayout>
      <div className="flex flex-col h-screen">
        {/* Header */}
        <DashboardHeader
          dashboard={dashboard}
          loading={saving || isLoading}
          onSave={handleSave}
          onPreview={handlePreview}
          onExport={handleExport}
          onImport={handleImport}
          onSettings={() => setSettingsModalOpen(true)}
        />

        {/* Error banner */}
        {hasError && (
          <div className="mx-4 mt-2 bg-red-50 border border-red-300 rounded-md p-3 text-sm text-red-700">
            {saveError ? `Save failed: ${saveError.message}` : dashboardError?.message}
          </div>
        )}

        {/* Connection warning */}
        {!haConnected && (
          <div className="mx-4 mt-2 bg-yellow-50 border border-yellow-200 rounded-md p-3 flex items-start gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path d="M8.488 11.75a1.25 1.25 0 00-2.5 0v3.5a1.25 1.25 0 002.5 0v-3.5zM9.376 7.874a.75.75 0 011.248 0l.833 1.667a.75.75 0 001.248 0l.833-1.667a.75.75 0 011.248 0l-.833 1.667a.75.75 0 000 1.248l1.667.833a.75.75 0 010 1.248l-1.667.833a.75.75 0 000 1.248l.833 1.667a.75.75 0 01-1.248 0L9.5 11.75H8.5a.75.75 0 010-1.5h1L9.376 7.874z" />
            </svg>
            <div className="text-sm text-yellow-800">
              <p className="font-medium">Home Assistant not connected</p>
              <p className="mt-0.5">
                Go to{' '}
                <a href="/connect" className="underline hover:text-yellow-900">
                  /connect
                </a>{' '}
                to configure your connection.
              </p>
            </div>
          </div>
        )}

        {/* Main content: sidebar + canvas */}
        <div className="flex flex-1 overflow-hidden">
          {/* Desktop/tablet sidebar (hidden on mobile) */}
          <aside className="hidden sm:block w-72 flex-shrink-0">
            <EntitySidebar entities={availableEntities} />
          </aside>

          {/* Canvas area - full width on mobile, flexible on desktop */}
          <main className="flex-1 p-4 overflow-auto bg-gray-50 min-w-0">
            <DashboardCanvas
              cards={cards}
              entityStates={entityStatesMap}
              onCardsChange={handleCardsChange}
              onConfigureCard={handleConfigureCard}
            />
          </main>
        </div>

        {/* Mobile sidebar bottom drawer (visible only on mobile) */}
        <MobileSidebar 
          isOpen={isMobileSidebarOpen} 
          onClose={() => setIsMobileSidebarOpen(false)}
          entities={availableEntities}
        />

        {/* Config modal */}
        <CardConfigModal
          key={selectedCardId || 'new'}
          isOpen={configModalOpen}
          onClose={() => setConfigModalOpen(false)}
          card={cards.find((c) => c.id === selectedCardId) || null}
          entities={availableEntities}
          onSave={handleSaveCardConfig}
        />

        {/* Export modal */}
        <ExportModal
          isOpen={exportModalOpen}
          onClose={() => setExportModalOpen(false)}
          dashboard={dashboard}
        />

        {/* Import modal */}
        <ImportModal
          isOpen={importModalOpen}
          onClose={() => setImportModalOpen(false)}
          onImport={handleConfirmImport}
        />

        {/* Settings modal */}
        <SettingsModal
          isOpen={settingsModalOpen}
          onClose={() => setSettingsModalOpen(false)}
        />
      </div>
    </ResponsiveLayout>
  )
}

export default DashboardView

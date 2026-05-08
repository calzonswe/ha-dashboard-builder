import React, { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { DashboardConfig } from '../types/api'

interface DashboardHeaderProps {
  dashboard: DashboardConfig | null
  loading: boolean
  onSave: () => void
  onPreview: () => void
  onExport?: () => void
  onImport?: () => void
  onSettings?: () => void
}

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

const DOMAIN_ICONS_MDI: Record<string, string> = {
  light: 'lightbulb',
  sensor: 'sensor',
  switch: 'toggle-switch',
  cover: 'window-shade',
  fan: 'fan',
  climate: 'thermostat',
  media_player: 'music-note',
  camera: 'camera',
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  dashboard,
  loading,
  onSave,
  onPreview,
  onExport,
  onImport,
  onSettings,
}) => {
  const navigate = useNavigate()
  const [title, setTitle] = React.useState(dashboard?.name || '')
  const [isEditing, setIsEditing] = React.useState(false)
  const [showExportMenu, setShowExportMenu] = React.useState(false)
  const menuRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (dashboard && dashboard.name !== title) {
      setTitle(dashboard.name)
    }
  }, [dashboard])

  // Close export menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleTitleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setTitle(e.target.value)
    },
    [],
  )

  const handleTitleBlur = useCallback(() => {
    setIsEditing(false)
  }, [])

  const handleTitleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.currentTarget.blur()
      }
    },
    [],
  )

  const handleSave = useCallback(() => {
    onSave()
  }, [onSave])

  const handlePreview = useCallback(() => {
    onPreview()
  }, [onPreview])

  const handleBack = useCallback(() => {
    navigate('/')
  }, [navigate])

  // Collect entity domains for the info badge
  const domainCounts: Record<string, number> = {}
  if (dashboard?.cards) {
    for (const card of dashboard.cards) {
      const parts = (card.entity_id || '').split('.')
      const domain = parts[0] || 'unknown'
      domainCounts[domain] = (domainCounts[domain] || 0) + 1
    }
  }

  // Pick the most common domain for icon
  let bestDomain = 'home'
  let bestCount = 0
  for (const [domain, count] of Object.entries(domainCounts)) {
    if (count > bestCount) {
      bestCount = count
      bestDomain = domain
    }
  }

  const handleExportClick = useCallback(() => {
    setShowExportMenu(false)
    onExport?.()
  }, [onExport])

  const handleImportClick = useCallback(() => {
    setShowExportMenu(false)
    onImport?.()
  }, [onImport])

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-full mx-auto px-3 sm:px-4 lg:px-6">
        {/* Mobile compact header */}
        <div className="flex items-center justify-between h-14 gap-2 sm:hidden">
          {/* Back button */}
          <button
            onClick={handleBack}
            className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="Go back"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M9.707 16.707a1 1 0 01-1.414 0L6 13.293V5a1 1 0 011.707-.707l2 2v1.586l1.293-1.293a1 1 0 011.414 1.414L9.707 16.707z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {/* Title - centered on mobile */}
          {isEditing ? (
            <input
              type="text"
              value={title}
              onChange={handleTitleChange}
              onBlur={handleTitleBlur}
              onKeyDown={handleTitleKeyDown}
              autoFocus
              className="text-base font-semibold text-gray-900 border-b-2 border-blue-400 outline-none bg-transparent flex-1 max-w-[200px] truncate"
            />
          ) : (
            <h1
              onClick={() => setIsEditing(true)}
              className="text-base font-semibold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors truncate flex items-center gap-1.5 justify-center flex-1 py-1"
              title="Click to edit title"
            >
              <span className="flex-shrink-0">{DOMAIN_ICONS[bestDomain] || '🏠'}</span>
              <span className="truncate">{loading ? 'Loading...' : dashboard?.name || 'Untitled Dashboard'}</span>
            </h1>
          )}

          {/* Mobile action buttons - compact */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {/* Card count badge */}
            {dashboard?.cards && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full sm:hidden">
                {dashboard.cards.length} cards
              </span>
            )}

            {/* Export/Import dropdown */}
            {onExport && onImport && (
              <div ref={menuRef} className="relative">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  disabled={!dashboard || dashboard.cards.length === 0}
                  className="p-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Export/Import menu"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.293a1 1 0 011.414 0L9 10.586V7a1 1 0 112 0v3.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" />
                  </svg>
                </button>

                {/* Dropdown menu */}
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-1 z-50">
                    <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Export</div>
                    <button onClick={handleExportClick} className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2">
                      📄 Export JSON
                    </button>
                    <button onClick={handleExportClick} className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2">
                      📝 Export YAML
                    </button>
                    <div className="border-t border-gray-200 my-1" />
                    <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Import</div>
                    <button onClick={handleImportClick} className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2">
                      📥 Import from HA
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Preview button */}
            <button
              onClick={handlePreview}
              disabled={!dashboard || dashboard.cards.length === 0}
              className="p-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Preview dashboard"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path fillRule="evenodd" d="M.458 10C1.135 6.39 4.07 4 7.5 4c1.43 0 2.865.39 4.07 1C12.93 4.39 15.865 6.79 16.543 10c-.678 3.21-3.613 5.61-7.043 6-1.205.16-2.43-.04-3.543-.59C3.135 15.61 1.2 13.21.458 10zM7.5 2C3.62 2 .72 4.81.11 8.28a1.968 1.968 0 000 .44C.72 12.19 3.62 15 7.5 15c1.46 0 2.82-.29 4.07-.83a1.97 1.97 0 00.93-.17C12.93 15.61 15.865 13.21 16.543 10c-.678-3.21-3.613-5.61-7.043-6C12.93 3.39 10.065 2 7.5 2z" clipRule="evenodd" />
              </svg>
            </button>

            {/* Save button */}
            <button
              onClick={handleSave}
              disabled={!dashboard || loading}
              className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '...' : 'Save'}
            </button>
          </div>
        </div>

        {/* Desktop/tablet full header */}
        <div className="hidden sm:flex items-center justify-between h-16 gap-4">
          {/* Back button */}
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M9.707 16.707a1 1 0 01-1.414 0L6 13.293V5a1 1 0 011.707-.707l2 2v1.586l1.293-1.293a1 1 0 011.414 1.414L9.707 16.707z"
                clipRule="evenodd"
              />
            </svg>
            <span className="hidden sm:inline">Back</span>
          </button>

          {/* Title */}
          {isEditing ? (
            <input
              type="text"
              value={title}
              onChange={handleTitleChange}
              onBlur={handleTitleBlur}
              onKeyDown={handleTitleKeyDown}
              autoFocus
              className="text-xl font-semibold text-gray-900 border-b-2 border-blue-400 outline-none bg-transparent w-full max-w-md"
            />
          ) : (
            <h1
              onClick={() => setIsEditing(true)}
              className="text-xl font-semibold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors truncate flex items-center gap-2"
              title="Click to edit title"
            >
              {DOMAIN_ICONS[bestDomain] || '🏠'}{' '}
              {loading ? 'Loading...' : dashboard?.name || 'Untitled Dashboard'}
            </h1>
          )}

          {/* Entity count + domain info */}
          <div className="hidden md:flex items-center gap-2">
            <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              {dashboard?.cards?.length || 0} card{dashboard?.cards?.length !== 1 ? 's' : ''}
            </span>
            {Object.keys(domainCounts).length > 0 && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                {Object.entries(domainCounts)
                  .slice(0, 3)
                  .map(([domain]) => (
                    <span key={domain} title={`${domain}: ${domainCounts[domain]} card(s)`}>
                      {DOMAIN_ICONS_MDI[domain] ? `🏷️${domain}` : domain}
                    </span>
                  ))}
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {/* Export dropdown */}
            {onExport && onImport && (
              <div ref={menuRef} className="relative">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  disabled={!dashboard || dashboard.cards.length === 0}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.293a1 1 0 011.414 0L9 10.586V7a1 1 0 112 0v3.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" />
                  </svg>
                  Export / Import
                  <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${showExportMenu ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>

                {/* Dropdown menu */}
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-1 z-50">
                    <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Export</div>
                    <button onClick={handleExportClick} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2">
                      📄 Export JSON
                    </button>
                    <button onClick={handleExportClick} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2">
                      📝 Export YAML
                    </button>
                    <div className="border-t border-gray-200 my-1" />
                    <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Import</div>
                    <button onClick={handleImportClick} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2">
                      📥 Import from HA
                    </button>
                  </div>
                )}
              </div>
            )}

            <button
              onClick={handlePreview}
              disabled={!dashboard || dashboard.cards.length === 0}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Preview
            </button>
            <button
              onClick={handleSave}
              disabled={!dashboard || loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : 'Save'}
            </button>
            {onSettings && (
              <button
                onClick={onSettings}
                className="p-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                title="Settings"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader

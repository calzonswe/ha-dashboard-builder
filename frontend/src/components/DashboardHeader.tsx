import React, { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { DashboardConfig } from '../types/api'

interface DashboardHeaderProps {
  dashboard: DashboardConfig | null
  loading: boolean
  onSave: () => void
  onPreview: () => void
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

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  dashboard,
  loading,
  onSave,
  onPreview,
}) => {
  const navigate = useNavigate()
  const [title, setTitle] = React.useState(dashboard?.title || '')
  const [isEditing, setIsEditing] = React.useState(false)

  React.useEffect(() => {
    if (dashboard && dashboard.title !== title) {
      setTitle(dashboard.title)
    }
  }, [dashboard])

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

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
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
              {DOMAIN_ICONS[dashboard?.cards?.[0]?.entity_id?.split('.')?.[0] || ''] || '🏠'}{' '}
              {loading ? 'Loading...' : dashboard?.title || 'Untitled Dashboard'}
            </h1>
          )}

          {/* Entity count */}
          <span className="hidden md:inline text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {dashboard?.cards?.length || 0} card{dashboard?.cards?.length !== 1 ? 's' : ''}
          </span>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
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
          </div>
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader

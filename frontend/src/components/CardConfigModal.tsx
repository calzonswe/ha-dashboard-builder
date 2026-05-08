import React, { useState, useEffect } from 'react'
import { HAEntity, CardConfig, DashboardCard } from '../types/api'

interface CardConfigModalProps {
  isOpen: boolean
  onClose: () => void
  card: DashboardCard | null
  entities: HAEntity[]
  onSave: (cardId: string, config: Partial<CardConfig>) => void
}

const CARD_TYPES: Array<{ value: CardConfig['type']; label: string; icon: string }> = [
  // Core Lovelace card types
  { value: 'entities', label: 'Entities List', icon: '📋' },
  { value: 'entity', label: 'Single Entity', icon: '🎯' },
  { value: 'glance', label: 'Glance Grid', icon: '👁️' },
  { value: 'thermostat', label: 'Thermostat', icon: '🌡️' },
  { value: 'gauge', label: 'Gauge', icon: '📊' },
  { value: 'picture-entity', label: 'Picture Entity', icon: '🖼️' },
  { value: 'button', label: 'Button', icon: '🔘' },
  { value: 'markdown', label: 'Markdown', icon: '📝' },
  { value: 'camera', label: 'Camera', icon: '📷' },
  { value: 'history', label: 'History Graph', icon: '📈' },
  { value: 'logbook', label: 'Logbook', icon: '📖' },
  // Layout cards
  { value: 'grid', label: 'Grid', icon: '⊞' },
  { value: 'vertical-stack', label: 'Vertical Stack', icon: '⬇️' },
  { value: 'horizontal-stack', label: 'Horizontal Stack', icon: '➡️' },
  // Legacy/custom types (kept for backwards compatibility)
  { value: 'state', label: 'State Display', icon: '💡' },
  { value: 'light', label: 'Light Control', icon: '☀️' },
  { value: 'switch', label: 'Switch Control', icon: '🔌' },
  { value: 'climate', label: 'Climate', icon: '❄️' },
  { value: 'sensor', label: 'Sensor', icon: '📡' },
]

const THEME_OPTIONS: Array<{ value: CardConfig['theme']; label: string }> = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
]

const COLOR_PRESETS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4']

const CardConfigModal: React.FC<CardConfigModalProps> = ({
  isOpen,
  onClose,
  card,
  entities,
  onSave,
}) => {
  const [title, setTitle] = useState('')
  const [cardType, setCardType] = useState<CardConfig['type']>('state')
  const [theme, setTheme] = useState<CardConfig['theme']>('light')
  const [accentColor, setAccentColor] = useState('#3B82F6')

  useEffect(() => {
    if (card) {
      setTitle(card.config?.title || '')
      setCardType(card.config?.type || 'state')
      setTheme(card.config?.theme || 'light')
      setAccentColor(card.config?.accentColor || '#3B82F6')
    }
  }, [card])

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  const handleSave = () => {
    if (!card) return
    onSave(card.id, {
      title: title.trim() || undefined,
      type: cardType,
      theme,
      accentColor,
    })
    onClose()
  }

  const handleClose = () => {
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Configure Card</h2>
          <button onClick={handleClose} className="p-1 rounded-md hover:bg-gray-100 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* Entity info */}
          {card && (
            <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <p className="text-sm text-gray-600 font-mono">{card.entity_id}</p>
            </div>
          )}

          {/* Entity selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Entity</label>
            <select
              value={card?.entity_id || ''}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            >
              {entities.map((e) => (
                <option key={e.entity_id} value={e.entity_id}>
                  {e.object_id} ({e.entity_id})
                </option>
              ))}
            </select>
          </div>

          {/* Card type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Card Type</label>
            <div className="grid grid-cols-3 gap-2">
              {CARD_TYPES.map((ct) => (
                <button
                  key={ct.value}
                  onClick={() => setCardType(ct.value)}
                  className={`flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition-all ${
                    cardType === ct.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  <span className="text-xl">{ct.icon}</span>
                  <span className="text-xs font-medium">{ct.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Title override */}
          <div>
            <label htmlFor="card-title" className="block text-sm font-medium text-gray-700 mb-1">
              Custom Title (optional)
            </label>
            <input
              id="card-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter custom title..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>

          {/* Theme */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
            <div className="flex gap-3">
              {THEME_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setTheme(opt.value)}
                  className={`px-4 py-2 rounded-md border-2 text-sm font-medium transition-all ${
                    theme === opt.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Accent color */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Accent Color</label>
            <div className="flex flex-wrap gap-2">
              {COLOR_PRESETS.map((color) => (
                <button
                  key={color}
                  onClick={() => setAccentColor(color)}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${
                    accentColor === color ? 'border-gray-900 scale-110' : 'border-transparent hover:border-gray-300'
                  }`}
                  style={{ backgroundColor: color }}
                  title={color}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
}

export default CardConfigModal

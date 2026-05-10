import { useState, useEffect } from 'react'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

type Tab = 'ha' | 'llm' | 'editor' | 'export'

interface SettingsData {
  ha_host: string
  ha_port: string
  ha_token: string
  llm_provider: string
  llm_model: string
  llm_base_url: string
  editor_theme: string
  editor_grid_size: string
  editor_snap_to_grid: string
  export_format: string
  export_include_unused: string
}

const DEFAULT_SETTINGS: SettingsData = {
  ha_host: 'localhost',
  ha_port: '8123',
  ha_token: '',
  llm_provider: 'ollama',
  llm_model: 'llama3.2',
  llm_base_url: 'http://localhost:11434',
  editor_theme: 'light',
  editor_grid_size: '12',
  editor_snap_to_grid: 'true',
  export_format: 'yaml',
  export_include_unused: 'false',
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('ha')
  const [settings, setSettings] = useState<SettingsData>(DEFAULT_SETTINGS)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      fetchSettings()
    }
  }, [isOpen])

  const fetchSettings = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token') || ''
      const res = await fetch('/api/settings', {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        credentials: 'same-origin',
      })
      if (res.ok) {
        const data = await res.json()
        setSettings({ ...DEFAULT_SETTINGS, ha_port: String(data.ha_port || '8123'), ...data })
      }
    } catch (err) {
      console.error('Failed to fetch settings:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const token = localStorage.getItem('auth_token') || ''
      const res = await fetch('/api/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: 'same-origin',
        body: JSON.stringify(settings),
      })
      if (res.ok) {
        setMessage('Settings saved successfully!')
        setTimeout(() => setMessage(null), 3000)
      } else {
        const err = await res.json().catch(() => ({ detail: 'Save failed' }))
        setMessage(err.detail || 'Failed to save settings')
      }
    } catch (err) {
      setMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key: keyof SettingsData, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  if (!isOpen) return null

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'ha', label: 'HA Connection', icon: '🏠' },
    { id: 'llm', label: 'LLM / Chat', icon: '🤖' },
    { id: 'editor', label: 'Editor', icon: '✏️' },
    { id: 'export', label: 'Export', icon: '📤' },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Settings</h2>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-gray-100 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <p className="text-gray-500 text-center py-8">Loading settings...</p>
          ) : (
            <>
              {activeTab === 'ha' && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">Home Assistant Connection</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                    <input
                      type="text"
                      value={settings.ha_host}
                      onChange={(e) => handleChange('ha_host', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                      placeholder="localhost"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                    <input
                      type="text"
                      value={settings.ha_port}
                      onChange={(e) => handleChange('ha_port', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                      placeholder="8123"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
                    <input
                      type="password"
                      value={settings.ha_token}
                      onChange={(e) => handleChange('ha_token', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                      placeholder="Long-lived access token"
                    />
                  </div>
                </div>
              )}

              {activeTab === 'llm' && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">LLM / Chat Settings</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                    <select
                      value={settings.llm_provider}
                      onChange={(e) => handleChange('llm_provider', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                      <option value="ollama">Ollama (localhost:11434)</option>
                      <option value="lmstudio">LM Studio (localhost:1234)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                    <input
                      type="text"
                      value={settings.llm_model}
                      onChange={(e) => handleChange('llm_model', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                      placeholder="llama3.2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                    <input
                      type="text"
                      value={settings.llm_base_url}
                      onChange={(e) => handleChange('llm_base_url', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                      placeholder="http://localhost:11434"
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    The LLM powers the chat assistant in the sidebar. Use the chat to generate dashboard cards.
                  </p>
                </div>
              )}

              {activeTab === 'editor' && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">Editor Settings</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Theme</label>
                    <select
                      value={settings.editor_theme}
                      onChange={(e) => handleChange('editor_theme', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Grid Size</label>
                    <select
                      value={settings.editor_grid_size}
                      onChange={(e) => handleChange('editor_grid_size', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                      <option value="6">6 columns</option>
                      <option value="12">12 columns</option>
                      <option value="24">24 columns</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="snapToGrid"
                      checked={settings.editor_snap_to_grid === 'true'}
                      onChange={(e) => handleChange('editor_snap_to_grid', e.target.checked ? 'true' : 'false')}
                      className="rounded border-gray-300"
                    />
                    <label htmlFor="snapToGrid" className="text-sm text-gray-700">Snap to grid</label>
                  </div>
                </div>
              )}

              {activeTab === 'export' && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">Export Settings</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Default Format</label>
                    <select
                      value={settings.export_format}
                      onChange={(e) => handleChange('export_format', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                      <option value="yaml">YAML</option>
                      <option value="json">JSON</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="includeUnused"
                      checked={settings.export_include_unused === 'true'}
                      onChange={(e) => handleChange('export_include_unused', e.target.checked ? 'true' : 'false')}
                      className="rounded border-gray-300"
                    />
                    <label htmlFor="includeUnused" className="text-sm text-gray-700">Include unused entities in export</label>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          {message && (
            <span className={`text-sm ${message.includes('Failed') ? 'text-red-600' : 'text-green-600'}`}>
              {message}
            </span>
          )}
          {!message && <span />}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
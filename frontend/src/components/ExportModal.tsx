import React, { useState } from 'react'
import { DashboardConfig } from '../types/api'
import { exportToLovelace, exportToLovelaceYaml } from '../utils/lovelaceExporter'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  dashboard: DashboardConfig | null
}

type ExportFormat = 'json' | 'yaml'

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose, dashboard }) => {
  const [format, setFormat] = useState<ExportFormat>('json')
  const [copied, setCopied] = useState(false)

  // Generate the export content
  const content = React.useMemo(() => {
    if (!dashboard) return ''
    return format === 'yaml' ? exportToLovelaceYaml(dashboard) : exportToLovelace(dashboard)
  }, [dashboard, format])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for browsers without clipboard API
      const textarea = document.createElement('textarea')
      textarea.value = content
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownload = () => {
    if (!content) return
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${(dashboard?.title || 'dashboard').replace(/\s+/g, '-').toLowerCase()}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Prevent body scroll when modal is open
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  const handleClose = () => {
    setCopied(false)
    onClose()
  }

  if (!isOpen || !dashboard) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-3xl mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Export Dashboard</h2>
          <button onClick={handleClose} className="p-1 rounded-md hover:bg-gray-100 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* Format selector */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Format:</span>
            <div className="flex rounded-md shadow-sm" role="group">
              <button
                onClick={() => setFormat('json')}
                className={`px-4 py-2 text-sm font-medium rounded-l-lg border transition-all ${
                  format === 'json'
                    ? 'bg-blue-600 text-white border-blue-600 z-10'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                JSON
              </button>
              <button
                onClick={() => setFormat('yaml')}
                className={`px-4 py-2 text-sm font-medium rounded-r-lg border transition-all ${
                  format === 'yaml'
                    ? 'bg-blue-600 text-white border-blue-600 z-10'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                YAML
              </button>
            </div>
          </div>

          {/* Info */}
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <p className="text-sm text-blue-700">
              This exports your dashboard as a Home Assistant Lovelace configuration. Import it in HA via{' '}
              <span className="font-mono bg-blue-100 px-1 rounded">Configuration → Lovelace Dashboards</span>.
            </p>
          </div>

          {/* Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Preview</label>
            <pre className="bg-gray-900 text-green-400 rounded-lg p-4 overflow-auto max-h-[35vh] text-xs leading-relaxed whitespace-pre-wrap break-all font-mono">
              {content}
            </pre>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>{dashboard.cards.length} card{dashboard.cards.length !== 1 ? 's' : ''}</span>
            <span>•</span>
            <span>{format === 'json' ? '~' + (content.length / 1024).toFixed(1) + ' KB JSON' : '~' + (content.length / 1024).toFixed(1) + ' KB YAML'}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCopy}
              disabled={!content}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                copied
                  ? 'bg-green-600 text-white'
                  : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-100'
              }`}
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
            <button
              onClick={handleDownload}
              disabled={!content}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              Download .{format}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExportModal

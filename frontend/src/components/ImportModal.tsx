import React, { useState } from 'react'
import { DashboardConfig } from '../types/api'
import { importFromLovelace } from '../utils/lovelaceImporter'

interface ImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImport: (dashboard: DashboardConfig) => void
}

type ImportMode = 'file' | 'paste'

const ImportModal: React.FC<ImportModalProps> = ({ isOpen, onClose, onImport }) => {
  const [mode, setMode] = useState<ImportMode>('file')
  const [jsonText, setJsonText] = useState('')
  const [importResult, setImportResult] = useState<{ dashboard: DashboardConfig | null; error?: string } | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

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
    setJsonText('')
    setImportResult(null)
    setIsProcessing(false)
    onClose()
  }

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      const text = String(reader.result || '')
      setJsonText(text)
      validateAndPreview(text)
    }
    reader.onerror = () => {
      setImportResult({ dashboard: null, error: 'Failed to read file' })
    }
    reader.readAsText(file)

    // Reset input so same file can be re-selected
    e.target.value = ''
  }

  // Handle paste/textarea change
  const handlePasteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJsonText(e.target.value)
    validateAndPreview(e.target.value)
  }

  // Validate and preview the JSON
  const validateAndPreview = (text: string) => {
    if (!text.trim()) {
      setImportResult(null)
      return
    }

    setIsProcessing(true)
    // Use setTimeout to allow UI to show loading state
    setTimeout(() => {
      const result = importFromLovelace(text)
      setImportResult(result)
      setIsProcessing(false)
    }, 50)
  }

  // Handle import into builder
  const handleConfirmImport = () => {
    if (!importResult?.dashboard) return
    onImport(importResult.dashboard)
    handleClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-3xl mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Import from Home Assistant</h2>
          <button onClick={handleClose} className="p-1 rounded-md hover:bg-gray-100 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* Mode selector */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Import from:</span>
            <div className="flex rounded-md shadow-sm" role="group">
              <button
                onClick={() => setMode('file')}
                className={`px-4 py-2 text-sm font-medium rounded-l-lg border transition-all ${
                  mode === 'file'
                    ? 'bg-blue-600 text-white border-blue-600 z-10'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                📁 File Upload
              </button>
              <button
                onClick={() => setMode('paste')}
                className={`px-4 py-2 text-sm font-medium rounded-r-lg border transition-all ${
                  mode === 'paste'
                    ? 'bg-blue-600 text-white border-blue-600 z-10'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                📋 Paste JSON
              </button>
            </div>
          </div>

          {/* File upload mode */}
          {mode === 'file' && (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                accept=".json,application/json"
                onChange={handleFileUpload}
                className="hidden"
                id="import-file-input"
              />
              <label htmlFor="import-file-input" className="cursor-pointer">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-400 mb-3" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8 5a3 3 0 000 6v7H6a1 1 0 100 2h4a1 1 0 100-2H8V5zm9 1a2 2 0 11-4 0v4a2 2 0 01-4 0V7a4 4 0 118 0v6h-1v-3a1 1 0 10-2 0v3H9.5V8A2.5 2.5 0 007 5.5 2.5 2.5 0 004.5 8v6h-1a1 1 0 100 2h1.5v3a1 1 0 102 0v-3H11v3a1 1 0 102 0v-3H14.5a1 1 0 100-2H16V9z" clipRule="evenodd" />
                </svg>
                <p className="text-gray-600 font-medium">Click to upload a .json file</p>
                <p className="text-sm text-gray-400 mt-1">or drag and drop your Home Assistant dashboard JSON here</p>
              </label>
            </div>
          )}

          {/* Paste mode */}
          {mode === 'paste' && (
            <div>
              <label htmlFor="import-json" className="block text-sm font-medium text-gray-700 mb-2">
                Paste your Home Assistant Lovelace JSON below:
              </label>
              <textarea
                id="import-json"
                value={jsonText}
                onChange={handlePasteChange}
                placeholder='{"title": "My Dashboard", "views": [...]}'
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent resize-y"
              />
            </div>
          )}

          {/* Validation / Preview */}
          {importResult && (
            <div className={`rounded-lg border p-4 ${importResult.error ? 'bg-red-50 border-red-300' : 'bg-green-50 border-green-300'}`}>
              {importResult.error ? (
                <>
                  <p className="text-sm font-medium text-red-700 mb-2">⚠ Import Error</p>
                  <p className="text-sm text-red-600">{importResult.error}</p>
                </>
              ) : importResult.dashboard ? (
                <>
                  <p className="text-sm font-medium text-green-700 mb-2">✓ Valid Lovelace Configuration</p>
                  <div className="space-y-1 text-sm text-green-600">
                    <p><strong>Title:</strong> {importResult.dashboard.name}</p>
                    <p><strong>Cards:</strong> {importResult.dashboard.cards.length} card{importResult.dashboard.cards.length !== 1 ? 's' : ''}</p>
                    {importResult.dashboard.cards.length > 0 && (
                      <>
                        <p className="mt-2 font-medium">Cards preview:</p>
                        <ul className="list-disc list-inside space-y-0.5 mt-1">
                          {importResult.dashboard.cards.slice(0, 10).map((card, i) => (
                            <li key={`${card.id}-${i}`}>
                              <span className="font-mono">{card.entity_id}</span>
                              {' — '}
                              <span className="text-gray-500">{card.config?.type || 'state'}</span>
                            </li>
                          ))}
                          {importResult.dashboard.cards.length > 10 && (
                            <li>+{importResult.dashboard.cards.length - 10} more cards...</li>
                          )}
                        </ul>
                      </>
                    )}
                  </div>
                </>
              ) : null}
            </div>
          )}

          {/* Loading indicator */}
          {isProcessing && (
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />
              Validating...
            </div>
          )}

          {/* Info */}
          <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
            <p className="text-sm text-yellow-700">
              💡 Tip: Export your dashboard from HA via{' '}
              <span className="font-mono bg-yellow-100 px-1 rounded">⋮ → Edit Dashboard → Three-dot menu → Export</span>
            </p>
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
          {importResult?.dashboard ? (
            <button
              onClick={handleConfirmImport}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Dashboard
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export default ImportModal

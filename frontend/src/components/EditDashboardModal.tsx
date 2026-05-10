import { useState } from 'react'
import { useToast } from '../hooks/useToast'

interface EditDashboardModalProps {
  isOpen: boolean
  dashboardId: number | null
  initialName: string
  initialDescription?: string
  onClose: () => void
}

export default function EditDashboardModal({
  isOpen,
  dashboardId,
  initialName,
  initialDescription = '',
  onClose,
}: EditDashboardModalProps) {
  const { addToast } = useToast()
  const [name, setName] = useState(initialName)
  const [description, setDescription] = useState(initialDescription)
  const [loading, setLoading] = useState(false)

  if (!isOpen || dashboardId === null) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      addToast('Dashboard name cannot be empty', 'error')
      return
    }

    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token') || ''
      await fetch(`/api/dashboards/${dashboardId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: 'same-origin',
        body: JSON.stringify({ name: name.trim(), description: description.trim() || null }),
      })
      addToast('Dashboard updated successfully!', 'success')
      onClose()
    } catch {
      addToast('Could not update dashboard. Check your connection.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setName(initialName)
    setDescription(initialDescription)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold">Edit Dashboard</h2>
          <button onClick={handleCancel} className="text-gray-400 hover:text-gray-600 text-xl leading-none" aria-label="Close">
            &times;
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Name field */}
          <div>
            <label htmlFor="dashboard-name" className="block text-sm font-medium text-gray-700 mb-1.5">
              Dashboard Name
            </label>
            <input
              id="dashboard-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Living Room"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition"
              required
            />
          </div>

          {/* Description field */}
          <div>
            <label htmlFor="dashboard-desc" className="block text-sm font-medium text-gray-700 mb-1.5">
              Description (optional)
            </label>
            <textarea
              id="dashboard-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Main living area controls"
              rows={3}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none transition"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

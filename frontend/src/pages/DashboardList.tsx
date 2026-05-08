import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { createDashboard, getDashboards, deleteDashboard, getHAStatus } from '../services/api'
import { DashboardConfig } from '../types/api'

const DashboardList: React.FC = () => {
  const navigate = useNavigate()
  const [dashboards, setDashboards] = useState<DashboardConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [haStatus, setHaStatus] = useState<{ connected: boolean; host?: string; port?: number }>({ connected: false })

  useEffect(() => {
    async function loadDashboards() {
      try {
        const data = await getDashboards()
        setDashboards(data)
      } catch (err) {
        console.error('Failed to load dashboards:', err)
        setError(err instanceof Error ? err.message : 'Failed to load dashboards')
      } finally {
        setLoading(false)
      }
    }
    loadDashboards()

    // Check HA connection status
    getHAStatus().then((status) => setHaStatus(status)).catch(() => {})
  }, [])

  const handleCreate = async () => {
    try {
      const newDashboard = await createDashboard({
        name: 'New Dashboard',
        description: '',
      })
      navigate(`/dashboard/${newDashboard.id}`)
    } catch (err) {
      console.error('Failed to create dashboard:', err)
      setError(err instanceof Error ? err.message : 'Failed to create dashboard')
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this dashboard?')) return
    try {
      await deleteDashboard(id)
      setDashboards((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      console.error('Failed to delete dashboard:', err)
      setError(err instanceof Error ? err.message : 'Failed to delete dashboard')
    }
  }

  const handleEdit = (id: string) => {
    navigate(`/dashboard/${id}`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Dashboards</h1>
        <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboards</h1>

        <div className="flex items-center gap-3">
          {/* Connection status indicator */}
          {!haStatus.connected && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.31 2.487-1.31 3.243 0 .76 1.31 0.01 2.487-0.765 1.31H8.257zm2.922 1.01c0.464-0.795 1.504-0.795 1.968 0 0.463 0.796-0.01 1.597-0.765 1.31H11.18zm-5.85 4.159a1.5 1.5 0 000 2.855A2.5 2.5 0 1110 10.75v-0.099A2.5 2.5 0 008.35 8.268z" clipRule="evenodd" />
              </svg>
              Not connected to HA
            </span>
          )}

          {haStatus.connected && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.709-10.71a.75.75 0 00-1.19-.44l-3.25 3.25h-3.04a.75.75 0 000 1.5h3.04l3.25 3.25a.75.75 0 101.19-.94L10.89 9.5H16v-1.5H10.89z" clipRule="evenodd" />
              </svg>
              Connected to {haStatus.host}
            </span>
          )}

          <button
            onClick={handleCreate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.75 4.75a9.75 9.75 0 100 19.5 9.75 9.75 0 000-19.5zM11 5.75h-2v2H8v1.5h1V13h1.5v-3.75h1V5.75z" />
            </svg>
            New Dashboard
          </button>
        </div>
      </div>

      {/* Connection warning */}
      {!haStatus.connected && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path d="M8.488 11.75a1.25 1.25 0 00-2.5 0v3.5a1.25 1.25 0 002.5 0v-3.5zM9.376 7.874a.75.75 0 011.248 0l.833 1.667a.75.75 0 001.248 0l.833-1.667a.75.75 0 011.248 0l-.833 1.667a.75.75 0 000 1.248l1.667.833a.75.75 0 010 1.248l-1.667.833a.75.75 0 000 1.248l.833 1.667a.75.75 0 01-1.248 0L9.5 11.75H8.5a.75.75 0 010-1.5h1L9.376 7.874z" />
          </svg>
          <div className="text-sm text-yellow-800">
            <p className="font-medium">Home Assistant not connected</p>
            <p className="mt-1">
              Go to{' '}
              <a href="/connect" className="underline hover:text-yellow-900">
                /connect
              </a>{' '}
              to configure your Home Assistant connection.
            </p>
          </div>
        </div>
      )}

      {/* Dashboard list */}
      {dashboards.length === 0 ? (
        <div className="border border-dashed border-gray-300 rounded-lg p-12 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4 text-gray-300" viewBox="0 0 20 20" fill="currentColor">
            <path d="M5.5 16a3.5 3.5 0 110-7 3.5 3.5 0 010 7zM15 16a3.5 3.5 0 110-7 3.5 3.5 0 010 7z" />
          </svg>
          <p className="text-gray-400 mb-2">No dashboards yet</p>
          <button
            onClick={handleCreate}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Create your first dashboard →
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((dashboard) => (
            <div
              key={dashboard.id}
              className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer group relative"
              onClick={() => handleEdit(dashboard.id || '')}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 truncate flex-1 pr-2">
                  {dashboard.name}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(dashboard.id || '')
                  }}
                  className="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-50 text-gray-400 hover:text-red-600 transition-all"
                  title="Delete dashboard"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4v10a2 2 0 002 2h8a2 2 0 002-2V4h-2.618l-.724-1.445A1 1 0 0011 2H9zm5 8.5a1.5 1.5 0 10-3 0 1.5 1.5 0 003 0zM6.5 10.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              {dashboard.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                  {dashboard.description}
                </p>
              )}

              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{(dashboard.cards || []).length} card{(dashboard.cards || []).length !== 1 ? 's' : ''}</span>
              </div>

              {/* Hover overlay */}
              <div className="absolute inset-0 bg-blue-50/0 group-hover:bg-blue-50/30 rounded-lg transition-colors pointer-events-none" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DashboardList

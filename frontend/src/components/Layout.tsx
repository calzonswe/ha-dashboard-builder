import React, { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { getHAStatus } from '../services/api'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [haConnected, setHaConnected] = useState(false)
  const { user, logout } = useAuth()

  useEffect(() => {
    getHAStatus().then((status) => setHaConnected(status.connected)).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile-only top bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200 sm:hidden">
        <div className="max-w-full mx-auto px-4 h-14 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900 truncate">HA Dashboard Builder</h1>
          {haConnected && (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-800 border border-green-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-2 w-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.709-10.71a.75.75 0 00-1.19-.44l-3.25 3.25h-3.04a.75.75 0 000 1.5h3.04l3.25 3.25a.75.75 0 101.19-.94L10.89 9.5H16v-1.5H10.89z" clipRule="evenodd" />
              </svg>
            </span>
          )}
        </div>
      </nav>

      {/* Desktop nav */}
      <nav className="hidden sm:block bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-semibold text-gray-900">HA Dashboard Builder</h1>

            <div className="flex items-center gap-3">
              {/* HA status */}
              {haConnected ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.709-10.71a.75.75 0 00-1.19-.44l-3.25 3.25h-3.04a.75.75 0 000 1.5h3.04l3.25 3.25a.75.75 0 101.19-.94L10.89 9.5H16v-1.5H10.89z" clipRule="evenodd" />
                  </svg>
                  Connected
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.31 2.487-1.31 3.243 0 .76 1.31 0.01 2.487-0.765 1.31H8.257zm2.922 1.01c0.464-0.795 1.504-0.795 1.968 0 0.463 0.796-0.01 1.597-0.765 1.31H11.18zm-5.85 4.159a1.5 1.5 0 000 2.855A2.5 2.5 0 1110 10.75v-0.099A2.5 2.5 0 008.35 8.268z" clipRule="evenodd" />
                  </svg>
                  Not connected
                </span>
              )}

              {/* User info & logout */}
              {user && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">{user.username}</span>
                  <button
                    onClick={logout}
                    className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main content - responsive padding */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        {children}
      </main>
    </div>
  )
}

export default Layout

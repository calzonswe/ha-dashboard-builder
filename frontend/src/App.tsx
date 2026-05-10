import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { ToastProvider } from './hooks/useToast'
import Layout from './components/Layout'
import DashboardList from './pages/DashboardList'
import DashboardView from './pages/DashboardView'
import ConnectionForm from './pages/ConnectionForm'
import PreviewPage from './pages/PreviewPage'
import LoginPage from './pages/LoginPage'
import OnboardingWizard from './pages/OnboardingWizard'

// ─── Auth wrapper that checks onboarding status ──────────────────────

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><p>Loading...</p></div>
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return <>{children}</>
}

function AuthRoutes() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><p>Loading...</p></div>

  // If not authenticated → login page
  if (!isAuthenticated) return <LoginPage />

  // Authenticated but not onboarded → onboarding wizard
  const [onboarded, setOnboarded] = useState<boolean | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('auth_token') || ''
    fetch('/api/settings/onboarding-status', {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      credentials: 'same-origin',
    })
      .then((res) => res.json())
      .then((data: { onboarded: boolean }) => setOnboarded(data.onboarded))
      .catch(() => setOnboarded(false))
  }, [])

  if (onboarded === false || onboarded === null) {
    return <OnboardingWizard />
  }

  // Onboarded → dashboard routes
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardList />} />
                  <Route path="/dashboard/:id" element={<DashboardView />} />
                  <Route path="/connect" element={<ConnectionForm />} />
                  <Route path="/preview/:id" element={<PreviewPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

const App: React.FC = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <AuthRoutes />
      </AuthProvider>
    </ToastProvider>
  )
}

export default App

import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardList from './pages/DashboardList'
import DashboardView from './pages/DashboardView'
import ConnectionForm from './pages/ConnectionForm'

const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardList />} />
        <Route path="/dashboard/:id" element={<DashboardView />} />
        <Route path="/connect" element={<ConnectionForm />} />
      </Routes>
    </Layout>
  )
}

export default App

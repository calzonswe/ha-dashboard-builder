import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardList from './pages/DashboardList'

const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardList />} />
        <Route path="/dashboard/:id" element={
          <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Dashboard View</h1>
            <p className="text-gray-500">Dashboard view placeholder — to be implemented in Epic 2.3.</p>
          </div>
        } />
      </Routes>
    </Layout>
  )
}

export default App

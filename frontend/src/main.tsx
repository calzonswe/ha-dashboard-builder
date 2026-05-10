import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './hooks/useToast'
import { EntityStateProvider } from './hooks/useWebSocket'
import './index.css'

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('root element not found')
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <EntityStateProvider>
          <App />
        </EntityStateProvider>
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>,
)

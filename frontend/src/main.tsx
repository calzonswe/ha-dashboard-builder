import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './hooks/useToast'
import { EntityStateProvider } from './hooks/useWebSocket'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
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

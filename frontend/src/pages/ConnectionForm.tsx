import { useState } from 'react'
import { useToast } from '../hooks/useToast'

export default function ConnectionForm() {
  const { addToast } = useToast()
  const [host, setHost] = useState('')
  const [port, setPort] = useState('8123')
  const [token, setToken] = useState('')
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const handleConnect = async () => {
    if (!host || !token) {
      setStatus('error')
      setMessage('Host and token are required')
      addToast('Please fill in host and token', 'warning')
      return
    }

    setStatus('connecting')
    setMessage('Connecting...')

    try {
      const res = await fetch('/api/ha/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host, port, token }),
      })

      if (res.ok) {
        setStatus('connected')
        setMessage('Connected successfully!')
        addToast('Home Assistant connection established!', 'success')
      } else {
        const data = await res.json()
        setStatus('error')
        setMessage(data.detail || 'Connection failed')
        addToast(`Connection failed: ${data.detail || 'Unknown error'}`, 'error')
      }
    } catch {
      setStatus('error')
      setMessage('Could not reach Home Assistant')
      addToast('Could not reach Home Assistant. Check host and port.', 'error')
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">HA Connection</h1>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow max-w-md">
        <div className="mb-3 sm:mb-4">
          <label htmlFor="host" className="block text-sm font-medium text-gray-700 mb-1">
            Host
          </label>
          <input
            id="host"
            type="text"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="homeassistant.local"
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
          />
        </div>

        <div className="mb-3 sm:mb-4">
          <label htmlFor="port" className="block text-sm font-medium text-gray-700 mb-1">
            Port
          </label>
          <input
            id="port"
            type="text"
            value={port}
            onChange={(e) => setPort(e.target.value)}
            placeholder="8123"
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
          />
        </div>

        <div className="mb-3 sm:mb-4">
          <label htmlFor="token" className="block text-sm font-medium text-gray-700 mb-1">
            Long-Lived Access Token
          </label>
          <input
            id="token"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6..."
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
          />
        </div>

        <button onClick={handleConnect} disabled={status === 'connecting'} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition w-full text-sm sm:text-base">
          {status === 'connecting' ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" className="opacity-75" />
              </svg>
              Connecting...
            </span>
          ) : (
            'Test Connection'
          )}
        </button>

        {message && (
          <div className={`mt-3 sm:mt-4 p-3 rounded text-sm ${status === 'connected' ? 'bg-green-100 text-green-700' : status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
            {message}
          </div>
        )}
      </div>
    </div>
  )
}

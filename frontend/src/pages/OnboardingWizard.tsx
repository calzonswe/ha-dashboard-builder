import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useToast } from '../hooks/useToast'
import { initializeSettings, login } from '../services/api'

type Step = 'welcome' | 'ha-connection' | 'llm-config' | 'summary'

const OnboardingWizard: React.FC = () => {
  const [step, setStep] = useState<Step>('welcome')
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  // HA connection state
  const [haHost, setHaHost] = useState('localhost')
  const [haPort, setHaPort] = useState(8123)
  const [haSsl, setHaSsl] = useState(false)
  const [haToken, setHaToken] = useState('')

  // LLM config state
  const [llmProvider, setLlmProvider] = useState('ollama')
  const [llmBaseUrl, setLlmBaseUrl] = useState('http://localhost:11434')
  const [llmModel, setLlmModel] = useState('llama3.2')

  // App name
  const [appName] = useState('HA Dashboard Builder')

  const { login: authLogin } = useAuth()

  const handleNext = async () => {
    if (step === 'welcome') {
      setStep('ha-connection')
    } else if (step === 'summary') {
      await saveAndFinish()
    }
  }

  const saveAndFinish = async () => {
    setLoading(true)
    try {
      // Initialize settings in DB
      await initializeSettings({
        app_name: appName,
        ha_host: haHost,
        ha_port: haPort,
        ha_ssl: haSsl,
        ha_access_token: haToken,
        llm_provider: llmProvider,
        llm_base_url: llmBaseUrl,
        llm_model: llmModel,
      })

      // Auto-connect to HA and discover entities
      const token = localStorage.getItem('auth_token') || ''
      const res = await fetch('/api/ha/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: 'same-origin',
        body: JSON.stringify({ host: haHost, port: haPort, token: haToken, ssl: haSsl }),
      })

      if (res.ok) {
        toast.success('Setup complete! Redirecting to dashboard...')
        window.location.href = '/'
      } else {
        const err = await res.json().catch(() => ({ detail: 'Connection failed' }))
        toast.error(err.detail || 'HA connection failed. You can configure it later.')
        // Still mark as onboarded and redirect
        window.location.href = '/'
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Setup failed'
      toast.error(message)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 px-4">
      <div className="w-full max-w-lg">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            {['welcome', 'ha-connection', 'llm-config', 'summary'].map((s, i) => (
              <div key={s} className={`h-2 flex-1 rounded-full transition-all ${step === s ? 'bg-blue-600' : step > s ? 'bg-green-500' : 'bg-gray-300'}`} />
            ))}
          </div>
          <p className="text-sm text-gray-500">Step {['welcome', 'ha-connection', 'llm-config', 'summary'].indexOf(step) + 1} of 4</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          {step === 'welcome' && (
            <>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">Welcome to HA Dashboard Builder</h2>
              <p className="text-gray-600 mb-6">
                Let's get your dashboard builder set up. We'll configure your Home Assistant connection and optional AI chat assistant in just a few steps.
              </p>

              {/* Feature highlights */}
              <div className="space-y-3 mb-8">
                {[
                  'Visual drag-and-drop dashboard builder',
                  'Real-time entity discovery from Home Assistant',
                  'AI-powered chat to build dashboards naturally',
                  'Responsive design for mobile and desktop',
                ].map((feature, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.709 3.171a.75.75 0 010 1.06l-8.485 8.485a.75.75 0 01-1.06 0L2.105 10.39a.75.75 0 011.06-1.06l2.92 2.92 7.958-7.958a.75.75 0 011.06 0z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={handleNext}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition"
              >
                Get Started
              </button>
            </>
          )}

          {step === 'ha-connection' && (
            <>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Home Assistant Connection</h2>
              <p className="text-sm text-gray-500 mb-6">Enter your Home Assistant instance details.</p>

              {/* Host */}
              <div className="mb-4">
                <label htmlFor="ha-host" className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                <input id="ha-host" type="text" value={haHost} onChange={(e) => setHaHost(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="localhost" />
              </div>

              {/* Port */}
              <div className="mb-4">
                <label htmlFor="ha-port" className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                <input id="ha-port" type="number" value={haPort} onChange={(e) => setHaPort(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="8123" />
              </div>

              {/* SSL */}
              <div className="mb-4">
                <label htmlFor="ha-token" className="block text-sm font-medium text-gray-700 mb-1">Long-Lived Access Token</label>
                <input id="ha-token" type="password" value={haToken} onChange={(e) => setHaToken(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Enter your HA access token" />
                <p className="text-xs text-gray-400 mt-1">Generate in Home Assistant → Profile → Long-Lived Access Tokens</p>
              </div>

              {/* SSL checkbox */}
              <label className="flex items-center gap-2 mb-6 cursor-pointer">
                <input type="checkbox" checked={haSsl} onChange={(e) => setHaSsl(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
                <span className="text-sm text-gray-700">Use SSL (HTTPS)</span>
              </label>

              {/* Buttons */}
              <div className="flex gap-3">
                <button onClick={() => setStep('welcome')} className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition">Back</button>
                <button onClick={handleNext} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition">Continue</button>
              </div>
            </>
          )}

          {step === 'llm-config' && (
            <>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">AI Chat Assistant</h2>
              <p className="text-sm text-gray-500 mb-6">Optional: Configure an LLM for AI-powered dashboard generation.</p>

              {/* Provider */}
              <div className="mb-4">
                <label htmlFor="llm-provider" className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <select id="llm-provider" value={llmProvider} onChange={(e) => setLlmProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white">
                  <option value="ollama">Ollama</option>
                  <option value="lmstudio">LM Studio</option>
                  <option value="none">Skip (configure later)</option>
                </select>
              </div>

              {/* Base URL */}
              {llmProvider !== 'none' && (
                <>
                  <div className="mb-4">
                    <label htmlFor="llm-base-url" className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                    <input id="llm-base-url" type="text" value={llmBaseUrl} onChange={(e) => setLlmBaseUrl(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="http://localhost:11434" />
                  </div>

                  {/* Model */}
                  <div className="mb-6">
                    <label htmlFor="llm-model" className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                    <input id="llm-model" type="text" value={llmModel} onChange={(e) => setLlmModel(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="llama3.2" />
                  </div>
                </>
              )}

              {/* Buttons */}
              <div className="flex gap-3">
                <button onClick={() => setStep('ha-connection')} className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition">Back</button>
                <button onClick={handleNext} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition">Continue</button>
              </div>
            </>
          )}

          {step === 'summary' && (
            <>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Review & Save</h2>
              <p className="text-sm text-gray-500 mb-6">Confirm your settings before completing setup.</p>

              {/* Summary */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3 mb-6 border border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">App Name</span>
                  <span className="text-sm font-medium text-gray-900">{appName}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">HA Host</span>
                  <span className="text-sm font-medium text-gray-900">{haHost}:{haPort}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">SSL</span>
                  <span className="text-sm font-medium text-gray-900">{haSsl ? 'Yes' : 'No'}</span>
                </div>
                {llmProvider !== 'none' && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">LLM Provider</span>
                      <span className="text-sm font-medium text-gray-900">{llmProvider}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Base URL</span>
                      <span className="text-sm font-medium text-gray-900">{llmBaseUrl}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Model</span>
                      <span className="text-sm font-medium text-gray-900">{llmModel}</span>
                    </div>
                  </>
                )}
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button onClick={() => setStep('llm-config')} className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition">Back</button>
                <button onClick={handleNext} disabled={loading}
                  className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition disabled:opacity-50">
                  {loading ? 'Saving...' : 'Save & Continue'}
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-500 mt-6">
          You can always change these settings later in the dashboard.
        </p>
      </div>
    </div>
  )
}

export default OnboardingWizard

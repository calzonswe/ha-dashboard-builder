import { Component, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React ErrorBoundary caught:', error.name, error.message, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      const fallback = this.props.fallback || (
        <div className="min-h-[40vh] flex items-center justify-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 max-w-md text-center">
            <h2 className="text-xl font-bold text-red-700 mb-3">Something went wrong</h2>
            <p className="text-red-600 mb-4">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 text-white px-5 py-2 rounded hover:bg-red-700 transition"
            >
              Reload Page
            </button>
          </div>
        </div>
      )
      return <>{fallback}</>
    }

    return this.props.children
  }
}

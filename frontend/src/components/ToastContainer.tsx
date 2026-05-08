import { useToast, Toast as ToastType } from '../hooks/useToast'

const TYPE_STYLES: Record<string, string> = {
  success: 'bg-green-50 border-green-400 text-green-800',
  error: 'bg-red-50 border-red-400 text-red-800',
  info: 'bg-blue-50 border-blue-400 text-blue-800',
  warning: 'bg-yellow-50 border-yellow-400 text-yellow-800',
}

const TYPE_ICONS: Record<string, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
  warning: '⚠',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm" aria-live="assertive">
      {toasts.map((toast: ToastType) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  )
}

function ToastItem({ toast, onClose }: { toast: ToastType; onClose: () => void }) {
  const styles = TYPE_STYLES[toast.type] || TYPE_STYLES.info
  const icon = TYPE_ICONS[toast.type] || 'ℹ'

  return (
    <div
      className={`border rounded-lg shadow-lg p-3 flex items-start gap-2 ${styles} animate-fade-in`}
      role="alert"
    >
      <span className="text-lg font-bold leading-none mt-0.5">{icon}</span>
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={onClose}
        className="text-gray-400 hover:text-gray-600 ml-2 flex-shrink-0"
        aria-label="Dismiss notification"
      >
        ✕
      </button>
    </div>
  )
}

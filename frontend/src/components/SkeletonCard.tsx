interface SkeletonCardProps {
  variant?: 'dashboard' | 'widget'
}

export default function SkeletonCard({ variant = 'dashboard', children }: React.PropsWithChildren<SkeletonCardProps>) {
  if (children) return <>{children}</>

  if (variant === 'widget') {
    return (
      <div className="bg-white p-4 rounded-lg shadow animate-pulse">
        <div className="flex justify-between items-start mb-3">
          <div className="h-5 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-6" />
        </div>
        <div className="h-10 bg-gray-200 rounded mb-3" />
        <div className="h-3 bg-gray-200 rounded w-2/3" />
      </div>
    )
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow animate-pulse">
      <div className="flex justify-between items-start mb-4">
        <div className="h-6 bg-gray-200 rounded w-2/3" />
        <div className="h-5 bg-gray-200 rounded w-12" />
      </div>
    </div>
  )
}

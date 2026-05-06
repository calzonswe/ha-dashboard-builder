import { useState, useEffect, useCallback } from 'react'
import { HAEntity } from '../types/api'
import { getEntities } from '../services/api'

interface UseEntitiesResult {
  entities: HAEntity[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useEntities(): UseEntitiesResult {
  const [entities, setEntities] = useState<HAEntity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getEntities()
      setEntities(data)
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refetch()
  }, [refetch])

  return { entities, loading, error, refetch }
}

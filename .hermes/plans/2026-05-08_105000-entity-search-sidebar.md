# Plan: Backend Entity Search Integration for Sidebar

## Goal

Replace the current client-side entity filtering in the sidebar with backend-powered search via `/api/ha/search`. This enables efficient searching across large Home Assistant installations (100+ entities) without loading all entities into the browser.

## Current Context / Assumptions

### Backend (already implemented)
- `POST /api/ha/search` endpoint exists in `backend/app/api/routes.py`
- Accepts `SearchRequest(query: str)` and returns `EntityListResponse(entities, count)`
- `EntityCache.search()` performs SQL LIKE query against `name` and `entity_id` fields (case-insensitive)
- `CachedEntity` schema includes: entity_id, domain, name, state, unit_of_measurement

### Frontend (needs changes)
- `getEntities()` in `frontend/src/services/api.ts` fetches ALL entities via `/api/ha/entities`
- `useEntities()` hook wraps this call and returns `{entities, loading, error, refetch}`
- `EntitySidebar.tsx` has a search input but only filters the pre-fetched client-side list
- `MobileSidebar.tsx` mirrors the same behavior for mobile

### Assumptions
- Backend search is fast (SQLite LIKE query)
- We can fetch entities in batches or use pagination if needed
- The sidebar should show results grouped by domain regardless of whether they come from cache or search

## Proposed Approach

1. **Add `searchEntities` API function** to the frontend service layer
2. **Create a new hook** `useEntitySearch` that handles debounced backend search
3. **Update EntitySidebar** to use the search hook when query is active, falling back to cached entities when no query
4. **Update MobileSidebar** with the same behavior

## Step-by-Step Plan

### Step 1: Add search API function (`frontend/src/services/api.ts`)

Add a new exported function after `getEntities()`:

```typescript
export async function searchEntities(query: string): Promise<HAEntity[]> {
  const res = await fetch(`${API_BASE}/dashboards/search-entities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  const data = await res.json()
  return data.entities.map((e: any) => ({
    entity_id: e.entity_id,
    object_id: e.entity_id.split('.')[1] || e.entity_id,
    state: e.state,
    attributes: {},
    last_changed: '',
    last_updated: '',
  }))
}
```

### Step 2: Create `useEntitySearch` hook (`frontend/src/hooks/useEntitySearch.ts`)

New file with debounced search that calls the backend API:

```typescript
import { useState, useEffect, useRef } from 'react'
import { HAEntity } from '../types/api'
import { searchEntities } from '../services/api'

export function useEntitySearch(query: string) {
  const [results, setResults] = useState<HAEntity[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const timeoutRef = useRef<number>()

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }

    setLoading(true)
    clearTimeout(timeoutRef.current)

    timeoutRef.current = window.setTimeout(async () => {
      try {
        const data = await searchEntities(query.trim())
        setResults(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)))
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300) // debounce

    return () => clearTimeout(timeoutRef.current)
  }, [query])

  return { results, loading, error }
}
```

### Step 3: Update EntitySidebar (`frontend/src/components/EntitySidebar.tsx`)

Changes needed:
- Import `useEntitySearch` hook
- Add search state and pass it to the new hook
- When query is active → use backend search results instead of client-side filtering
- Show loading spinner while searching
- Show error message if search fails
- Maintain domain grouping for both cached and search results

Key changes:
```tsx
import { useEntitySearch } from '../hooks/useEntitySearch'

const EntitySidebar: React.FC<EntitySidebarProps> = ({ entities, ... }) => {
  const [search, setSearch] = useState('')
  const { results: searchResults, loading: searching, error: searchError } = useEntitySearch(search)
  
  // Use search results when query is active, otherwise use cached entities
  const displayEntities = search.trim() ? searchResults : entities
  
  // ... rest of component with domain grouping using displayEntities
}
```

### Step 4: Update MobileSidebar (`frontend/src/components/MobileSidebar.tsx`)

Same pattern as EntitySidebar — integrate `useEntitySearch` for backend-powered search on mobile.

## Files Likely to Change

| File | Action | Reason |
|------|--------|--------|
| `frontend/src/services/api.ts` | Edit | Add `searchEntities()` function |
| `frontend/src/hooks/useEntitySearch.ts` | **Create** | New debounced search hook |
| `frontend/src/components/EntitySidebar.tsx` | Edit | Use backend search when query active |
| `frontend/src/components/MobileSidebar.tsx` | Edit | Same as EntitySidebar |

## Tests / Validation

### Backend tests (existing)
- Run existing test suite: `cd backend && python -m pytest tests/ -v`
- Verify `/api/ha/search` endpoint works with mocked HA client

### Frontend validation
1. Open dashboard builder → sidebar should show entities grouped by domain
2. Type in search box → results should update after 300ms debounce
3. Search for "living room" → should match entity names and IDs containing that text
4. Clear search → should revert to showing all cached entities
5. Test with no HA connection → should show error gracefully

### Manual testing checklist
- [ ] Backend search returns correct results for various queries
- [ ] Frontend shows loading state during search
- [ ] Frontend handles empty results (no matches)
- [ ] Frontend handles search errors gracefully
- [ ] Mobile sidebar also uses backend search
- [ ] Domain grouping works correctly with search results

## Risks, Tradeoffs, and Open Questions

### Risks
1. **Backend dependency**: If HA is disconnected, the search endpoint will fail — need graceful fallback to cached entities or empty state
2. **Debounce timing**: 300ms may feel slow on fast connections; could be tuned lower (e.g., 150ms)
3. **No pagination for large results**: If a search returns hundreds of matches, the sidebar could overflow — consider limiting to first 50-100 results

### Tradeoffs
- **Client-side vs Backend filtering**: Client-side is instant but doesn't scale; backend search scales well but adds network latency
- **Hybrid approach chosen**: Use cached entities for browsing (no query), backend search only when user types — best of both worlds

### Open Questions
1. Should we add a "search all" button to trigger full-text search across all entity names?
2. Do we need to handle special characters in search queries (SQL injection protection)? → Backend uses parameterized SQL, so safe.
3. Should the sidebar show a "loading entities..." state while initial fetch completes?

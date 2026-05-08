# Fix: Frontend ↔ Backend API Mismatches

## Goal

Resolve all frontend-backend API response format mismatches that cause the React app to crash on load (TypeError: dashboard is not iterable) and produce incorrect data display.

## Current Context / Assumptions

- **Backend**: FastAPI at `~/projects/ha-dashboard-builder/backend/app/api/dashboard_routes.py`
- **Frontend**: React + TypeScript Vite app at `~/projects/ha-dashboard-builder/frontend/src/`
- The backend returns paginated/wrapped responses with `{dashboards: [...], count: N}` format
- The frontend expects plain arrays or has incorrect field name mappings
- The SSE endpoint and states endpoint also have potential mismatches

## Issues Found

### Issue 1: Dashboard List — Wrapped response vs plain array (CRITICAL)
**Location**: `frontend/src/pages/DashboardList.tsx` line 30
**Problem**: Backend returns `{dashboards: [...], count: N}` but the frontend tries to iterate directly over the API response object. The `.map()` call on a non-array causes `TypeError: dashboard is not iterable`.
- **Backend**: `DashboardListResponse(dashboards=[...], count=N)` → JSON: `{"dashboards": [...], "count": 3}`
- **Frontend** (line 24): `const dashboards = data?.dashboards || []` — this extraction is correct
- **Root cause**: The actual crash happens because the API service or hook doesn't properly unwrap the response. Need to verify the exact path where `.map()` fails.

### Issue 2: Dashboard Detail — Field name mismatches
**Location**: `frontend/src/hooks/useDashboard.ts`, `frontend/src/components/DashboardHeader.tsx`
**Problem**: Backend returns `name` but frontend expects `title`. Also backend has no `updated_at` field.
- **Backend** (`FullDashboardResponse`): `{id, name, description, cards: [...]}` — uses `name`
- **Frontend** (`DashboardConfig` type): `{id?, title, description?, cards, layout?, created_at?, updated_at?}` — expects `title`, `updated_at`
- **Impact**: Dashboard header shows "Untitled Dashboard" instead of the actual name. `dashboard.title` is always undefined.

### Issue 3: Card/Widget field mismatches
**Location**: `frontend/src/hooks/useDashboard.ts`, `frontend/src/components/DashboardCanvas.tsx`
**Problem**: Backend returns widget fields (`card_type`, `entity_id`, `title`) but frontend expects different names.
- **Backend** (`WidgetResponse`): `{id, page_id, card_type, entity_id?, title?, config?, x, y, width, height}`
- **Frontend** (`DashboardCard` type): `{id, entity_id, x, y, width, height, config?}` — missing `card_type`, `page_id`
- **Impact**: Card types not displayed correctly. `page_id` field ignored (acceptable).

### Issue 4: SSE States endpoint format mismatch
**Location**: `frontend/src/hooks/useEntityStates.ts` line 35
**Problem**: Backend states endpoint returns `{states: [...], count: N}` but frontend expects plain array.
- **Backend** (`StateListResponse`): `{states: [HAState...], count: N}`
- **Frontend** (line 35): `for (const s of states)` — iterates over the whole object instead of `states.states`

### Issue 5: Entity list endpoint format mismatch
**Location**: `frontend/src/hooks/useEntities.ts` line 22
**Problem**: Backend returns `{entities: [...], count: N}` but frontend expects plain array.
- **Backend** (`EntityListResponse`): `{entities: [CachedEntity...], count: N}`
- **Frontend** (line 22): `setEntities(data)` — sets the whole object instead of `data.entities`

### Issue 6: Card update request field name mismatch
**Location**: `frontend/src/hooks/useDashboard.ts` lines 57-67
**Problem**: Frontend sends `card_type` but backend expects different field names in `CardUpdateRequest`.
- **Frontend** sends: `{id, card_type, entity_id, title, config, x, y, width, height}`
- **Backend** (`CardUpdateRequest`): accepts `{card_type?, entity_id?, title?, config?, x?, y?, width?, height?}` — this actually matches!

## Proposed Approach

### Phase 1: Fix the critical crash (Issue 1)
1. Verify exact error by checking how `getDashboards()` returns data in `api.ts`
2. Ensure DashboardList properly unwraps `{dashboards, count}` → uses only `.dashboards` array

### Phase 2: Fix field name mappings (Issues 2-5)
3. Add adapter layer in frontend hooks to map backend fields → frontend expectations
4. Specifically handle `name` → `title` mapping for dashboards
5. Handle wrapped responses: `{states, count}` → extract `.states`, `{entities, count}` → extract `.entities`

### Phase 3: Verify and test (Issue 6)
6. Confirm card update request format matches backend expectations
7. Test all endpoints end-to-end

## Step-by-Step Plan

### Step 1: Fix DashboardList.tsx — unwrap dashboard response
**File**: `frontend/src/pages/DashboardList.tsx`
- Verify line 24 correctly extracts `data?.dashboards || []`
- If the crash is elsewhere, trace to find where `.map()` receives an object instead of array

### Step 2: Fix useDashboard.ts — map backend fields to frontend expectations
**File**: `frontend/src/hooks/useDashboard.ts`
- In `loadDashboard()`, transform backend response:
  ```ts
  const data = await apiGetDashboard(dashboardId)
  // Backend returns {id, name, description, cards} but frontend expects title
  const transformed = {
    ...data,
    title: data.name || data.title || '',  // map 'name' → 'title'
    updated_at: new Date().toISOString(),  // add missing field
  }
  setDashboard(transformed)
  ```

### Step 3: Fix useEntityStates.ts — unwrap states response
**File**: `frontend/src/hooks/useEntityStates.ts`
- Line 32: Change `const states = await getStates()` to handle wrapped response
- Add: `const statesData = data?.states || []` or fix the API service

### Step 4: Fix useEntities.ts — unwrap entities response
**File**: `frontend/src/hooks/useEntities.ts`
- Line 21: Change `setEntities(data)` to `setEntities(data?.entities || [])`

### Step 5: Verify card update request format
**File**: `frontend/src/hooks/useDashboard.ts` lines 57-67
- Confirm the payload matches backend `CardUpdateRequest` schema
- The field names already match — no changes needed here

## Files Likely to Change

| File | Changes |
|------|---------|
| `frontend/src/pages/DashboardList.tsx` | Unwrap dashboard list response |
| `frontend/src/hooks/useDashboard.ts` | Map `name` → `title`, handle response format |
| `frontend/src/hooks/useEntityStates.ts` | Unwrap states array from wrapped response |
| `frontend/src/hooks/useEntities.ts` | Unwrap entities array from wrapped response |
| `frontend/src/services/api.ts` | Verify API service returns unwrapped data or add adapters |

## Tests / Validation

1. **Dashboard List page**: Navigate to `/` — should display all dashboards without crash
2. **Dashboard Detail page**: Click a dashboard — should show correct title (not "Untitled Dashboard")
3. **Entity sidebar**: Should list discovered entities from HA
4. **Live states**: Entity state badges should update in real-time via SSE
5. **Card save**: Drag/resize cards and click Save — should persist without errors

## Risks, Tradeoffs, and Open Questions

### Risks
- **SSE format unknown**: Need to verify exact SSE event payload format from backend
- **Backend changes risky**: Modifying FastAPI response schemas could break other consumers
- **Type safety**: Adding ad-hoc field mappings reduces type safety; consider updating types instead

### Tradeoffs
- **Frontend adapters vs Backend changes**: Fixing in frontend is safer (no API contract changes), but backend should ideally match frontend expectations
- **Field mapping strategy**: Central adapter functions vs inline transforms per hook

### Open Questions
1. Does the SSE endpoint actually return `{states, count}` wrapped format or plain array?
2. Are there other pages/components that consume these APIs?
3. Should we update the backend to use consistent response formats (all wrapped or all unwrapped)?

## Verification Steps

After implementing fixes:
1. Run `cd frontend && npm run build` — should compile without errors
2. Start dev server and navigate through all pages
3. Check browser console for any remaining type errors
4. Verify dashboard title displays correctly in header
5. Test save operation on a dashboard with cards

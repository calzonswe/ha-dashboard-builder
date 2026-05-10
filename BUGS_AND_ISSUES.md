# HA Dashboard Builder - Bugs, Issues & Missing Features

## 🔴 Critical / Blocking Issues

### 1. Home Assistant Connection Requires Access Token (Not Configured)
**Status:** Backend can reach HA on HTTP, but authentication fails because `HA_ACCESS_TOKEN` is empty in `.env`.
- **Impact:** No entities are discovered; dashboard cards cannot be created from real HA data.
- **Fix:** Add a valid long-lived access token to the backend's `.env` file (`/app/.env` inside container).
- **Workaround:** Use the `/api/ha/connect` endpoint with a valid token, or set `HA_ACCESS_TOKEN` in `.env`.

### 2. HA SSL Setting Not Exposed via Connect Endpoint
**Status:** The `/api/ha/connect` POST endpoint creates an HAAPI instance without passing `ssl=False`, causing SSL errors when connecting to HTTP-based HA instances.
- **Impact:** Users behind a firewall or using HTTP (not HTTPS) cannot connect to HA through the UI.
- **Fix:** Add `ssl` field to `HAConnectionRequest` schema and pass it through to HAAPI constructor.

### 3. No Preview Page Exists Despite Code References It
**Status:** The frontend calls `window.open('/preview/${id}', '_blank')` in DashboardView, but there is no `/preview/:id` route defined in App.tsx or any preview page component.
- **Impact:** Clicking "Preview" button opens a blank/404 page.
- **Fix:** Create a PreviewPage component and add the route to App.tsx.

---

## 🟡 High Priority Issues

### 4. Chat Endpoint Has No System Prompt / Card Schema Context
**Status:** The chat endpoint injects entity context as a system message but doesn't provide:
- A list of supported card types (light, sensor, switch, camera, etc.)
- The expected YAML/card configuration format for each card type
- Instructions on how to map HA entities to dashboard cards

**Impact:** LLM returns generic responses (e.g., when asked "add outdoor temperature", it returned a Home Assistant YAML sensor config instead of a dashboard card definition).

**Fix:** Add comprehensive system prompt with:
```
You are a Home Assistant Dashboard Builder assistant. You help users create dashboard cards.
Supported card types and their configurations:
- light: { type: 'state-card', entity_id: 'light.xxx', title: '...' }
- sensor: { type: 'sensor-card', entity_id: 'sensor.xxx', unit: '°C' }
- switch: { type: 'switch-card', entity_id: 'switch.xxx' }
- camera: { type: 'camera-card', entity_id: 'camera.xxx' }
Return ONLY valid JSON card configurations, never YAML.
```

### 5. Chat Endpoint Doesn't Create Cards — Only Returns Config Text
**Status:** The chat endpoint is read-only (returns text responses). There's no `/api/chat/add-card` or similar endpoint that would parse the LLM response and actually create a dashboard card.

**Impact:** Users can ask for cards but nothing happens — they have to manually copy-paste configs into the UI.

**Fix:** Add an endpoint like `POST /api/chat/messages` with `action: "add_card"` that parses LLM JSON responses and creates cards via the dashboard API.

### 6. Dashboard Cards Don't Show Live Entity States
**Status:** The frontend has `useEntityStates()` hook for real-time state updates, but entity states are fetched from `/api/ha/entities` which requires HA connection (currently broken due to missing token).

**Impact:** Even when cards exist in the dashboard, they show stale or empty data.

---

## 🟠 Medium Priority Issues

### 7. Entity Sidebar Doesn't Show Areas
**Status:** The `EntitySidebar.tsx` groups entities by domain only (`light`, `sensor`, etc.). It doesn't group by Home Assistant areas (rooms), which is the more intuitive way to browse entities.

**Fix:** Add area-based grouping as an alternative view in the sidebar.

### 8. No Entity Picker Modal for Adding Cards
**Status:** The `EntityPickerModal.tsx` component exists but there's no clear "Add Card" button flow that opens it. Users must know how to use the drag-and-drop from the sidebar.

**Fix:** Add a prominent "+ Add Card" button in the DashboardHeader or DashboardCanvas toolbar.

### 9. CardConfigModal Doesn't Support All Card Types
**Status:** The `CardConfigModal.tsx` has limited configuration options. It doesn't support:
- Camera stream settings (stream URL, refresh interval)
- Energy price card specific fields (price entity, currency)
- Weather card fields (forecast entity, units)

**Fix:** Add type-specific configuration forms in the modal based on `card_type`.

### 10. No Undo/Redo for Dashboard Changes
**Status:** Dragging cards around or editing configs has no undo functionality. If a user accidentally moves a card, they can't easily revert.

**Fix:** Implement undo stack in `useDashboard` hook (store previous state before mutations).

### 11. Export Modal Generates HA YAML but Doesn't Match Card Structure
**Status:** The export modal generates Home Assistant Lovelace YAML, but the dashboard cards use a custom JSON structure. The exported YAML may not match how cards are actually rendered in the frontend.

**Fix:** Either:
- Make the exporter generate proper Lovelace card YAML for each card type
- Or document that exports are for reference only and users should manually recreate in HA UI

### 12. Import Modal Has No Validation
**Status:** The import modal accepts any JSON/YAML without validating against the expected schema. Invalid imports could corrupt dashboard data.

**Fix:** Add schema validation before importing, with error messages for invalid fields.

---

## 🔵 Low Priority / Nice-to-Have Issues

### 13. No Dark Mode Toggle
**Status:** The frontend uses a light theme throughout (`bg-gray-50`, `text-gray-900`). No dark mode option exists despite the `CardConfig.theme` supporting `'light' | 'dark'`.

**Fix:** Add a dark mode toggle in settings and apply Tailwind's `dark:` classes.

### 14. Dashboard List Doesn't Show Card Count
**Status:** The dashboard list page shows dashboards but doesn't indicate how many cards each has, making it hard to identify which dashboard is which.

**Fix:** Add card count badge next to each dashboard name.

### 15. No Keyboard Shortcuts
**Status:** No keyboard shortcuts for common actions (delete selected card, copy/paste card, undo).

**Fix:** Add keyboard shortcuts using a library like `react-hotkeys`.

### 16. WebSocket Reconnection Not Handled Gracefully
**Status:** The SSE/WebSocket connection to `/api/ws/status` doesn't have explicit reconnection logic with exponential backoff. If the backend restarts, the frontend may show a broken state indefinitely.

**Fix:** Add reconnection handling in `useWebSocket.tsx`.

### 17. No Loading Skeletons for Dashboard View
**Status:** When loading a dashboard, there's no skeleton/placeholder UI — just a blank canvas until data arrives.

**Fix:** Add skeleton loaders in DashboardCanvas while `loading` is true.

---

## 📋 Infrastructure / DevOps Issues

### 18. Docker Compose Doesn't Mount .env File
**Status:** The docker-compose.yml passes environment variables using `${VAR:-default}` syntax, but the `.env` file is not mounted into the container. The backend reads from `/app/.env` which doesn't exist by default.

**Fix:** Add a volume mount for `.env` or use `env_file` directive in docker-compose.yml.

### 19. No Health Check for HA Connection
**Status:** The Docker health check only verifies the FastAPI server is running (`/health`). It doesn't verify HA connectivity, so the container shows "healthy" even when HA is unreachable.

**Fix:** Add a `/health/ha` endpoint that checks HA connection and include it in the healthcheck command.

### 20. Frontend Nginx Config Proxies All /api/* to Backend
**Status:** The nginx config proxies all `/api/*` requests to the backend, which is correct for REST API but may cause issues if new endpoints are added that don't follow the `/api/` prefix convention.

**Note:** This is more of a design note than a bug — it's working as intended.

---

## 🐛 Minor Bugs / Typos

### 21. DEBUG Mode Enabled in Production
**Status:** `config.py` has `DEBUG: bool = True`. Debug mode should be disabled in production builds.

**Fix:** Set `DEBUG=False` or use an environment variable to control it.

### 22. EntityCard Doesn't Handle "unavailable" / "unknown" States
**Status:** The `EntityCard.tsx` component doesn't have special styling for HA states like `"unavailable"`, `"unknown"`, or `"off"` (for lights). It just displays the raw state string.

**Fix:** Add state-aware styling in EntityCard.

### 23. No Error Boundary Around DashboardCanvas
**Status:** If a card component throws an error during render, there's no fallback UI — the entire canvas breaks.

**Fix:** Wrap individual cards or the canvas in an ErrorBoundary with per-card error handling.

---

## 📊 Summary

| Category | Count | Priority |
|----------|-------|----------|
| Critical / Blocking | 3 | 🔴 Must fix before usable |
| High Priority | 2 | 🟡 Should fix for good UX |
| Medium Priority | 8 | 🟠 Nice to have for polish |
| Low Priority | 5 | 🔵 Enhancement suggestions |
| Minor Bugs | 3 | ⚪ Quick wins |

**Total issues identified:** 23

---

## 🎯 Recommended Fix Order

1. **Fix HA token configuration** (#1) — without this, no real data flows through the app
2. **Add system prompt to chat endpoint** (#4) — so LLM returns proper card configs
3. **Create preview page** (#3) — so "Preview" button works
4. **Expose SSL setting in connect endpoint** (#2) — so HTTP HA connections work from UI
5. **Fix EntityCard state handling** (#22) — quick win for better UX

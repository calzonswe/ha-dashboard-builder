# Plan: Close Open GitHub Issues (#53, #54, #55)

## Goal

Address all 3 currently open GitHub issues in the ha-dashboard-builder repository by fixing code where needed and closing issues that have already been resolved.

## Current Context

- **Repository**: `~/projects/ha-dashboard-builder` (GitHub: `calzonswe/ha-dashboard-builder`)
- **Open Issues**: #53, #54, #55
- **Recent Activity**: All 3 issues were identified in a previous session; fixes for #54 and #55 have been committed but issues remain open. Only #53 requires actual code changes.

## Analysis of Each Issue

### Issue #55 — "HA API routes double-prefixed (/api/api/ha/*)"
- **Status**: ✅ Already fixed in commit `1c02c5c` ("fix: remove duplicate /api prefix from HA router")
- **Current state**: Routes correctly at `/api/ha/*` (verified via curl)
- **Action needed**: Close the GitHub issue

### Issue #54 — "Missing frontend service in docker-compose.yml"
- **Status**: ✅ Already fixed — `docker-compose.yml` includes the frontend service (lines 40–50)
- **Current state**: Both containers running (`ha-dashboard-api`, `ha-dashboard-frontend`)
- **Action needed**: Close the GitHub issue

### Issue #53 — "HA connection failure crashes app startup"
- **Status**: 🔴 Still broken — requires code changes
- **Problem**: In `backend/app/main.py`, the `lifespan` function creates `HAAPI`, `EntityDiscoveryService`, `CacheRefreshService`, and `HAEventListener` eagerly without try/except. If HA is unreachable, the app crashes during startup.
- **Current behavior**: App fails to start if HA instance is unavailable
- **Expected behavior**: App starts successfully even without HA; reports HA connectivity status separately

## Proposed Approach

### Step 1: Fix Issue #53 — Make HA connection optional at startup

**File to change**: `backend/app/main.py`

**Changes needed:**
1. Wrap the entire service initialization block (lines 34–65) in a try/except
2. Catch `HAConnectionError`, `httpx.ConnectError`, and general exceptions
3. Log warnings but don't crash — set `ha_client = None` on failure
4. Skip dependent services (`discovery_service`, `cache_refresh_service`, `event_listener`) if HA client is None
5. Add a `/health/ha` endpoint that reports HA connectivity status separately

**Code sketch:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ha_client, discovery_service, cache_refresh_service, event_listener, llm_service
    
    init_db()
    
    # Initialize HA client with error handling
    ha_client = None
    discovery_service = None
    cache_refresh_service = None
    event_listener = None
    
    try:
        ha_client = HAAPI(
            host=settings.HA_HOST,
            port=settings.HA_PORT,
            token=settings.HA_ACCESS_TOKEN,
        )
        # Test connection (will raise if unreachable)
        await asyncio.to_thread(ha_client.test_connection)
        
        discovery_service = EntityDiscoveryService(ha_client=ha_client)
        cache_refresh_service = CacheRefreshService(discovery_service, interval_seconds=60)
        await cache_refresh_service.start()
        
        event_listener = HAEventListener(
            ha_client=ha_client,
            websocket_manager=websocket_manager,
            poll_interval=settings.WS_POLL_INTERVAL or 5.0,
        )
        await event_listener.start()
    except Exception as exc:
        logger.warning(f"HA connection failed at startup (non-fatal): {exc}")
        ha_client = None
    
    # Initialize LLM service if provider is configured
    llm_service = LLMService(...)
    from app.services.llm_service import set_llm_service
    set_llm_service(llm_service)
    
    yield
    
    # Shutdown (existing code, unchanged)
```

**Additional endpoint to add:**
```python
@app.get("/health/ha")
async def ha_health_check():
    """Health check for Home Assistant connectivity."""
    if ha_client is None:
        return {"ha_connected": False, "message": "HA not configured or unreachable"}
    try:
        await asyncio.to_thread(ha_client.test_connection)
        return {"ha_connected": True}
    except Exception as exc:
        return {"ha_connected": False, "error": str(exc)}
```

### Step 2: Close all three GitHub issues

Use `gh issue close` for each:
- `gh issue close 53 --comment "Fixed — HA connection is now optional at startup..."`
- `gh issue close 54 --comment "Resolved — frontend service added to docker-compose.yml"`
- `gh issue close 55 --comment "Resolved — duplicate /api prefix removed from router"`

## Files Likely to Change

| File | Change |
|------|--------|
| `backend/app/main.py` | Wrap HA init in try/except; add `/health/ha` endpoint |

## Tests / Validation

1. **Start container without HA**: Run with empty `HA_ACCESS_TOKEN` — app should start and log warning instead of crashing
2. **Test `/health` endpoint**: Should return `{"status": "healthy"}` regardless of HA state
3. **Test `/health/ha` endpoint**: Should return `{"ha_connected": false}` when HA is unreachable, `{"ha_connected": true}` when reachable
4. **Test API routes**: Verify `/api/ha/status`, `/api/ha/entities`, etc. still work when HA is connected
5. **Run existing tests**: `cd backend && python -m pytest` (if test suite exists)

## Risks & Tradeoffs

- **Risk**: If HA connection fails mid-runtime (not just at startup), services won't auto-reconnect — this is a known limitation that can be addressed in a future enhancement
- **Tradeoff**: Making HA optional means some endpoints (`/api/ha/entities`, `/api/ha/services/call`) will return 400 with "No HA connection configured" instead of crashing the entire app — this is acceptable behavior
- **Risk**: The try/except block catches all exceptions, which could mask bugs in service initialization. Mitigation: log detailed warnings so issues are still visible

## Open Questions

1. Should we add a retry loop (N attempts with backoff) before giving up on HA connection at startup? Currently the HAAPI class already has 3 retries built-in (`max_retries = 3`), so this may be sufficient.
2. Should the `/health/ha` endpoint be included in the main `/health` response, or kept separate? Keeping it separate avoids blocking the health check on HA connectivity.

## Execution Order

1. Fix `backend/app/main.py` (issue #53)
2. Test locally with docker compose
3. Commit and push
4. Close all 3 issues via `gh issue close`

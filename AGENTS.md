# HA Dashboard Builder — Agent Guide

## Project structure

Two packages in one repo:
- `backend/` — Python FastAPI (uv, SQLAlchemy, httpx)
- `frontend/` — React 18 + Vite + TypeScript (npm, dnd-kit, Tailwind)

Root `conftest.py` adds project root to `sys.path` for pytest.

## Commands

```bash
# Backend (run from backend/ or use workdir)
uv sync                          # install deps
uv run uvicorn app.main:app --reload   # dev server on :8000
uv run pytest -v                 # all tests (56 passing)
uv run pytest tests/test_file.py --tb=short
uv run flake8 app/ tests/        # lint
uv run black --check app/ tests/ # format check

# Frontend (run from frontend/ or use workdir)
npm install
npm run dev                      # Vite dev server on :3000 (proxies /api → :8000)
npm run build                    # tsc && vite build
```

## Key architecture facts

- **Two SQLite DBs**: `ha_dashboard.db` (SQLAlchemy ORM: Page/Card models) and `ha_entities.db` (raw sqlite3 for entity cache with state_history table).
- **Global services in `main.py`**: `ha_client`, `discovery_service`, `cache_refresh_service`, `event_listener` are module-level globals initialized in the FastAPI `lifespan` hook.
- **HA API routes** at `/api/ha/*` (routes.py), **dashboard CRUD** at `/api/v1/*` (dashboard_routes.py), **WebSocket** at `/api/ws/entities` (websocket.py).
- **Frontend API mismatch**: `frontend/src/services/api.ts` calls `/api/v1/states` and `/api/v1/events/stream` — these endpoints **don't exist** in the backend. Use `/api/ha/entities` instead. Known issue, not yet fixed.
- **Frontend uses `@/` path alias** mapping to `./src/`.
- **Bulk card save**: `PUT /api/v1/dashboards/{id}/cards` is atomic — the frontend `useDashboard` hook sends the full card list. Cards not in the request are deleted.
- **LLM config stubs** exist in `backend/app/config.py`: `OLLAMA_BASE_URL`, `LMSTUDIO_BASE_URL`, `DEFAULT_LLM_MODEL` — no functional LLM code yet.
- **LLM plan** in `.hermes/hermes_plan.md`: backend-agent pattern, chat sidebar tab, REST-first, full Lovelace card type support.

## Repo-specific conventions

- Python: `flake8` (max-line-length=120, ignore E501/W503/E203), `black` with target py311. No mypy in CI (flake8 + black only).
- TypeScript: `strict: true`, `noUnusedLocals`, `noUnusedParameters` — these will fail `npm run build`.
- Frontend uses native `fetch`, no axios. Auth token from `localStorage` sent as Bearer header.
- Entity cache uses raw sqlite3 (not SQLAlchemy). Dashboard storage uses SQLAlchemy ORM.
- CORS allows `http://localhost:3000` by default.
- `uv` is the Python package manager (not pip). Lockfile is `uv.lock`.

## Test infra

- `backend/tests/conftest.py` deletes `ha_dashboard.db` before test session, then calls `init_db()`.
- HA API is globally monkeypatched with a `MagicMock` — no real HA instance needed.
- `asyncio_mode = auto` in pytest config. Use `async def` for async tests directly.

## LLM & settings plan (from `.hermes/hermes_plan.md`)

Build order:
1. Backend `LLMService` + `POST /api/chat/messages` route + settings CRUD
2. Settings UI modal (4 tabs: HA, LLM, Editor, Export) in SQLite `Setting` model
3. Chat UI as tab in existing EntitySidebar
4. Full Lovelace card type schemas
5. Polish (WebSocket streaming, bulk previews, error recovery)
6. Fix known API mismatches and Docker frontend wiring

## Sidebar component architecture

`EntitySidebar` is a fixed-width sidebar (`w-72`) on desktop. Mobile uses `MobileSidebar` as a bottom drawer. The chat tab should integrate into the existing `EntitySidebar` component — it shares the same responsive breakpoints (`hidden sm:block`).

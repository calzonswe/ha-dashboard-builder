# HA Dashboard Builder

A visual dashboard builder for Home Assistant. Build custom dashboards with drag-and-drop widgets that display and control your smart home entities — lights, sensors, switches, climate devices, and more.

The project consists of:
- **Backend** — FastAPI REST API + WebSocket server (Python 3.11+)
- **Frontend** — React SPA with a visual canvas builder (TypeScript)

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Browser    │◄────────│  FastAPI Backend  │────────►│ Home Assistant│
│  React SPA   │ WebSocket│                  │ HTTP/WS   │              │
│  (port 3000) │ REST     │                  │           │              │
└──────────────┘         └──────────────────┘         └──────────────┘
                              │        │
                         SQLite DB    Entity Cache
                         (dashboards)  (entities + states)
```

### Components

| Component | Tech | Port | Description |
|-----------|------|------|-------------|
| **Backend API** | FastAPI (Python 3.11+) | 8000 | REST endpoints, WebSocket server, entity discovery |
| **Frontend** | React + Vite + TypeScript | 3000 | Visual dashboard builder canvas |
| **Database** | SQLite | — | Dashboard & widget persistence (`ha_dashboard.db`) |
| **Entity Cache** | SQLite | — | Cached HA entities and state history (`cache.db`) |

## Backend

### Tech Stack

- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy 2.x with declarative models
- **Database**: SQLite (file-based, no external DB required)
- **Settings**: Pydantic `BaseSettings` — reads from `.env` and environment variables
- **HTTP Client**: `httpx` for Home Assistant REST API calls
- **WebSocket**: FastAPI built-in WebSocket support with custom connection manager

### Directory Structure

```
backend/
├── app/
│   ├── main.py              # Application entry point, lifespan, router registration
│   ├── config.py            # Settings (env vars + .env file)
│   ├── database.py          # SQLAlchemy models: Page, Card, Entity; DB init & session
│   └── api/
│       ├── routes.py        # HA connection, entity discovery, search, service calls
│       ├── dashboard_routes.py  # Dashboard CRUD (pages + widgets/cards)
│       ├── websocket.py     # WebSocket endpoint + ConnectionManager
│       └── schemas.py       # Pydantic request/response models
├── tests/                   # pytest test suite
├── pyproject.toml           # Dependencies & build config (uv)
└── uv.lock                  # Lock file for reproducible builds
```

### API Endpoints

All endpoints are documented in the Swagger UI at `http://localhost:8000/docs`.

#### Home Assistant Integration (`/api/ha/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ha/status` | Connection status to HA instance |
| POST | `/api/ha/connect` | Connect to a Home Assistant instance (host, port, token) |
| POST | `/api/ha/discover` | Discover and cache all entities from HA |
| GET | `/api/ha/entities` | List cached entities (filterable by domain, area, device) |
| GET | `/api/ha/entities/{entity_id}` | Get a single entity's cached state |
| POST | `/api/ha/search` | Search entities by name or ID substring |
| POST | `/api/ha/services/{domain}/{service}` | Call a Home Assistant service |

#### Dashboards (`/api/v1/dashboards`)

Dashboard CRUD for the visual builder. Each dashboard is a "page" containing widgets (cards).

**Dashboards:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboards` | List all dashboards |
| POST | `/api/v1/dashboards` | Create a new dashboard |
| GET | `/api/v1/dashboards/{id}` | Get a dashboard with all its widgets |
| PUT | `/api/v1/dashboards/{id}` | Update dashboard name/description |
| DELETE | `/api/v1/dashboards/{id}` | Delete dashboard and all its widgets |

**Widgets (Cards):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboards/{dashboard_id}/widgets` | List all widgets on a dashboard |
| POST | `/api/v1/dashboards/{dashboard_id}/widgets` | Add a widget to a dashboard |
| PUT | `/api/v1/dashboards/{dashboard_id}/widgets/{widget_id}` | Update a single widget (partial) |
| DELETE | `/api/v1/dashboards/{dashboard_id}/widgets/{widget_id}` | Remove a single widget |
| PUT | `/api/v1/dashboards/{dashboard_id}/cards` | **Bulk replace** all cards atomically (primary save endpoint for drag-and-drop builder) |

#### WebSocket (`/ws/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ws/status` | Active connection count and status |
| WS | `/ws/entities` | Real-time entity state updates. Subscribe with `subscribe:entity_id`, unsubscribe with `unsubscribe:entity_id`. Ping/pong keepalive supported. |

#### Health & Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (used by Docker healthcheck) |
| GET | `/docs` | Swagger UI interactive API docs |
| GET | `/openapi.json` | OpenAPI 3.1 schema |

### Database Models

**Page** (`pages` table) — A dashboard page:
- `id`, `name`, `description`, `created_at`, `updated_at`

**Card** (`cards` table) — A widget on a dashboard page:
- `id`, `page_id` (FK → pages), `card_type`, `title`, `entity_id`, `config` (JSON), `x`, `y`, `width`, `height`

**Entity** (`entities` table) — Cached HA entity state:
- `id` (entity_id PK), `name`, `state`, `attributes` (JSON), `last_updated`

### Configuration

Settings are loaded from `.env` and environment variables via Pydantic `BaseSettings`.

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `"HA Dashboard Builder"` | Application display name |
| `DEBUG` | `True` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./ha_dashboard.db` | SQLAlchemy database URL |
| `HA_HOST` | `"localhost"` | Home Assistant hostname/IP |
| `HA_PORT` | `8123` | Home Assistant port |
| `HA_ACCESS_TOKEN` | *(empty)* | Long-lived access token for HA API auth |
| `WS_POLL_INTERVAL` | `5.0` | WebSocket state poll interval (seconds) |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS allowed origins |

### Running the Backend Locally

```bash
cd backend
uv sync                          # Install dependencies from pyproject.toml
cp .env.example .env             # Create config file (edit HA credentials)
uv run uvicorn app.main:app --reload  # Start dev server on port 8000
```

## Frontend

### Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: CSS modules / custom properties (dark theme)
- **State Management**: React hooks + context
- **HTTP Client**: Native `fetch` API with Bearer token auth

### Directory Structure

```
frontend/
├── src/
│   ├── main.tsx                 # App entry point, router setup
│   ├── components/              # Reusable UI components (buttons, modals, cards)
│   ├── pages/                   # Page views: DashboardBuilder, Login, Entities
│   ├── services/                # API client layer (api.ts, websocket.ts)
│   ├── types/                   # TypeScript interfaces (api.ts)
│   └── App.tsx                  # Root component with routing
├── public/                      # Static assets
├── vite.config.ts               # Vite config with dev proxy to backend
├── nginx.conf                   # Production Nginx config (SPA + API proxy)
├── Dockerfile.frontend          # Multi-stage build for production
└── package.json                 # Dependencies & scripts
```

### Development Mode

```bash
cd frontend
npm install                      # Install dependencies
npm run dev                      # Start Vite dev server on port 3000
```

The Vite dev server proxies `/api` requests to `http://localhost:8000` (backend). WebSocket connections at `/ws` are also proxied.

### Production Build

```bash
cd frontend
npm run build                    # Build for production
```

The Dockerfile (`Dockerfile.frontend`) builds the React app and serves it with Nginx, including API proxy configuration so the frontend can reach the backend without CORS issues.

## Docker Deployment

### Quick Start

```bash
# Set your HA credentials in .env (or pass as env vars)
export HA_TOKEN="your-long-lived-access-token"

# Build and start
docker compose up --build -d

# Check health
curl http://localhost:8000/health
# {"status":"healthy"}

# View Swagger docs
open http://localhost:8000/docs
```

### Docker Compose Services

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `ha-dashboard-api` | Custom (Python 3.11) | 8000 | FastAPI backend with entity discovery, caching, WebSocket |

### Dockerfile Details

The backend Dockerfile:
- Uses Python 3.11 slim base image
- Instails uv for dependency management
- Copies `backend/app/` into `/app/app/` (correct path mapping)
- Runs `uv sync --frozen` to install from `uv.lock`
- Starts with `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Healthcheck hits `/health` endpoint

### Environment Variables in Docker Compose

The compose file passes HA connection settings and cache configuration via environment variables. The SQLite cache file (`cache.db`) is mounted as a volume for persistence across restarts.

## Authentication

All HA API endpoints require a **Long-Lived Access Token** from your Home Assistant instance:

1. Open HA → Settings → Security
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token", give it a name, and copy the token
4. Set `HA_ACCESS_TOKEN` in `.env` or as an environment variable

The frontend stores this token in `localStorage` and sends it as a Bearer token in all API requests.

## Entity Discovery & Caching

### How It Works

1. **Connect** — Provide HA host, port, and access token via `/api/ha/connect`
2. **Discover** — Call `/api/ha/discover` to fetch all entity states from HA
3. **Enrich** — States are enriched with device metadata (area, manufacturer, model)
4. **Cache** — Results are stored in SQLite (`cache.db`) for fast lookups and persistence across restarts
5. **Poll** — A background service refreshes the cache every 60 seconds by default

### Cache Schema

The entity cache uses two tables:

- `entities` — Current state of each HA entity (entity_id, name, domain, type, state, attributes, area, device)
- `state_history` — State change log with timestamps for historical tracking

### Filtering & Search

Entities can be queried by:
- **Domain** — `light`, `sensor`, `switch`, `climate`, etc.
- **Area/Room** — "Living Room", "Kitchen", etc.
- **Device** — Filtered by device ID
- **Entity Type** — `bulb`, `thermostat`, `binary_sensor`, etc.
- **Current State** — e.g., filter all entities that are `"on"`
- **Full-text search** — Search across entity names and IDs (case-insensitive)

## Development Workflow

### Setting Up Locally

```bash
# 1. Clone the repo
git clone https://github.com/calzonswe/ha-dashboard-builder.git
cd ha-dashboard-builder

# 2. Backend setup
cd backend
uv sync                          # Install deps from pyproject.toml + uv.lock
cp .env.example .env             # Edit HA credentials
uv run uvicorn app.main:app --reload   # Start on port 8000

# 3. Frontend setup (in another terminal)
cd ../frontend
npm install
npm run dev                      # Start on port 3000 with API proxy
```

### Running Tests

```bash
cd backend
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest tests/test_api.py  # Specific test file
```

### Adding New Endpoints

1. Define Pydantic schemas in `backend/app/api/schemas.py`
2. Create route functions in the appropriate router file (`routes.py`, `dashboard_routes.py`)
3. Register the router in `backend/app/main.py` if using a new file
4. Add tests in `backend/tests/`

### Adding New Frontend Components

1. Create component files in `frontend/src/components/` or `frontend/src/pages/`
2. Import and use in your page/view components
3. Use the API client functions from `frontend/src/services/api.ts` for backend calls

## Known Issues & TODOs

- **Frontend-backend API mismatch** — The frontend's `api.ts` references endpoints (`/api/states`, `/api/events/stream`) that don't exist in the current backend. These need to be either implemented on the backend or the frontend updated to match existing routes.
- **HA connection not configured** — Without a valid HA instance and token, entity discovery will fail. The app handles this gracefully but shows "connection refused" errors until configured.
- **Frontend Docker service** — A `Dockerfile.frontend` exists but is not wired into `docker-compose.yml`. Adding it would enable full-stack container deployment.

## License

MIT License

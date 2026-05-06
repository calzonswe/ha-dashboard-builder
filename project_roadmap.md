# HA Dashboard Builder - Project Roadmap

### Phase 1: Backend Stabilization & Dockerization ✅ COMPLETE
**Goal:** A reliable, containerized API that passes all tests and is ready for production deployment.

#### Epic 1.1: Test Fixes & Validation ✅ DONE
- [x] **Activity 1.1.1:** Fix `conftest.py` to add project root to `sys.path` so imports resolve correctly.
- [x] **Activity 1.1.2:** Update `test_ha_client.py` mocks to handle async context managers (`async with`) properly using `AsyncMock`.
- [x] **Activity 1.1.3:** Fix `test_websocket.py` streaming mock (ensure generator yields correctly).
- [x] **Activity 1.1.4:** Run full test suite (`pytest -v`) and verify 100% pass rate — **56/56 tests passing**.

#### Epic 1.2: API Hardening & Security ✅ DONE
- [x] **Activity 1.2.1:** Migrate Pydantic `class Config` to `model_config = ConfigDict()` (Pydantic v2).
- [x] **Activity 1.2.2:** Implement global exception handler middleware (catch raw exceptions, return JSON error responses instead of 500 traces).
- [x] **Activity 1.2.3:** Add Bearer Token authentication (simple API key check via header) to protect endpoints.
- [ ] **Activity 1.2.4:** Implement rate limiting (using `slowapi` or similar) to prevent HA overload from rapid polling — *deferred to Phase 3*.

#### Epic 1.3: Dockerization & Deployment Configs ✅ DONE
- [x] **Activity 1.3.1:** Create multi-stage `Dockerfile` (builder stage with `uv`, runtime stage with slim Python image).
- [x] **Activity 1.3.2:** Create `docker-compose.yml` with a working example connecting to a local HA instance.
- [x] **Activity 1.3.3:** Add `.env.example` documenting all required environment variables (`HA_URL`, `HA_TOKEN`, etc.).

**Phase 1 Summary:** All critical fixes complete, test suite stable (56/56 passing), API hardened with auth + exception handling, Docker deployment ready.

---

## Phase 2: Frontend MVP (Visual Builder)
**Goal:** A React-based drag-and-drop interface to design Home Assistant dashboards visually.

### Epic 2.1: Project Setup & Architecture
- [ ] **Activity 2.1.1:** Scaffold React + TypeScript frontend using Vite (`npm create vite@latest`).
- [ ] **Activity 2.1.2:** Install core dependencies: `dnd-kit` (drag-and-drop), `lucide-react` (icons), `clsx`/`tailwind` (styling).
- [ ] **Activity 2.1.3:** Configure Tailwind CSS and set up the base layout structure (Sidebar, Canvas, Properties Panel).

### Epic 2.2: Dashboard Canvas & Drag-and-Drop
- [ ] **Activity 2.2.1:** Implement the main Grid/Canvas component using `dnd-kit` for drag-and-drop interactions.
- [ ] **Activity 2.2.2:** Create individual "Card" components that can be dragged, resized, and reordered on the canvas.
- [ ] **Activity 2.2.3:** Manage dashboard state (layout JSON) in React context or Zustand store.

### Epic 2.3: Entity Browser & Card Editor
- [ ] **Activity 2.3.1:** Build a searchable sidebar component to browse/filter Home Assistant entities (lights, sensors, etc.).
- [ ] **Activity 2.3.2:** Implement "Click-to-add" logic that drops selected entities onto the canvas as new cards.
- [ ] **Activity 2.3.3:** Create a Properties Panel/Modal to edit card settings (entity_id, name, icon, color) when a card is clicked.

### Epic 2.4: Backend Integration
- [ ] **Activity 2.4.1:** Connect frontend API client (`fetch` or `axios`) to the backend endpoints for entity discovery and state fetching.
- [ ] **Activity 2.4.2:** Implement "Save Dashboard" functionality (POST layout JSON to backend).
- [ ] **Activity 2.4.3:** Implement "Load Dashboard" functionality (GET saved layouts from backend).

---

## Phase 3: Polish, Export & Release
**Goal:** Make the product usable by end-users with export capabilities and documentation.

### Epic 3.1: YAML Generation & Export
- [ ] **Activity 3.1.1:** Implement backend logic to convert JSON dashboard layout into Home Assistant Lovelace YAML format.
- [ ] **Activity 3.1.2:** Add "Export as YAML" button in the frontend that triggers a file download of the generated config.
- [ ] **Activity 3.1.3:** Create a "Live Preview" mode in the frontend that renders actual HA cards using `home-assistant-webcomponents`.

### Epic 3.2: LLM Assistant Integration (Optional but Recommended)
- [ ] **Activity 3.2.1:** Add Ollama/LMStudio client module to the backend for local AI inference.
- [ ] **Activity 3.2.2:** Create a chat interface in the frontend sidebar where users can describe card settings via natural language.
- [ ] **Activity 3.2.3:** Implement prompt engineering to parse LLM responses into valid card configuration objects.

### Epic 3.3: Documentation & Release
- [ ] **Activity 3.3.1:** Write comprehensive `README.md` with installation instructions, feature list, and usage examples.
- [ ] **Activity 3.3.2:** Create GitHub Actions workflow for automated testing and Docker image publishing on push/tag.
- [ ] **Activity 3.3.3:** Tag the first stable release (`v1.0.0`) and create a GitHub Release with changelog.

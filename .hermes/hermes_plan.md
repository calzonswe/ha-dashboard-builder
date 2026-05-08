# HA Dashboard Builder — LLM + Settings GUI Plan

## Architecture
- **Backend-agent pattern**: Python/FastAPI `LLMService` with provider abstraction
- **Chat sidebar**: Tab in existing entity sidebar
- **REST-first**: `POST /api/chat/messages` + session management; WebSocket streaming later
- **Settings**: SQLite-backed key-value settings model

## LLM Capabilities
- Card-level + full dashboard generation via structured JSON output
- Full Lovelace card type support with schema validation
- Hybrid context: full entity catalog + entity lookup tool calls
- Selection-aware context (selected cards → LLM prompt)

## Response Handling
- Validate LLM JSON server-side; retry with error on malformed output
- Auto-apply simple operations (undo toast), preview for bulk ops
- Warn on hallucinated entities, reject invalid card params

## Settings UI
- Modal with 4 tabs: HA, LLM, Editor, Export
- Triggered from gear icon in builder header
- Persisted in SQLite via key-value `Setting` model

## Build Order
1. Backend LLM service + chat API
2. Settings UI (modal + API integration)
3. Chat UI (sidebar tab, input, context, undo)
4. Full card type schemas + validation
5. Polish (streaming, previews, error recovery)
6. Fix known issues (API mismatches, Docker)

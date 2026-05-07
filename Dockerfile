# ---------------------------------------------------------------------------
# Multi-stage Dockerfile for HA Dashboard Builder (FastAPI + Home Assistant)
# ---------------------------------------------------------------------------
# Stage 1: Build dependencies with uv for speed
# Stage 2: Minimal runtime image

# ---- Builder stage ----
FROM python:3.11-slim AS builder

RUN pip install --upgrade uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

# ---- Runtime stage ----
FROM python:3.11-slim

LABEL maintainer="ha-dashboard-builder" \
      description="Home Assistant Integration API with real-time state updates"

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source code from backend
COPY backend/app/ ./app/

# Set runtime environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

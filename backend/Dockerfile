# Carenova AI — Backend Dockerfile
# FastAPI + Python 3.12 — port 8004

FROM python:3.12-slim AS base

# Security: run as non-root
RUN groupadd --gid 1001 carenova \
    && useradd --uid 1001 --gid carenova --shell /bin/bash --create-home carenova

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies stage ────────────────────────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Production stage ──────────────────────────────────────────────────────────
FROM base AS production

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=carenova:carenova . .

USER carenova

# Health check — ResilientAI monitors this
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "2", "--log-level", "info"]

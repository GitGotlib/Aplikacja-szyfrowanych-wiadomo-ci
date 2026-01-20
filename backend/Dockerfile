FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for common crypto wheels; keep minimal.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install backend package so `app` is importable regardless of CWD.
# This makes local runs (`uvicorn app.main:app`) deterministic.
COPY backend /app/backend
RUN pip install --no-cache-dir -e /app/backend

# Versioned DB schema (authoritative, auditable)
COPY database /app/database

COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh

# Create non-root user; runtime process will drop privileges via entrypoint.
RUN useradd -r -u 10001 appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

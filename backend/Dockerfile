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

# Application source will live under backend/app
COPY backend/app /app/app

# Non-root runtime
RUN useradd -r -u 10001 appuser
USER 10001

EXPOSE 8000

# Entry point expects FastAPI application at app.main:app (to be implemented later).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

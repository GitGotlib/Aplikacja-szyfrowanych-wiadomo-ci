# Frontend build container (React + Vite + TypeScript).
# This Dockerfile is intentionally limited to build concerns; static serving is handled by NGINX reverse proxy.

FROM node:20-alpine

WORKDIR /app

# Expected frontend structure (to be created when implementing UI):
# - frontend/package.json, frontend/package-lock.json
# - frontend/vite.config.ts, frontend/tsconfig.json
# - frontend/index.html, frontend/src/

# Build stage (will succeed once the above files exist)
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Output directory: /app/dist

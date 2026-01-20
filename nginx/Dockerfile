# NGINX runtime image that serves the frontend static build and proxies /api to backend.

FROM node:20-alpine AS frontend-build
WORKDIR /work

COPY frontend/package*.json ./frontend/
WORKDIR /work/frontend
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend/ /work/frontend/
RUN npm run build

FROM nginx:1.25-alpine

# Static frontend
COPY --from=frontend-build /work/frontend/dist /usr/share/nginx/html

# NGINX config and TLS checks
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/nginx.prod.conf /etc/nginx/nginx.prod.conf
COPY nginx/check-certs.sh /etc/nginx/check-certs.sh
RUN chmod 755 /etc/nginx/check-certs.sh

# Runtime behavior:
# - config may be overridden by bind-mount in docker-compose
# - certs are mounted into /etc/nginx/certs
CMD ["/bin/sh", "-c", "sh /etc/nginx/check-certs.sh; exec nginx -g 'daemon off;'" ]

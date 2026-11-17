FROM public.ecr.aws/docker/library/node:24.22.3-bookworm-slim@sha256:0e2646ab57e77b7a384a0cb59b6815b182c77e1f9c3ba36bd8435bd9c4e6680e AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
ARG BACKEND_INTERNAL_ORIGIN=http://backend:8000
ENV BACKEND_INTERNAL_ORIGIN=$BACKEND_INTERNAL_ORIGIN
RUN npm run build

FROM public.ecr.aws/docker/library/node:24.22.3-bookworm-slim@sha256:0e2646ab57e77b7a384a0cb59b6815b182c77e1f9c3ba36bd8435bd9c4e6680e AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
COPY --from=builder --chown=node:node /app/.next/standalone ./
USER node
CMD ["node", "server.js"]

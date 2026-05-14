# NexVest frontend - multi-stage
# -------------------------------
# Stage 1: compilar la SPA con Vite.
# Stage 2: servirla con Caddy + actuar como reverse proxy al backend.

# ---------- Stage 1: build ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Copiamos solo los manifiestos primero para cachear `npm ci`.
COPY package.json package-lock.json* bun.lockb* ./
RUN npm ci

COPY . .

# La SPA habla con el backend bajo /api (mismo dominio, Caddy lo proxea).
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---------- Stage 2: runtime ----------
FROM caddy:2-alpine

# Build del paso anterior.
COPY --from=builder /app/dist /var/www/nexvest

# El Caddyfile se monta como volumen desde compose para que sea editable.
EXPOSE 80 443

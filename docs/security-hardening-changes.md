# Security Hardening & Infrastructure Updates

**Date:** 2026-08-03  
**Scope:** Docker Compose, Caddy reverse proxy, PostgreSQL backup, pgAdmin firewall, secret management

---

## Summary

Centralized all secrets into a root `.env`, added Caddy as the sole public reverse proxy (ports 80/443), introduced automated PostgreSQL backups, created a firewall script to restrict pgAdmin access by IP, and removed hardcoded credentials from all Compose services.

---

## Files Created

| File | Purpose |
|------|---------|
| `.env` | Single source of truth for all secrets (Postgres, pgAdmin, backend, frontend, Caddy) |
| `Caddyfile` | Reverse proxy config with security headers for `api.rentalapp.com` and `rentalapp.com` |
| `scripts/pg-backup.sh` | Daily PostgreSQL dump with 7-day retention |
| `scripts/setup-firewall.sh` | UFW-based IP allow-list for pgAdmin port 5050 |
| `backend/.env.example` | Template for local backend development |
| `backend/.dockerignore` | Prevents `.env` from being baked into Docker images |

---

## Files Modified

### `docker-compose.yml`

- **Removed all hardcoded secrets** — every service now uses `env_file: - .env`
- **Removed exposed ports** for postgres (5433), redis (6380), backend (8000), and frontend (5173/80). Only Caddy (80/443) and pgAdmin (5050) remain exposed to the host.
- **Added `caddy` service** — reverse proxy on ports 80/443 with ACME/TLS support
- **Added `backup` service** — automated PostgreSQL dumps
- **Added Postgres healthcheck** — `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`
- **Backend `depends_on`** — now waits for `service_healthy` (postgres) and `service_started` (redis)
- **Backend command** — added `-d $POSTGRES_DB` to `pg_isready` wait loop to fix FATAL database-not-found errors
- **Backend uvicorn** — added `--proxy-headers` for correct client IP handling behind reverse proxy
- **Frontend build** — added `args: VITE_API_URL: ${VITE_API_URL}` to inject API URL at build time
- **Caddy env injection** — `environment: - CADDY_EMAIL=${CADDY_EMAIL}` so ACME account registers correctly
- **Backup env injection** — `environment: - PGPASSWORD=${POSTGRES_PASSWORD}` so `pg_dump` authenticates non-interactively

### `backend/.env`

- **Emptied** — all secrets moved to root `.env`. Contains only a 2-line comment directing developers to the root `.env`.

### `backend/.env.example`

- **Created** — full template of all backend environment variables for local development outside Docker Compose.

### `backend/.dockerignore`

- **Created** — excludes `.env`, `__pycache__`, `venv`, `*.pyc`, `.DS_Store`, `uploads/` from Docker build context.

### `frontend/Dockerfile`

- **Moved `ARG VITE_API_URL` and `ENV VITE_API_URL=$VITE_API_URL`** inside the `builder` stage (after `FROM node:20-alpine AS builder`). Previously these lines were before the first `FROM`, which Docker rejects in multi-stage builds.

### `frontend/nginx.conf`

- **Unchanged** — still serves SPA fallback and static assets. Caddy handles public traffic; nginx only serves internally on port 80.

---

## Files Unchanged

| File | Reason |
|------|--------|
| `Caddyfile` | Security headers and proxy rules are correct as written |
| `scripts/pg-backup.sh` | Logic is correct once `PGPASSWORD` is injected (fixed in compose) |
| `scripts/setup-firewall.sh` | IP ranges are placeholders; user must edit before running |
| `.gitignore` | Already ignores `.env` and `backend/uploads/` |

---

## Security Headers Added (Caddyfile)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()`
- `-Server` (removes server info)
- `request_body max_size 10MB` (limits payload size)

---

## Required Manual Steps

1. **Edit `Caddyfile`** — replace `api.rentalapp.com` and `rentalapp.com` with your actual domain(s)
2. **Edit `scripts/setup-firewall.sh`** — replace the placeholder IP ranges (`192.168.1.0/24`, `10.0.0.0/8`) with your allowed IPs, then run:
   ```bash
   sudo bash scripts/setup-firewall.sh
   ```
3. **Free port 80** — another Compose project (`notification-nginx`) is currently bound to `0.0.0.0:80`. Stop it before starting the rental app:
   ```bash
   docker compose -f /path/to/notification/docker-compose.yml down
   ```
4. **Start the stack:**
   ```bash
   docker compose up -d --build
   ```

---

## Verification

```bash
# Check all services are running
docker compose ps

# Check Caddy logs for TLS provisioning
docker compose logs caddy

# Check backup service
docker compose logs backup

# Verify firewall rules
sudo ufw status | grep 5050
```

# Local Development vs Production Workflow

## Overview

To keep development fast and deployments reliable, use **different workflows for your local machine and your production server**.

The goal is simple:

* **Develop locally with Vite** for instant hot reloads.
* **Deploy with Docker + Caddy** for a secure production environment.

---

# Local Development (Laptop)

During development, avoid using Caddy and the production frontend container.

Instead, run only the services your application depends on.

## Start the Backend Services

```bash
docker compose up postgres redis backend
```

This starts:

* PostgreSQL
* Redis
* FastAPI Backend

---

## Start the Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will start the frontend with hot module reloading.

### Local URLs

**Frontend**

```
http://localhost:5173
```

**Backend**

```
http://localhost:8000
```

---

## Frontend Environment Variables

Create a local environment file:

**frontend/.env.local**

```env
VITE_API_URL=http://localhost:8000
```

Every frontend API request will now go directly to your local backend.

Benefits:

* Instant hot reload
* No Docker rebuilds after frontend changes
* Faster debugging
* Simpler workflow

---

# Production (VPS)

The production environment should continue using Docker for every service.

Architecture:

```
Internet
      │
      ▼
   Caddy (HTTPS)
      │
      ├── Frontend (Nginx)
      └── Backend (FastAPI)
                │
                ▼
        PostgreSQL + Redis
```

Production API URL:

```env
VITE_API_URL=https://api.alphaone.africa
```

---

# Environment Configuration

Instead of commenting and uncommenting code, maintain separate environment files.

## Local Development

**frontend/.env.local**

```env
VITE_API_URL=http://localhost:8000
```

## Production

**frontend/.env.production**

```env
VITE_API_URL=https://api.alphaone.africa
```

Vite automatically selects the correct environment when running:

Development:

```bash
npm run dev
```

Production build:

```bash
npm run build
```

No code changes are required.

---

# Deployment Workflow

Once development is complete:

Build production images:

```bash
docker compose build
```

Start production containers:

```bash
docker compose up -d
```

Or, if deploying through Git:

1. Commit changes
2. Push to GitHub
3. Pull on the VPS
4. Rebuild and restart Docker

---

# Recommended Local Stack

```
React (Vite)
http://localhost:5173
        │
        ▼
FastAPI
http://localhost:8000
        │
        ▼
PostgreSQL + Redis
```

---

# Recommended Production Stack

```
Internet
      │
      ▼
Caddy (HTTPS)
      │
      ├── Frontend (Nginx)
      └── Backend (FastAPI)
                │
                ▼
        PostgreSQL + Redis
```

---

# Services Needed During Development

| Service         |        Local        | Production |
| --------------- | :-----------------: | :--------: |
| React (Vite)    |          ✅          |      ❌     |
| Frontend Nginx  |          ❌          |      ✅     |
| FastAPI Backend |          ✅          |      ✅     |
| PostgreSQL      |          ✅          |      ✅     |
| Redis           |          ✅          |      ✅     |
| Docker          | Optional (Frontend) |      ✅     |
| Caddy           |          ❌          |      ✅     |
| HTTPS           |          ❌          |      ✅     |

---

# Recommended Workflow

### Local Development

```text
Edit Code
      │
      ▼
Save File
      │
      ▼
Vite Hot Reload
      │
      ▼
Test Immediately
```

### Production Deployment

```text
Commit Changes
      │
      ▼
Push to GitHub
      │
      ▼
Pull on VPS
      │
      ▼
docker compose build
      │
      ▼
docker compose up -d
```

---

# Guiding Principle

Keep local development as lightweight and fast as possible.

* Use **Vite** for development.
* Use **Docker** for backend services.
* Reserve **Docker + Nginx + Caddy + HTTPS** for production deployments.

This approach minimizes development overhead while keeping the production environment secure, reproducible, and easy to deploy.

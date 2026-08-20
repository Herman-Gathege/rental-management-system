# 🏢 Rental Property Management Platform

A full-stack multi-tenant SaaS platform for managing rental properties, tenants, staff, and finances.

This repository contains the entire development environment:

- React frontend  
- FastAPI backend  
- PostgreSQL database  
- Redis  
- pgAdmin  
- Docker orchestration  

👉 Everything runs with one command.

---

## ✨ Tech Stack

### Frontend
- React + Vite  
- Context API for auth  
- Modular feature architecture  
- Nginx (production container)  

### Backend
- FastAPI  
- SQLAlchemy  
- Alembic migrations  
- JWT Authentication (Access + Refresh)  
- Redis (token + background tasks ready)  
- Role Based Access Control  

### Infrastructure
- Docker + Docker Compose  
- PostgreSQL 15  
- Redis 7  
- pgAdmin 4  
- Nginx reverse proxy  

---

## 📦 Repository Structure
Rental-Property-Management-Tool/
│
├── backend/ → FastAPI API
├── frontend/ → React Vite app
├── docker-compose.yml
└── README.md


---

## 🚀 QUICK START (ONE COMMAND)

This project is Docker-first.  
You do **NOT** need Python, Node, or Postgres installed locally.

### 1️⃣ Clone repo

```bash
git clone <repo-url>
cd Rental-Property-Management-Tool
```

### 2️⃣ Start the entire platform

```bash
docker compose up --build
```

⏳ First startup may take several minutes.

### 🌐 Access the Apps

Once containers finish booting:

Service	URL
Frontend	http://localhost

Backend API	http://localhost:8000

Swagger Docs	http://localhost:8000/docs

pgAdmin	http://localhost:5050
pgAdmin login
Email: admin@admin.com
Password: admin
🧠 What Happens Automatically

### When Docker starts:

PostgreSQL container boots
Backend waits for DB readiness
Alembic migrations run automatically
Roles are seeded automatically
FastAPI starts
React app is built and served via Nginx

### 👉 running manual migrations
```bash
cd backend
change postgres url to local host

alembic revision --autogenerate -m "your message here"
alembic upgrade head

go back to root dir
change postgres url back
docker compose up --build
sudo systemctl start docker
docker compose up --build --force-recreate

```bash server commands below:

ssh webloom@165.245.251.183
cd /opt/webloom/rental-management-system

git pull
docker compose up -d --build

nano .env
                            ```

### 🔑 Default Architecture Ports
Container	Internal Port	Host Port
frontend (nginx)	80	5173
backend (FastAPI)	8000	8000
postgres	5432	5433
redis	6379	6380
pgadmin	80	5050
🧪 Verifying Everything Works
Backend health check

Open:
http://localhost:8000/docs

You should see Swagger UI.

Frontend check

Open:
http://localhost

You should see the React app.

🗄️ Database Connection (pgAdmin)

Inside pgAdmin create a server:

Host: postgres
Port: 5432
User: rental_user
Password: rental_pass
Database: rental_db

### ⚠️ Important: host is postgres (Docker network), not localhost.

🔐 Authentication Overview

Implemented features:

Registration
Login
JWT Access tokens
Refresh tokens stored in DB
Password reset flow
Role Based Access Control

Supported Roles

### Role	Description

LANDLORD	- Portfolio owner
PROPERTY_MANAGER - Manages properties
FINANCE -	Accounting team
TENANT -	Rent payer
SYSTEM -	Automations

### 🛠️ Development Workflow

Start environment
```bash
docker compose up

Stop environment

docker compose down

Reset database completely

docker compose down -v
docker compose up --build
⚠️ This deletes all data and recreates the DB from scratch.
```

### 🐛 Debugging Guide
Backend not connecting to Postgres
```bash
docker compose logs backend
```
You should see:

Postgres is ready!
Running upgrade...
Uvicorn running on http://0.0.0.0:8000

Frontend not loading
```bash
docker compose down
docker compose up --build
```

Port already in use
```bash
sudo lsof -i :5432
```
Stop local Postgres if running.

### Redis warning about memory overcommit

Linux only — run once:
```bash
sudo sysctl vm.overcommit_memory=1
```

🔄 Running Backend Commands Manually

Enter backend container
```bash
docker compose exec backend bash
```

Run migrations manually
```bash
alembic upgrade head
```
Seed roles manually
```bash
python -m app.db.seed_roles
```

### 🎨 Frontend Architecture Overview
src/
├── api/              → API clients
├── context/          → Auth state
├── features/
│   ├── auth/
│   ├── dashboard/
│   └── superadmin/
├── routes/           → Routing + guards
├── components/       → Shared UI
└── styles/           → Global CSS

### 👉 The frontend is feature-based, not page-based.

### 👩‍💻 Adding a New Developer
```bash
git clone <repo>
cd Rental-Property-Management-Tool
docker compose up --build
```

Open:
http://localhost

🎉 Ready to code.

### 📌 Current Development Stage
✅ Sprint 1 completed
Auth system
Roles
Docker environment
Frontend scaffolding

🔜 Next
Organization bootstrap
User invitations
Property + unit models

### 🤝 Contributing
Create feature branch
Run app with Docker
Commit changes
Open Pull Request
💡 Final Note

#### This README will save future-you hours of setup pain 😄
# 🏢 Rental Property Management System (Backend)

A multi-tenant SaaS backend for managing rental properties, tenants, leases, and financial operations. Built with **FastAPI**, **PostgreSQL**, and **JWT-based authentication**.

---

# 🚀 Tech Stack

* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Migrations:** Alembic
* **Auth:** JWT (Access + Refresh Tokens)
* **Storage:** AWS S3 (stubbed for now)
* **Email:** SendGrid (stubbed for now)

---

# 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       └── auth.py
│   ├── core/
│   │   ├── config.py
│   │   ├── jwt.py
│   │   ├── roles.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   ├── deps.py
│   │   ├── session.py
│   │   └── seed_roles.py
│   ├── models/
│   │   ├── organization.py
│   │   ├── role.py
│   │   └── users.py
│   ├── schemas/
│   │   └── user.py
│   ├── services/
│   │   ├── email_service.py
│   │   └── s3_service.py
│   └── main.py
```

---

# ⚙️ Setup Instructions

## 1️⃣ Clone Repository

```
git clone <your-repo-url>
cd Rental-Property-Management-Tool/backend
```

---

## 2️⃣ Create Virtual Environment

```
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

## 4️⃣ Environment Variables

Create a `.env` file in `/backend`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/rental_db
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Optional (can be fake for dev)
SENDGRID_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_BUCKET_NAME=your_bucket
```

---

## 5️⃣ Run Database Migrations

```
alembic upgrade head
```

---

## 6️⃣ Seed Roles

```
python -m app.db.seed_roles
```

---

## 7️⃣ Start Server

```
uvicorn app.main:app --reload
```

---

## 8️⃣ Access API Docs

```
http://127.0.0.1:8000/docs
```

---

# 🔐 Authentication System

## Features Implemented

* User Registration
* Login (JWT)
* Access Tokens (short-lived)
* Refresh Tokens (long-lived)
* Protected Routes
* Role-Based Access Control (RBAC)
* Password Reset (email-based)

---

# 🔑 Auth Flow

### Register

```
POST /auth/register
```

### Login

```
POST /auth/login
```

Returns:

* access_token
* refresh_token

---

### Get Current User

```
GET /auth/me
Authorization: Bearer <access_token>
```

---

### Refresh Token

```
POST /auth/refresh?token=<refresh_token>
```

---

### Forgot Password

```
POST /auth/forgot-password?email=<email>
```

---

### Reset Password

```
POST /auth/reset-password?token=<token>&new_password=<password>
```

---

# 🛡️ RBAC (Roles)

Roles supported:

* LANDLORD
* PROPERTY_MANAGER
* FINANCE
* TENANT

---

## Role Protection Example

```
Depends(require_role("LANDLORD"))
```

---

# 🧪 Testing with cURL

### Login

```
curl -X POST "http://127.0.0.1:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "admin@test.com",
  "password": "123456"
}'
```

---

### Protected Route

```
curl -X GET "http://127.0.0.1:8000/auth/me" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### Refresh Token

```
curl -X POST "http://127.0.0.1:8000/auth/refresh?token=YOUR_REFRESH_TOKEN"
```

---

# ⚠️ Common Issues

### Invalid Token

* Ensure `Authorization: Bearer <token>` format
* Do NOT include refresh token in header

---

### Migration Errors

* Ensure DB is running
* Check `DATABASE_URL`

---

### 422 Errors

* Ensure correct request format (JSON vs form)

---

# 🧠 Development Notes

* Multi-tenant system via `organization_id`
* Future: property-level isolation
* External services (email/S3) are stubbed for dev
* Designed for scalability (10k+ units)

---

# 📌 Next Steps (Sprint 2)

* Organization switching
* Property & Unit models
* Tenant onboarding
* Lease management

---

# 🤝 Contributing

1. Fork repo
2. Create feature branch
3. Run migrations
4. Test endpoints
5. Submit PR

---

# 📄 License

MIT License

# Fitness Studio Booking API

A production-quality REST API for managing fitness class schedules and bookings. Built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

## What's in this project

| Concern | Implementation |
|---|---|
| Authentication | JWT (HS256) via `python-jose` + `passlib/bcrypt` |
| Authorization | Role-based access control — `user` and `admin` roles |
| Database | PostgreSQL via SQLAlchemy ORM |
| Race condition safety | Atomic `UPDATE WHERE available_slots > 0` — no overselling under concurrent load |
| Idempotency | Client-supplied `idempotency_key` prevents duplicate bookings on retried requests |
| Input validation | Pydantic v2 schemas with field constraints and email validation |
| Structured logging | Timestamped log output to stdout (production-ready) |
| Tests | pytest — 25+ tests covering auth, RBAC, edge cases, and a concurrent booking simulation |
| Containerisation | Docker + Docker Compose for local dev |

---

## Project structure

```
booking-api/
├── app/
│   ├── main.py              # FastAPI app, middleware, router registration
│   ├── database.py          # SQLAlchemy engine, session factory, get_db dependency
│   ├── models.py            # ORM models: User, FitnessClass, Booking
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── seed.py              # Database seeder (sample data + admin user)
│   ├── core/
│   │   ├── config.py        # Settings from environment variables
│   │   ├── security.py      # JWT creation/verification, password hashing, RBAC deps
│   │   └── logging.py       # Structured logger setup
│   └── routers/
│       ├── auth.py          # POST /auth/register, POST /auth/login
│       ├── classes.py       # GET /classes/, GET /classes/{id}, POST, DELETE
│       └── bookings.py      # POST /bookings/, GET /bookings/me, DELETE /bookings/{id}
├── tests/
│   ├── conftest.py          # Fixtures: in-memory SQLite DB, test client, tokens
│   ├── test_auth.py         # Registration and login tests
│   ├── test_classes.py      # Class CRUD and RBAC tests
│   └── test_bookings.py     # Booking flow, idempotency, race condition test
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── alembic.ini
```

---

## Quickstart (Docker)

```bash
git clone https://github.com/Newton-hubs/Booking-API.git
cd Booking-API

# Start PostgreSQL + API
docker-compose up --build

# Seed sample data and an admin user
docker-compose exec api python -m app.seed
```

API is now live at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## Quickstart (local)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env

# Create tables and seed data
python -m app.seed

# Run dev server
uvicorn app.main:app --reload
```

---

## API reference

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Create a user account |
| `POST` | `/auth/login` | None | Get a JWT access token |

### Classes

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/classes/` | None | List all upcoming classes |
| `GET` | `/classes/{id}` | None | Get a single class |
| `POST` | `/classes/` | Admin JWT | Create a new class |
| `DELETE` | `/classes/{id}` | Admin JWT | Delete a class |

### Bookings

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/bookings/` | User JWT | Book a class |
| `GET` | `/bookings/me` | User JWT | List my bookings |
| `DELETE` | `/bookings/{id}` | User JWT | Cancel my booking |

---

## Authentication flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","name":"Jane","password":"password123","role":"user"}'

# 2. Login — copy the access_token from the response
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"password123"}'

# 3. Use the token
curl http://localhost:8000/bookings/me \
  -H "Authorization: Bearer <your_token_here>"
```

---

## Booking a class

```bash
# Basic booking
curl -X POST http://localhost:8000/bookings/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"class_id": 1}'

# With idempotency key (safe to retry)
curl -X POST http://localhost:8000/bookings/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"class_id": 1, "idempotency_key": "my-unique-request-id-001"}'
```

Sending the same `idempotency_key` twice returns the original booking instead of creating a duplicate — safe for network retries.

---

## Admin operations

```bash
# Login as admin (seeded by app.seed)
# Email: admin@fitnessstudio.com  Password: admin1234

curl -X POST http://localhost:8000/classes/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Evening Pilates",
    "scheduled_at": "2026-05-01T18:00:00+05:30",
    "instructor": "Sunita Rao",
    "available_slots": 12
  }'
```

---

## Running tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database — no PostgreSQL required to run the suite.

Key test scenarios covered:
- Registration, login, token validation
- Role enforcement (admin vs user vs unauthenticated)
- Booking happy path, duplicate prevention, full-class rejection
- Idempotency key deduplication
- Slot return on cancellation
- **Concurrent booking race condition** — 5 threads compete for 1 slot; exactly 1 wins

---

## Design decisions

**Atomic slot decrement**: The booking endpoint uses `UPDATE classes SET available_slots = available_slots - 1 WHERE id = ? AND available_slots > 0`. The `rowcount` check ensures that if two concurrent requests both read `available_slots = 1`, only one UPDATE will actually match the `> 0` condition. No application-level lock needed.

**DB-level uniqueness**: A `UniqueConstraint("class_id", "user_id")` on the bookings table acts as a safety net even if two requests pass the application check simultaneously.

**Idempotency**: Clients can supply an `idempotency_key` on booking requests. The server returns the existing booking if the key was already used, making retries safe.

**RBAC via JWT payload**: The role is embedded in the token at login time. `require_role("admin")` is a factory dependency that reads the role from the decoded payload — no extra DB query per request.

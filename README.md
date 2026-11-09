# Language Learning Platform

Language Learning Platform — бул тил үйрөнүүгө арналган backend платформа. Долбоор Duolingo жана Messenger сыяктуу функционалдарды бириктирет.

## Features

- User registration and authentication
- JWT access and refresh tokens
- User roles: User / Admin
- Languages
- Courses
- Lessons
- Exercises
- User progress
- XP system
- Streak system
- Achievements
- Daily challenges
- Leaderboard
- Friends
- Course reviews
- Real-time chat
- WebSocket
- PostgreSQL database
- Redis
- REST API
- Docker / Docker Compose

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Redis
- WebSocket
- Pydantic
- JWT
- Docker
- Docker Compose

## Architecture

The project uses a modular monolith architecture.

```text
Language-learning-platform/
│
├── backend/
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── database/
│   └── config.py
│
├── migrations/
│   └── versions/
│
├── main.py
├── alembic.ini
├── .env
├── .gitignore
└── README.md
```

## Core learning flow

1. Register with `POST /auth/register`. Every account receives its own 5 hearts.
2. Start an active language with `POST /learning-path/languages/{language_id}/start`.
3. Read the unlocked path and lessons from the learning-path endpoints.
4. Submit an exercise through `POST /exercises/{exercise_id}/submit` with a unique `Idempotency-Key` header.
5. Read server-owned progress, XP, streak, leaderboard and hearts. Clients cannot write these values directly.
6. Create a private chat by sending `participant_username`; it always contains exactly two users.

### Exercise idempotency

Every ordinary exercise submission requires a non-empty `Idempotency-Key`. Replaying the same key and payload returns the stored result without repeating XP or a heart penalty. Reusing a key with another answer returns `409 IDEMPOTENCY_CONFLICT`.

```http
POST /exercises/42/submit
Authorization: Bearer <access-token>
Idempotency-Key: lesson-42-attempt-1
Content-Type: application/json

{"answer":"hello"}
```

The response contains `correct`, `score`, `hearts_left`, and `heart_status`. `heart_status.next_heart_at` is an aware UTC timestamp or `null` when hearts are full.

### Hearts and time

- Maximum: 5 hearts per user.
- A wrong first attempt removes one heart. Practice of a completed exercise does not.
- One heart regenerates every 30 minutes from the first loss, capped at 5.
- Durable timestamps are UTC. Daily streak rules use `Asia/Bishkek`; the frontend converts UTC only for display.

### Stable core errors

- `USERNAME_EXISTS`, `EMAIL_EXISTS`, `USER_CONFLICT`
- `LANGUAGE_NOT_FOUND`, `INACTIVE_LANGUAGE`
- `IDEMPOTENCY_KEY_REQUIRED`, `IDEMPOTENCY_CONFLICT`
- `PARTICIPANT_NOT_FOUND`, `SELF_CHAT_NOT_ALLOWED`, `PRIVATE_CHAT_FULL`
- `UNSAFE_AVATAR_EXTENSION`, `INVALID_AVATAR`, `AVATAR_TOO_LARGE`

Core domain errors use `{"detail":{"code":"...","message":"..."}}` where the route exposes a structured error.

## Health endpoints

- `GET /health` is liveness and does not require PostgreSQL or Redis.
- `GET /ready` checks PostgreSQL and Redis with bounded timeouts, returning `200` or `503`.
- Redis rate limiting is fail-open: an outage does not block core requests, while `/ready` reports Redis unavailable.

## Local setup

Provide `DATABASE_URL`, `REDIS_URL`, and a non-empty `SECRET_KEY`, then run:

```bash
python -m pip install -r req.txt
python -m alembic upgrade head
uvicorn main:duolingo --reload
```

Docker services can be started with:

```bash
docker compose -f backend/docker-compose.yml up --build
```

## Tests

```bash
python -m pytest -v
python -m pytest -v -m integration
python -m alembic heads
```

Integration tests create disposable PostgreSQL databases named `llp_test_*`; production data is not used.

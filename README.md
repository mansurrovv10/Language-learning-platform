# Language Learning Platform

Production-oriented FastAPI backend for a Duolingo-style language-learning application with private real-time chat. PostgreSQL is the source of truth. Redis and OpenAI are optional integrations: their outages do not block registration, lessons, deterministic exercises, progress, or chat REST writes.

## Implemented product flow

1. Register with `POST /auth/register`. Each account has an isolated balance of five hearts.
2. Select a language with `POST /learning-path/{language_id}/start`.
3. Load courses, lessons and exercises, including compatible paged/search routes.
4. Submit an answer with `POST /exercises/{exercise_id}/submit` and a unique `Idempotency-Key` header.
5. Read server-owned progress, XP, streak, daily goal, spaced-repetition queue and hearts.
6. Recover a heart with a finite practice session created from the user's difficult exercises.
7. Use private REST/WebSocket chat; Redis Pub/Sub fans events out between application instances when enabled.
8. Optionally request bounded AI explanations, hints, examples, level chat, review tasks or advisory free-text evaluation.

Clients cannot directly write progress, XP, streaks, heart balances or review scheduling.

## Hearts and practice

- Maximum balance: five hearts per user.
- The first wrong attempt on an incomplete exercise removes one heart. An idempotent replay does not remove another one.
- One heart regenerates every 30 minutes from the first loss, up to the maximum. `next_heart_at` is an aware UTC timestamp; the frontend should run only a display countdown and refresh authoritative status from the backend.
- `GET /gamification/hearts/{user_id}` returns current server-calculated status.
- `POST /practice/sessions` creates or returns the active 15-minute session with at most three server-selected review exercises.
- `POST /practice/sessions/{session_id}/complete` accepts every session item. A score of at least 80% awards at most one heart. Replaying the same completion returns the stored result; changing its answers returns `IDEMPOTENCY_CONFLICT`.
- Practice never awards XP and never advances the streak.

## Daily goal and spaced repetition

- `GET /daily-goal` returns the current Bishkek calendar day, target, earned XP, remaining XP and completion state.
- `PUT /daily-goal` accepts `{"target_xp": 20}`; allowed targets are 10–200. Earned XP is always calculated by the server.
- `GET /reviews/due?limit=20&offset=0` returns the authenticated user's due exercises in deterministic order.
- Wrong answers become due immediately. Correct answers advance through 1, 3, 7, 14 and 30-day intervals; a later mistake resets the interval.
- Instants are stored in UTC. Daily boundaries use `Asia/Bishkek` (UTC+6); the next local day begins at 18:00 UTC.

## Pagination and search

The existing list endpoints remain compatible. New `/paged` routes return:

```json
{"items": [], "total": 0, "limit": 20, "offset": 0}
```

Supported discovery routes include `GET /languages/paged`, `GET /courses/paged`, `GET /lessons/paged`, `GET /exercises/paged`, admin-only `GET /users/paged`, and `GET /chats/{chat_id}/messages/paged`. Use `limit` from 1 to 100, non-negative `offset`, and optional normalized `q` where supported. Results have deterministic ordering and authorization is enforced before data is returned.

## Optional AI assistance

OpenAI is optional. Without `OPENAI_API_KEY`, AI endpoints return controlled `503 AI_UNAVAILABLE`; all deterministic learning features continue to work.

- `POST /ai/explain` — concise explanation for an exercise answer.
- `POST /ai/hint` — a hint instructed not to reveal the answer.
- `POST /ai/examples` — one to five examples.
- `POST /ai/chat` — bounded conversation using the learner's selected language and level.
- `POST /ai/review` — tasks based only on server-selected due material.
- `POST /ai/evaluate` — advisory structured evaluation of a free-text answer; it never changes game state.

Requests are authenticated, length-limited, moderated on input and output, limited by a per-user daily quota, sent with `store=false`, and recorded in a minimal usage audit. Expected failures are `AI_UNAVAILABLE` (503), `AI_QUOTA_EXCEEDED` (429), `AI_UNSAFE_INPUT` (400), and `AI_PROVIDER_ERROR`/`AI_UNSAFE_OUTPUT` (502). AI evaluation is not guaranteed to be perfectly accurate.

## Exercise idempotency

Every ordinary submission requires a non-empty `Idempotency-Key` of at most 255 characters. Replaying the same key and payload returns the stored response without duplicating XP, progress, review advancement or a heart penalty. Reusing a key with different content returns `409 IDEMPOTENCY_CONFLICT`.

```http
POST /exercises/42/submit
Authorization: Bearer <access-token>
Idempotency-Key: lesson-42-attempt-1
Content-Type: application/json

{"answer":"hello"}
```

## Chat and WebSocket

Private chat creation accepts `participant_username` and guarantees exactly two distinct participants. REST mutations commit to PostgreSQL before events are delivered. Local WebSocket clients receive events immediately. If Redis is configured, an instance-tagged envelope forwards each event to remote instances once while suppressing self-echo and duplicates. Redis publish/subscription failure is fail-open for core chat operations.

WebSocket timestamps are UTC ISO-8601 values. The frontend may display them in `Asia/Bishkek`, but must not rewrite stored instants.

## Health and dependencies

- `GET /health` is process liveness and has no dependency checks.
- `GET /ready` uses PostgreSQL as the only mandatory readiness dependency.
- Redis is optional and is reported as `ok`, `unavailable`, or `disabled`.
- OpenAI is optional and is reported as `configured` or `disabled`.

## Configuration

Required:

- `DATABASE_URL` — PostgreSQL SQLAlchemy async URL, for example `postgresql+asyncpg://user:password@localhost:5432/database`.
- `SECRET_KEY` — at least 32 random characters; known placeholders are rejected.

Optional:

- `REDIS_URL` — defaults to `redis://localhost:6379/0`; an empty value disables Redis.
- `OPENAI_API_KEY` — enables AI endpoints; empty disables them.
- `OPENAI_MODEL` — defaults to `gpt-6-luna`.
- `AI_DAILY_QUOTA` — successful/reserved calls per user and Bishkek day; default 20.
- `AI_TIMEOUT_SECONDS` — provider timeout; default 15.
- `ALLOWED_ORIGINS`, `HOST`, `PORT`, `MAX_HEARTS`, `HEART_REGEN_MINUTES`.

Never commit a real `.env` file or production secret. The repository ignores `.env`.

## Local setup

Python 3.12 is the supported runtime.

```bash
python -m pip install -r req.txt
python -m alembic upgrade head
uvicorn main:duolingo --reload
```

Docker Compose:

```bash
SECRET_KEY="replace-with-at-least-32-random-characters" \
docker compose -f backend/docker-compose.yml up --build
```

PostgreSQL must become healthy before the API starts. Redis may start later or remain unavailable.

## Verification

```bash
ruff check .
python -m compileall -q backend migrations main.py
python -m alembic heads
python -m alembic upgrade head
python -m pytest
docker compose -f backend/docker-compose.yml config --quiet
```

Integration tests create disposable PostgreSQL databases named `llp_test_*`; production data is never used. CI runs once on Python 3.12 with PostgreSQL 17 and Redis 7.

## Architecture

The application is a modular monolith. API handlers delegate to transactional services and repositories; SQLAlchemy/Alembic own persistence; PostgreSQL remains authoritative; Redis and OpenAI are bounded adapters around the core domain.

```text
backend/
  api/           HTTP and WebSocket transport
  schemas/       validated request/response contracts
  services/      transactions and domain rules
  repositories/  persistence queries
  models/        SQLAlchemy entities
  providers/     optional external adapters
  database/      sessions and health checks
migrations/      Alembic history
tests/           unit and PostgreSQL integration tests
```

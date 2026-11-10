# Product Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete practice, motivation, discovery, spaced repetition, optional AI, multi-instance chat, and production verification.

**Architecture:** Extend the existing FastAPI modular monolith with focused transactional modules. PostgreSQL remains authoritative; Redis and OpenAI are optional fail-safe integrations.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL 17, Redis 7, httpx, Pydantic 2, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-product-completion-design.md`

## Global Constraints

- Preserve existing non-paged endpoint contracts.
- Store instants as aware UTC and use Asia/Bishkek for daily boundaries.
- AI never mutates authoritative learning/game state.
- New mutations are transactional and idempotent where replay is possible.
- Redis/OpenAI outages do not break registration, lessons, deterministic exercises, or private chat REST operations.

## Review Focus

- Replaying practice completion must never award two hearts.
- A UTC instant crossing 18:00 must move daily goal/review behavior to the next Bishkek day exactly once.
- Empty/oversized search, pagination, and AI inputs must return stable 4xx responses.
- Missing OpenAI/Redis must produce controlled behavior without partial writes.
- A process must not echo its own Redis chat event twice.

---

### Task 1: Production Hygiene and Clean Extension Migration

**Files:** Modify `backend/api/users.py`, `backend/schemas/course_schema.py`, `.github/workflows/ci.yml`; create new models and `migrations/versions/product_completion.py`; test `tests/integration/test_product_migration.py`. Practice item rows include immutable exercise snapshots plus unique session position/exercise constraints; every model check/unique is mirrored by the migration.

**Interfaces:** Produces schema tables for `review_item`, `practice_session`, `practice_session_item`, `user_daily_goal`, and `ai_usage`.

- [ ] Write failing regression tests for role changes, Pydantic v2 schema config, Python 3.12 CI, and migration constraints.
- [ ] Run focused tests and confirm failure.
- [ ] Fix hygiene issues and add final models/migration.
- [ ] Apply migration to a disposable PostgreSQL database and verify metadata constraints.
- [ ] Commit `fix: prepare production completion schema`.

### Task 2: Daily Goals

**Files:** Create `backend/api/daily_goals.py`, `backend/services/daily_goal_service.py`, repository/schema modules, and `tests/integration/test_daily_goals.py`; modify `main.py`.

**Interfaces:** Produces `get_status(user_id, at=None)` and `set_target(user_id, target_xp)` with target 10–200.

- [ ] Test default 20 XP, Bishkek boundary, user update, and server-derived progress.
- [ ] Implement repository aggregation with UTC bounds derived from Bishkek dates.
- [ ] Expose authenticated GET/PUT endpoints.
- [ ] Run focused and full tests; commit `feat: add daily xp goals`.

### Task 3: Spaced Repetition

**Files:** Create review API/service/repository/schema modules; modify `backend/services/exercise_service.py`; test `tests/integration/test_spaced_repetition.py`.

**Interfaces:** Produces `record_result(user_id, exercise_id, correct, at, commit=False)` and paged due-review reads.

- [ ] Test wrong scheduling, correct interval progression, reset behavior, isolation, and due ordering.
- [ ] Implement deterministic 1/3/7/14/30-day scheduling inside exercise transaction.
- [ ] Add due-review paged endpoint and tests.
- [ ] Commit `feat: add spaced repetition scheduling`.

### Task 4: Earn-a-Heart Practice

**Files:** Create practice API/service/repository/schema modules; test `tests/integration/test_practice_hearts.py`; modify `main.py`.

**Interfaces:** Produces create-session and idempotent complete-session operations as defined in the spec; passing score >=80 awards at most one heart.

- [ ] Test finite server-selected sessions, expiry, ownership, score, heart cap, replay, and no XP/streak.
- [ ] Implement transactional creation/completion with row locks.
- [ ] Expose authenticated endpoints and complete heart status.
- [ ] Commit `feat: earn hearts through practice`.

### Task 5: Pagination and Search

**Files:** Create `backend/schemas/page_schema.py`; modify language/course/lesson/exercise/user/chat repositories and APIs; test `tests/integration/test_pagination_search.py`.

**Interfaces:** Produces the spec's compatible `/paged` route matrix with `items,total,limit,offset`, deterministic ordering, authorization, and optional normalized `q`.

- [ ] Test bounds, stable ordering, totals, case-insensitive search, and access control.
- [ ] Implement SQL count/query pairs without loading full tables.
- [ ] Add paged routes while retaining old list routes.
- [ ] Commit `feat: add paged search endpoints`.

### Task 6: Optional Bounded AI

**Files:** Create AI API/provider/service/schema/repository modules; modify config/`main.py`/`req.txt`; test `tests/unit/test_ai_service.py` and `tests/integration/test_ai_api.py`.

**Interfaces:** Produces the six authenticated request/response contracts, context rules, moderation, error bodies, and atomic quota semantics defined in the spec.

- [ ] Test missing key, input bounds, daily quota, timeout/provider errors, moderation, prompt data minimization, and non-mutation.
- [ ] Implement provider interface and Responses API adapter with `store=false`, moderation, `gpt-6-luna`, output/token/time limits, and hashed safety id.
- [ ] Persist usage audit and expose authenticated endpoints.
- [ ] Commit `feat: add bounded ai learning assistance`.

### Task 7: Redis Multi-instance Chat Events

**Files:** Create `backend/services/chat_event_broker.py`; modify chat API/WebSocket/main lifespan, `backend/database/health.py`, and Compose readiness; test `tests/integration/test_chat_broker.py` and readiness behavior.

**Interfaces:** Produces fail-open envelope publishing and a cancellable subscriber forwarding remote targeted events once; PostgreSQL remains the sole mandatory readiness dependency.

- [ ] Test local delivery, remote delivery, own-event suppression, Redis outage, startup, and shutdown.
- [ ] Implement instance-tagged Redis Pub/Sub and lifespan listener.
- [ ] Commit `feat: fan out chat events through redis`.

### Task 8: Final Production Verification

**Files:** Modify `README.md`, `.github/workflows/ci.yml`, Docker configuration; create final journey tests.

**Interfaces:** Consumes all prior modules and publishes stable frontend contracts.

- [ ] Run Python 3.12 full tests, PostgreSQL migrations, Redis integration, compose validation, compile, diff, and secret audit.
- [ ] Document heart timer, practice, goals, review, pagination, AI availability/errors, and deployment variables.
- [ ] Request whole-branch review and fix Critical/Important findings.
- [ ] Commit `test: verify completed learning platform`.

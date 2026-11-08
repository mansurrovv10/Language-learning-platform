# Core Learning Flow Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a tested core path from registration through language learning, hearts, progress, XP/streak, and private chat on a clean PostgreSQL baseline.

**Architecture:** Keep the existing FastAPI modular monolith, but move core game-state mutations behind server-owned service transactions. PostgreSQL is authoritative for durable state, Redis remains an optional/fail-open runtime dependency for rate limiting, and all instants are stored as aware UTC while calendar rules use `Asia/Bishkek`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL 17, Alembic, Redis 7, Pydantic 2, pytest, pytest-asyncio, httpx.

**Spec:** `docs/superpowers/specs/2026-11-09-core-learning-flow-stabilization-design.md`

## Global Constraints

- Preserve the existing FastAPI/SQLAlchemy/PostgreSQL/Redis modular-monolith structure.
- Database contents are disposable; replace the broken migration history with one clean baseline and one Alembic head.
- Start with failing tests and use `python -m pytest`, not the hanging standalone `pytest.exe` found in this Windows environment.
- Store instants as aware UTC; use `ZoneInfo("Asia/Bishkek")` for streak and daily calendar dates.
- Hearts start at 5, regenerate one every 30 minutes beginning with the first loss, and never exceed 5.
- Clients cannot mutate hearts, progress, XP, streak, rank, or access level directly.
- Exercise side effects are atomic and idempotent through the `Idempotency-Key` header.
- AI, daily goals, earn-a-heart practice, spaced repetition, new group chats, and multi-instance WebSocket fan-out remain out of scope.
- Do not overwrite unrelated user worktree changes; review overlapping heart/exercise edits before each patch.

## Review Focus

- Two concurrent requests with the same idempotency key must produce one stored result, one penalty/reward, and no 500; covered in Task 4.
- UTC 18:00 crossing into the next Bishkek day must advance daily behavior exactly once; covered in Task 2 and Task 5.
- A missing Redis server must not break normal registration, lessons, exercise submission, or liveness; covered in Task 8.
- A non-member or ordinary member must not add users to a private chat or read its messages; covered in Task 6.
- Empty, oversized, malformed, or replayed client inputs must return stable 4xx errors without partial writes; covered in Tasks 3, 4, 6, and 7.

---

## File Structure

- `backend/time.py`: single source of truth for UTC instants and Bishkek calendar dates.
- `backend/models/exercise_submission.py`: durable idempotency record for exercise submissions.
- `backend/schemas/error_schema.py`: stable machine-readable error payload.
- `backend/services/exercise_service.py`: one transactional exercise-submission use case.
- `backend/services/chat_service.py`: private-chat membership policy and message validation.
- `backend/services/account_service.py`: soft-deactivation and token revocation.
- `backend/database/health.py`: bounded PostgreSQL/Redis readiness checks.
- `tests/unit/`: pure heart, answer, time, streak, and permission rules.
- `tests/integration/`: real PostgreSQL/Redis migration and API/WebSocket flows.

### Task 1: Clean PostgreSQL Baseline and Integration Harness

**Files:**
- Modify: `req.txt`
- Modify: `backend/models/__init__.py`
- Create: `backend/models/exercise_submission.py`
- Replace: `migrations/versions/*.py` with one clean baseline migration
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_migrations.py`
- Modify: `pytest.ini`

**Interfaces:**
- Consumes: current SQLAlchemy metadata and the approved disposable-database decision.
- Produces: `ExerciseSubmission` with unique `(user_id, idempotency_key)` and integration fixtures `postgres_url`, `redis_url`, `db_session`, and `api_client`.

- [ ] **Step 1: Add the failing empty-database migration test**

Create `test_upgrade_head_on_empty_database` that runs `alembic upgrade head` against an empty PostgreSQL schema and asserts exactly one Alembic head. Add `test_baseline_contains_core_constraints` asserting unique constraints for hearts/user, streak/user, user-language, user-exercise, user-lesson, and submission idempotency.

- [ ] **Step 2: Run the migration tests and verify the duplicate-table failure**

Run: `python -m pytest tests/integration/test_migrations.py -v -m integration`

Expected: FAIL on the current duplicate `level_test`, `user_language`, or `user_exercise_progress` creation.

- [ ] **Step 3: Add explicit async-test dependencies and integration marker**

Add compatible `pytest-asyncio` and PostgreSQL/Redis test requirements to `req.txt`; register `integration` in `pytest.ini`. Fixtures must use environment-provided test URLs and skip with a clear reason when integration services are absent.

- [ ] **Step 4: Define the final idempotency model**

Create `ExerciseSubmission` fields: UUID `id`, UUID `user_id`, integer `exercise_id`, string `idempotency_key`, string `request_hash`, JSON `response`, aware UTC `created_at`; add a named unique constraint on `(user_id, idempotency_key)` and export it from `backend/models/__init__.py`.

- [ ] **Step 5: Replace broken pre-release history with one baseline**

Remove the obsolete version files and create one baseline that reflects all exported models exactly once, including foreign keys, unique constraints, indexes for common user/chat/progress lookups, and timezone-aware timestamp columns.

- [ ] **Step 6: Verify baseline and metadata**

Run: `python -m alembic heads`

Expected: one head.

Run: `python -m pytest tests/integration/test_migrations.py -v -m integration`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add req.txt pytest.ini backend/models migrations/versions tests/integration
git commit -m "test: establish clean database baseline"
```

### Task 2: Unified UTC and Bishkek Time Rules

**Files:**
- Create: `backend/time.py`
- Modify: timestamp-bearing files under `backend/models/`
- Modify: `backend/repositories/gamification_repo.py`
- Modify: `backend/services/challenge_service.py`
- Create: `tests/unit/test_time.py`
- Modify: `tests/test_hearts_regen.py`

**Interfaces:**
- Consumes: timezone-aware columns from Task 1.
- Produces: `utc_now() -> datetime`, `bishkek_date(at: datetime | None = None) -> date`, and `to_utc_naive_compat(value: datetime) -> datetime` only if temporary compatibility is required during the transition.

- [ ] **Step 1: Write failing time-boundary tests**

Assert that `2026-11-08T17:59:59Z` is November 8 in Bishkek, `2026-11-08T18:00:00Z` is November 9, and returned UTC instants include timezone information.

- [ ] **Step 2: Write failing aware-heart tests**

Update regeneration tests to use aware UTC values and assert `next_heart_at` is exactly 30 minutes after the regeneration anchor.

- [ ] **Step 3: Run focused tests**

Run: `python -m pytest tests/unit/test_time.py tests/test_hearts_regen.py -v`

Expected: FAIL because shared time functions and `next_heart_at` do not exist.

- [ ] **Step 4: Implement the shared time module and replace local clocks**

Implement `utc_now` with `datetime.now(timezone.utc)` and `bishkek_date` with `ZoneInfo("Asia/Bishkek")`. Replace `datetime.utcnow()`, `date.today()`, and ad-hoc UTC conversion in core models/services/repositories.

- [ ] **Step 5: Expose complete heart timing**

Add `next_heart_at: datetime | None` to `HeartsResponse` and to `GamificationRepository.get_hearts_status`; full hearts return null.

- [ ] **Step 6: Verify unit tests**

Run: `python -m pytest tests/unit/test_time.py tests/test_hearts_regen.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/time.py backend/models backend/repositories/gamification_repo.py backend/services/challenge_service.py backend/schemas/gamification_schema.py tests
git commit -m "fix: unify UTC and Bishkek calendar time"
```

### Task 3: Registration, Language Selection, and Lesson Access

**Files:**
- Modify: `backend/services/auth_ser.py`
- Modify: `backend/repositories/auth_repo.py`
- Modify: `backend/services/learning_path_service.py`
- Modify: `backend/repositories/learning_path_repo.py`
- Modify: `backend/config.py`
- Create: `backend/schemas/error_schema.py`
- Create: `tests/integration/test_registration_learning_path.py`

**Interfaces:**
- Consumes: `db_session`/`api_client` fixtures and aware time helpers.
- Produces: atomic `AuthService.register(...)`, idempotent `LearningPathService.start_language(...)`, and error body `{"detail": {"code": str, "message": str}}` for core domain failures.

- [ ] **Step 1: Write failing registration tests**

Test that registration creates exactly one user and one five-heart row, duplicate email/username produces stable 400 responses, and two users receive independent heart rows.

- [ ] **Step 2: Write failing language/access tests**

Test that an active language starts idempotently at A1, an inactive/missing language is rejected, and a user cannot access a lesson belonging to a language they have not started.

- [ ] **Step 3: Write configuration validation tests**

Test that application configuration rejects a missing/blank `SECRET_KEY` outside an explicitly marked test environment.

- [ ] **Step 4: Run focused integration tests**

Run: `python -m pytest tests/integration/test_registration_learning_path.py -v -m integration`

Expected: FAIL because registration does not create hearts atomically and language existence/activity is not enforced.

- [ ] **Step 5: Implement atomic registration and normalized conflicts**

Change repository operations used by registration to `flush` within one service transaction, add the initial `Hearts(user_id=user.id, hearts=5)`, and translate uniqueness races to stable 400 errors.

- [ ] **Step 6: Implement language validation and idempotent start**

Add `LearningPathRepository.get_language(language_id: int)` and enforce `Language.is_active` before `get_or_create_user_language`.

- [ ] **Step 7: Verify focused tests**

Run: `python -m pytest tests/integration/test_registration_learning_path.py -v -m integration`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/config.py backend/services/auth_ser.py backend/repositories/auth_repo.py backend/services/learning_path_service.py backend/repositories/learning_path_repo.py backend/schemas/error_schema.py tests/integration/test_registration_learning_path.py
git commit -m "fix: stabilize registration and language access"
```

### Task 4: Atomic and Idempotent Exercise Submission

**Files:**
- Modify: `backend/api/exercises.py`
- Modify: `backend/services/exercise_service.py`
- Modify: `backend/repositories/exercise_progress_repo.py`
- Modify: `backend/repositories/progress_repo.py`
- Modify: `backend/repositories/gamification_repo.py`
- Modify: `backend/repositories/achievement_repo.py`
- Modify: `backend/schemas/exercise_schema.py`
- Create: `backend/repositories/exercise_submission_repo.py`
- Create: `tests/unit/test_answer_matching.py`
- Create: `tests/integration/test_exercise_submission.py`

**Interfaces:**
- Consumes: `ExerciseSubmission`, `utc_now`, and stable error payloads.
- Produces: `ExerciseService.submit_exercise(exercise_id, data, user_id, idempotency_key, is_admin=False) -> ExerciseResult`; ordinary submissions require non-empty `Idempotency-Key`.

- [ ] **Step 1: Write failing answer-rule tests**

Pin ordered answers as order-sensitive, match-pair answers as order-insensitive, normalized text as case/space-insensitive, and null/malformed answers as invalid rather than correct.

- [ ] **Step 2: Write failing transaction and replay tests**

Test wrong answer removes one heart, correct answer removes none, completed practice removes none and awards no XP, identical replay returns the same response, changed payload with the same key returns 409, and a forced late failure rolls back hearts/progress/XP together.

Also assert ordinary exercise responses never expose `correct_answer`, and admin preview returns correctness without creating hearts, progress, XP, streak, achievement, leaderboard, or idempotency side effects.

- [ ] **Step 3: Write the concurrency test**

Submit the same key concurrently and assert one `ExerciseSubmission`, one exercise-progress row, at most one heart loss, and at most one first-completion XP entry.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/unit/test_answer_matching.py tests/integration/test_exercise_submission.py -v`

Expected: FAIL on missing header/repository and current fragmented commits.

- [ ] **Step 5: Implement request fingerprinting and reservation**

Create `ExerciseSubmissionRepository.get_or_reserve(user_id: UUID, key: str, exercise_id: int, request_hash: str)` and `store_response(submission, response: dict)`. A same-key/different-hash request raises the domain idempotency conflict.

- [ ] **Step 6: Make the use case one transaction**

Remove independent commits from repositories used by submission; lock the heart/progress rows where needed, flush intermediate state, and commit once in the API/service transaction boundary.

- [ ] **Step 7: Implement type-specific answer comparison**

Dispatch comparison by `Exercise.type`; preserve sequence order for translation/fill-gap and allow unordered pair comparison only for match exercises.

- [ ] **Step 8: Expand the result contract**

Return `correct`, `score`, and nested/current heart status including `next_heart_at`; admin preview computes correctness but returns without durable game mutations.

- [ ] **Step 9: Verify focused and existing tests**

Run: `python -m pytest tests/unit/test_answer_matching.py tests/test_exercise_hearts.py tests/test_hearts_regen.py tests/integration/test_exercise_submission.py -v`

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add backend/api/exercises.py backend/services/exercise_service.py backend/repositories backend/schemas/exercise_schema.py tests
git commit -m "fix: make exercise submission atomic and idempotent"
```

### Task 5: Server-Owned Progress, XP, and Bishkek Streak

**Files:**
- Modify: `backend/api/progress.py`
- Modify: `backend/services/gamification_service.py`
- Modify: `backend/repositories/leaderboard_repo.py`
- Create: `tests/unit/test_streak.py`
- Create: `tests/integration/test_progress_gamification.py`

**Interfaces:**
- Consumes: atomic exercise completion from Task 4 and `bishkek_date` from Task 2.
- Produces: read-only ordinary-user progress API and `advance_streak_for_learning(user_id: UUID, occurred_at: datetime)` used only by first exercise completion.

- [ ] **Step 1: Write failing progress-ownership tests**

Assert an ordinary user cannot set `completed` or `score`, another user's progress remains forbidden, and admin maintenance—if retained—is explicitly admin-only.

- [ ] **Step 2: Write failing streak tests**

Assert two correct completions on the same Bishkek date advance once, UTC 18:00 crosses to the next Bishkek day, a missed local day resets to one, and achievement XP does not advance streak.

- [ ] **Step 3: Write XP/leaderboard consistency tests**

Assert first completion awards 10 XP once, practice awards zero, and the user's returned leaderboard position is derived consistently after the award.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/unit/test_streak.py tests/integration/test_progress_gamification.py -v`

Expected: FAIL because users can mutate progress and streak rules are duplicated.

- [ ] **Step 5: Remove ordinary progress mutation and consolidate streak logic**

Delete or admin-protect `PUT /progress/{progress_id}` and keep one streak implementation using the shared Bishkek date function.

- [ ] **Step 6: Make leaderboard reads authoritative**

Ensure rank/XP returned after an award cannot remain stale; either recompute affected ranks transactionally or derive them from XP history for the current scale.

- [ ] **Step 7: Verify focused tests**

Run: `python -m pytest tests/unit/test_streak.py tests/integration/test_progress_gamification.py -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/api/progress.py backend/services/gamification_service.py backend/repositories/leaderboard_repo.py tests
git commit -m "fix: enforce server-owned progress and streak rules"
```

### Task 6: Private Chat and WebSocket Permissions

**Files:**
- Modify: `backend/api/chats.py`
- Modify: `backend/api/chat_ws.py`
- Modify: `backend/services/chat_service.py`
- Modify: `backend/repositories/chat_repo.py`
- Modify: `backend/schemas/chat_schema.py`
- Create: `tests/unit/test_chat_permissions.py`
- Create: `tests/integration/test_chat.py`

**Interfaces:**
- Consumes: authenticated user dependency and aware UTC timestamps.
- Produces: `ChatCreate` with required `participant_username` for private chat; `ChatService.create_private_chat(data, creator_id)` atomically creates chat plus two members.

- [ ] **Step 1: Write failing permission and validation tests**

Assert private creation needs an existing second user, self-chat/third-member/group creation are rejected, only creator/admin may add/remove another member, and non-members cannot read or post.

- [ ] **Step 2: Write failing message tests**

Assert empty/whitespace and oversized content return 422, valid content receives an aware UTC timestamp, and message history is restricted to members.

- [ ] **Step 3: Write failing WebSocket lifecycle tests**

Assert valid authentication sends `auth.ok` without double-accept, invalid/inactive tokens close with 4401/4403, and a member receives `message.created`.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/unit/test_chat_permissions.py tests/integration/test_chat.py -v`

Expected: FAIL on double accept and missing membership authorization.

- [ ] **Step 5: Implement atomic private-chat creation and policy checks**

Move creator/two-member creation into one service transaction; disable new group creation and enforce creator/admin/member rules at service boundaries.

- [ ] **Step 6: Accept WebSocket exactly once**

Keep the endpoint's initial accept and change `ConnectionManager.connect` to registration only, or let the manager own the sole accept; tests must prove one accept path.

- [ ] **Step 7: Add message constraints and pagination-ready ordering**

Use Pydantic `min_length=1`/bounded maximum plus stripped validation; order by `(created_at, id)` for stable future pagination.

- [ ] **Step 8: Verify focused tests**

Run: `python -m pytest tests/unit/test_chat_permissions.py tests/integration/test_chat.py -v`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add backend/api/chats.py backend/api/chat_ws.py backend/services/chat_service.py backend/repositories/chat_repo.py backend/schemas/chat_schema.py tests
git commit -m "fix: secure private chat and websocket lifecycle"
```

### Task 7: Account Deactivation and Avatar Upload Safety

**Files:**
- Create: `backend/services/account_service.py`
- Modify: `backend/api/users.py`
- Modify: `backend/repositories/user_repo.py`
- Modify: `backend/repositories/auth_repo.py`
- Modify: `backend/api/auth.py`
- Modify: `main.py`
- Create: `tests/integration/test_account_security.py`

**Interfaces:**
- Consumes: current-user authentication and durable refresh tokens.
- Produces: `AccountService.deactivate(user_id: UUID) -> None`; deactivation sets `is_active=False`, revokes all refresh tokens, and leaves learning/chat history intact.

- [ ] **Step 1: Write failing deactivation tests**

Assert deactivation preserves related rows, revokes all refresh tokens, blocks login/access/refresh, and is idempotent.

- [ ] **Step 2: Write failing upload tests**

Assert non-raster/SVG, invalid image bytes, oversized files, and dangerous extensions are rejected; valid JPEG/PNG/WebP receives a generated server filename and bounded storage path.

- [ ] **Step 3: Run focused tests**

Run: `python -m pytest tests/integration/test_account_security.py -v`

Expected: FAIL because deletion attempts hard deletes and upload trusts MIME/read-all behavior.

- [ ] **Step 4: Implement soft deactivation**

Replace `/users/me` hard deletion with `AccountService.deactivate`; add `AuthRepository.delete_refresh_tokens_for_user(user_id)` and verify inactive status on login/refresh/current-user paths.

- [ ] **Step 5: Implement bounded raster validation**

Stream to a bounded temporary file, verify actual JPEG/PNG/WebP content using an image library, generate a safe filename, and keep the existing `/uploads` mount without trusting the original extension.

- [ ] **Step 6: Verify focused tests**

Run: `python -m pytest tests/integration/test_account_security.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/services/account_service.py backend/api/users.py backend/repositories/user_repo.py backend/repositories/auth_repo.py backend/api/auth.py main.py tests/integration/test_account_security.py req.txt
git commit -m "fix: deactivate accounts and secure avatar uploads"
```

### Task 8: Readiness, Docker Dependencies, and Full Core Verification

**Files:**
- Create: `backend/database/health.py`
- Modify: `main.py`
- Modify: `backend/docker-compose.yml`
- Modify: `backend/middleware.py`
- Modify: `tests/test_health.py`
- Create: `tests/integration/test_readiness_redis.py`
- Create: `tests/integration/test_core_journey.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: all prior core APIs and integration fixtures.
- Produces: `/health` liveness independent of dependencies and `/ready` bounded PostgreSQL/Redis readiness response.

- [ ] **Step 1: Write failing liveness/readiness tests**

Assert `/health` returns immediately when PostgreSQL/Redis are unavailable; `/ready` reports dependency failure with 503 and bounded latency; healthy services return 200.

- [ ] **Step 2: Write Redis fail-open/expiry tests**

Assert rate-limit keys expire and a Redis connection failure allows normal core requests while readiness reports Redis unavailable.

- [ ] **Step 3: Write the end-to-end core journey test**

Register two users, start an active language, access a lesson, submit one wrong and one correct exercise with distinct idempotency keys, verify isolated hearts/progress/10 XP/streak, create a private chat, authenticate WebSocket, and exchange a message.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_health.py tests/integration/test_readiness_redis.py tests/integration/test_core_journey.py -v`

Expected: FAIL before readiness and dependency health checks exist.

- [ ] **Step 5: Implement bounded health checks and Docker health ordering**

Add PostgreSQL `SELECT 1` and Redis `PING` checks with explicit timeouts; add Compose healthchecks and `service_healthy` dependencies before migrations/application startup.

Remove the core correctness dependency on the in-process heart-refill loop. If the optimization loop remains, prove startup, shutdown, and multi-run behavior are harmless; otherwise remove it and rely on request-time regeneration.

- [ ] **Step 6: Document the stable frontend contract**

Update README with registration-to-chat setup, `Idempotency-Key`, heart response/timer behavior, UTC/Bishkek display rule, core error codes, and integration-test commands.

- [ ] **Step 7: Run the complete suite**

Run: `python -m pytest -v`

Expected: all non-integration tests pass.

Run with PostgreSQL and Redis test services configured: `python -m pytest -v -m integration`

Expected: all integration tests pass.

Run: `python -m alembic upgrade head`

Expected: clean database reaches the single head.

- [ ] **Step 8: Review the final diff for secret/file leakage**

Run: `git status --short` and `git diff --check`; confirm `.env`, uploaded media, caches, and credentials are untracked.

- [ ] **Step 9: Commit**

```bash
git add backend/database/health.py main.py backend/docker-compose.yml backend/middleware.py tests README.md
git commit -m "test: verify complete core learning journey"
```


# Core Learning Flow Stabilization Design

## Intent

Stabilize the first demonstrable version of the language-learning platform before adding more product breadth. The version must reliably support the complete path:

`registration -> language selection -> lesson -> exercises -> hearts -> progress -> XP/streak -> chat`

The purpose of this phase is not to redesign the product or add AI. It is to make the existing core safe, internally consistent, testable, and suitable for frontend integration.

## Goals

- A new user can register, authenticate, select an active language, open an allowed lesson, submit exercises, and see server-owned progress.
- Every user has an isolated five-heart balance.
- A wrong answer to a not-yet-completed exercise removes exactly one heart.
- Heart recovery starts with the first loss (`5 -> 4`) and restores one heart every 30 minutes, up to five.
- A user with zero hearts cannot submit a new, incomplete exercise, but may practice an already completed exercise.
- Repeated or concurrent HTTP submissions cannot duplicate a penalty, progress update, or XP award.
- XP is awarded once for the first correct completion of an exercise.
- Streak and daily boundaries follow the `Asia/Bishkek` calendar.
- Chat authentication, membership permissions, message delivery, and timestamps work for the current single-instance deployment.
- The Alembic chain upgrades a completely empty PostgreSQL database to the current schema without duplicate-table failures.
- Critical behavior is covered by automated unit and PostgreSQL/Redis integration tests.

## Non-goals for this phase

- AI explanations, AI conversation, AI grading, or generated exercises.
- Practice-to-earn-a-heart.
- Daily XP goals.
- Spaced repetition.
- Full frontend implementation; this phase only provides a stable API contract for it.
- Horizontal WebSocket scaling across multiple backend instances.
- New group-chat features, attachments, calls, or advanced moderation.
- Reworking all existing course content.

## Anti-goals

- Do not let the client directly set completion, score, hearts, XP, streak, rank, or access level.
- Do not store Bishkek-shifted local timestamps in the database.
- Do not use an AI model to decide deterministic exercise correctness or award game state.
- Do not solve migration problems by silently deleting an existing user database.
- Do not mix unrelated feature additions into the stabilization changes.

## Constraints

- Keep the existing FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, Redis, and Pydantic stack.
- Preserve existing user worktree changes; stabilization work must be reviewed against them instead of overwriting them.
- Existing database contents are disposable for this pre-release project. The database may be rebuilt from a clean baseline migration.
- The current deployment is one Uvicorn application instance behind Nginx. Multi-instance chat delivery is deferred.
- Public API changes should use explicit response schemas and consistent HTTP errors so the frontend can integrate without database knowledge.

## Approaches considered

### 1. Point fixes

Patch each observed bug in place. This is fastest initially but keeps fragmented commits, inconsistent time rules, and incomplete test coverage. Rejected because failures in one core step can still leave game state partially updated.

### 2. Full backend rewrite

Replace the existing modules with a newly designed application. This could produce a cleaner model but has excessive scope and regression risk for a practical team project. Rejected.

### 3. Incremental core-flow stabilization

Retain the modular monolith, define server-owned invariants, repair one core flow, and protect it with integration tests before adding features. Selected because it produces a demonstrable product while preserving the team's existing work.

## Core behavior

### Registration and authentication

- Registration normalizes email, validates username/password, and handles database uniqueness races as a client error rather than a 500.
- User creation and initial heart creation occur atomically.
- A newly registered user begins with five hearts.
- Startup fails clearly if `SECRET_KEY` or `DATABASE_URL` is missing or unsafe for the selected environment.
- Refresh-token hardening beyond what is required for a stable core flow may be handled as a follow-up security task, but existing refresh behavior must remain tested.
- Account removal in this phase means soft deactivation, refresh-token revocation, and login denial. Learning and chat history remain stored; irreversible deletion/anonymization is deferred.

### Language selection and learning access

- A user may start only an existing active language.
- Starting a language is idempotent: repeated calls return the same `UserLanguage` state.
- Initial level remains A1 and placement remains incomplete, matching the existing project behavior.
- Course and lesson access is derived on the server from `UserLanguage`; IDs supplied by the client do not bypass access checks.

### Exercise submission and idempotency

- Submission accepts an `Idempotency-Key` HTTP header representing one user action. The same user and key return the already stored result without applying side effects again.
- The idempotency record stores the user, endpoint operation, exercise, canonical request fingerprint, response, and creation time. Reusing a key with a different exercise or answer returns an idempotency-conflict response.
- Idempotency records are retained without automated deletion in this phase; a bounded retention/cleanup policy is deferred until usage volume requires it.
- The server verifies exercise access and answer format before mutating game state.
- Correctness rules are exercise-type-specific. Ordered exercises preserve order; unordered matching exercises may compare as sets/pairs.
- A submitted null or structurally invalid answer cannot accidentally equal an invalid stored answer.
- The following occur in one database transaction:
  - lock or derive the user's current hearts;
  - reserve the idempotency key;
  - check correctness;
  - apply at most one heart loss;
  - store exercise progress;
  - recompute lesson progress;
  - award first-completion XP at most once;
  - update the streak;
  - store the response for idempotent replay.
- Repository methods used by this flow flush changes but do not independently commit.

### Hearts

- Maximum balance is five.
- Recovery begins when the first heart is lost and continues at one heart per 30 elapsed minutes.
- Recovery is derived from persisted UTC state during reads and submissions; correctness does not depend on a continuously running background loop.
- A background pass may remain only as an optimization and must be safe if disabled or run by more than one process.
- Heart status includes:
  - `hearts`;
  - `max_hearts`;
  - `seconds_to_next_heart`;
  - `next_heart_at` as a timezone-aware UTC timestamp or null when full.
- The exercise response returns the updated heart status so the frontend can start its timer without an extra race-prone request.

### Progress, XP, and streak

- Remove ordinary-user access to mutate `UserProgress` directly. Admin maintenance, if retained, uses an explicitly admin-only route.
- Exercise completion is unique per `(user_id, exercise_id)` and lesson progress is unique per `(user_id, lesson_id)`.
- Repeating a completed exercise is practice: it does not remove hearts and does not award XP again.
- Streak advances only on the first qualifying XP activity of a Bishkek calendar day.
- In this phase, a qualifying streak activity is the first correct completion of an exercise. Achievement rewards, administrative awards, and other XP sources do not advance streak.
- All internal instants are stored as timezone-aware UTC. Calendar-day conversion uses `ZoneInfo("Asia/Bishkek")` in one shared time utility.
- Daily challenge behavior is not expanded in this phase, but any existing "today" lookup must use the same Bishkek date rule.

### Chat

- A WebSocket is accepted exactly once, then authenticated within a bounded timeout.
- Inactive or invalid users are rejected.
- Creating a private chat requires the second participant's username and atomically creates the chat with exactly those two members.
- Creating group chats is disabled in this phase. Existing group-chat rows remain readable to authorized members but group read-receipt semantics and new group creation are deferred.
- Only the chat creator or a platform admin may add another member.
- A normal member may remove only themselves; the creator/admin may remove another member according to chat rules.
- A private chat has exactly two members and cannot be expanded into a group by adding more members.
- Reading or posting messages requires membership; platform-admin read access remains an explicit administrative exception.
- HTTP message content has non-empty and maximum-length validation.
- Message timestamps are timezone-aware UTC. The frontend displays them in `Asia/Bishkek`.
- `is_read` remains usable only for the current simple/private-chat scope. Per-user group read receipts are deferred.
- Current in-process WebSocket delivery is acceptable for the single application instance. Redis-backed cross-instance fan-out is deferred, but Redis availability receives an integration test because rate limiting and future presence depend on it.

### Administrator exercise preview

- An administrator may preview and submit exercises without lesson-access or heart restrictions.
- Preview submissions do not mutate hearts, progress, XP, streak, achievements, or leaderboard state.

## Database migrations

- Replace the broken pre-release migration history with one clean baseline representing the stabilized schema.
- Recreate the development database from that baseline; preserving current rows is not required.
- Keep exactly one Alembic head and create every table and constraint once.
- Use timezone-aware timestamp columns in the baseline, so no conversion of historical naive timestamps is needed.
- The migration test creates an empty PostgreSQL database/schema and runs `alembic upgrade head`.
- A second test compares important resulting constraints with SQLAlchemy metadata.

## API and error contract

- Use consistent error objects with a stable machine code and human-readable message for core-flow failures.
- Expected core codes include invalid credentials, inactive language, locked lesson, invalid answer shape, no hearts, and idempotency conflict.
- Authentication and authorization failures remain 401/403; missing resources use 404; exhausted hearts use 409; validation uses 422.
- OpenAPI schemas must not expose correct answers to ordinary users.

## Testing strategy

### Unit tests

- Heart regeneration at boundaries and maximum cap.
- Exercise-type-specific answer comparison.
- Bishkek day conversion around UTC 18:00, which is local midnight.
- Streak same-day, next-day, and missed-day behavior.
- Permission policy for chat members.

### PostgreSQL integration tests

- Registration creates one user and five isolated hearts.
- Two users' heart balances never affect each other.
- Wrong/correct/repeated exercise submissions apply the intended effects.
- Replaying an idempotency key returns the same result with no duplicate effects.
- Concurrent submissions preserve unique progress and single XP awards.
- Users cannot mutate their progress directly.
- Empty-schema Alembic upgrade succeeds.
- Core deletion/deactivation behavior does not violate foreign keys.

### Redis integration tests

- Rate-limit keys expire as expected.
- Redis outage follows the documented fail-open behavior for normal API requests.
- Basic connection health is observable independently of liveness.

### Chat integration tests

- Successful WebSocket authentication does not double-accept.
- Invalid/inactive authentication is closed with the expected code.
- Unauthorized membership changes fail.
- Members can send and receive message-created events.

## Health and operability

- Keep a lightweight liveness endpoint that does not block on dependencies.
- Add a readiness endpoint that checks PostgreSQL and Redis with bounded timeouts.
- Application shutdown cancels background work without hanging on dependency connections.
- Docker Compose waits for PostgreSQL and Redis health before running migrations/application startup.

## Delivery order

1. Repair and test migrations on an empty PostgreSQL database.
2. Introduce shared UTC/Bishkek time rules and migrate timestamp columns safely.
3. Protect progress from client mutation.
4. Make exercise submission atomic and idempotent, including hearts and XP/streak.
5. Stabilize registration and language/lesson access invariants.
6. Fix chat WebSocket lifecycle and membership permissions.
7. Add PostgreSQL/Redis integration coverage and readiness checks.
8. Publish the finalized heart/timer API contract for frontend work.

## Deferred roadmap

After this design is implemented and verified:

1. Practice session that can award one heart under controlled rules.
2. Daily XP target, initially 20 XP and configurable later.
3. Pagination and search across messages/content where needed.
4. Spaced repetition driven by a durable mistake/review model.
5. AI explanations, examples, level-based conversation, personalized review suggestions, hints, and probabilistic free-text feedback with quotas and safety controls.

## Builder-owned decisions

- Exact names of internal helper functions and repository methods.
- Test fixture organization and container naming.
- Whether core error-code strings use upper snake case or lower kebab case, provided the style is consistent and documented.
- Small response-schema naming choices that do not change behavior.


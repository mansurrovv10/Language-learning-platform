# Product Completion Design

## Intent

Complete the remaining learning-product backend while preserving the FastAPI modular monolith and the server-owned game-state rules already shipped. The result must support sustainable practice, daily motivation, discoverable paged content, spaced repetition, optional bounded AI assistance, and multi-instance chat without making OpenAI or Redis hard dependencies for ordinary learning.

## Goals

- Let a user earn exactly one heart by passing a finite server-created practice session.
- Track a configurable daily XP target using the Asia/Bishkek calendar.
- Schedule weak exercises for review with deterministic spaced-repetition intervals.
- Add bounded search/pagination without breaking existing list endpoints.
- Add optional AI explanations, hints, examples, level-aware conversation, review generation, and free-text assessment.
- Make AI non-authoritative: it never directly grants XP, hearts, completion, rank, or access.
- Support cross-instance WebSocket fan-out through Redis with fail-open local delivery.
- Finish Python 3.12 CI, schema quality, configuration, migrations, tests, and documentation.

## Non-goals

- AI-generated answers do not replace deterministic exercise grading.
- Group chat remains disabled; private chat stays exactly two participants.
- No paid AI request is made when `OPENAI_API_KEY` is absent.
- No frontend framework is introduced into this backend-only repository; stable timer and pagination contracts are documented for the frontend team.

## Architecture

### Practice and review

`ReviewItem` stores one row per user/exercise with `box`, `due_at`, `last_result`, and attempt counters. Every non-admin, non-replayed graded attempt updates it. A wrong answer resets to box 0 and is due immediately. A correct answer advances one box, capped at box 5, and is due after an elapsed 1, 3, 7, 14, or 30 days from the authoritative attempt instant.

A `PracticeSession` snapshots up to three due or previously failed exercises in `(due_at, exercise_id)` order, expires after 15 minutes, and can be completed once. At least one eligible exercise is required; otherwise creation returns `409 PRACTICE_NOT_AVAILABLE`. A user has at most one unexpired active session, which creation returns again. Full-heart users may practise but cannot exceed five hearts. Each item stores an immutable question, type, options, and correct-answer snapshot; responses never expose the correct answer. Completion requires exactly one answer for every item, rejects missing/duplicate/foreign items, and persists the payload hash plus result. An identical replay returns the stored result, a changed replay returns `409 IDEMPOTENCY_CONFLICT`, and a completed replay remains valid after expiry. At least 80% correct awards one heart, capped at five; practice awards no XP or streak.

### Daily goal

`UserDailyGoal` stores the user's target XP, default 20 and constrained to 10–200. Progress is derived from `XPHistory` between local Bishkek day boundaries converted to UTC, so it cannot drift or be client-edited.

### Pagination and search

Existing list endpoints remain compatible. New `/paged` endpoints return `{items,total,limit,offset}` and accept trimmed `q` of at most 100 characters, `limit` 1–100, and a non-negative `offset`. Languages search name/code; courses search title/description; lessons search title; exercises search question; admin-only users search username/email but retain the existing private schema; chat-message search is restricted to current members and searches content. Ordering is deterministic with an ID tie-breaker; messages use `(created_at, id)`. Initial coverage includes languages, courses, lessons, exercises, users, and chat messages.

### AI

`AIProvider` is an interface; `OpenAIResponsesProvider` uses the Responses API over `httpx`, `store=false`, `gpt-6-luna` by default, `max_output_tokens`, integrated moderation, structured JSON output where evaluation is required, a hashed `safety_identifier`, and strict timeouts. `AIUsage` provides a durable per-user audit and daily request quota. Missing configuration returns stable `503 AI_UNAVAILABLE`; provider failures return `502 AI_PROVIDER_ERROR`; moderation blocks unsafe output. AI endpoints only return guidance and advisory assessments.

All AI routes are authenticated under `/ai`. The server derives the user's selected language, level, and bounded learning context; clients cannot impersonate another level or user. `/explain` accepts an exercise id and the user's answer and returns `{explanation}`; `/hint` accepts an exercise id and returns `{hint}` without the answer; `/examples` accepts an exercise id and count 1–5 and returns `{examples}`; `/chat` accepts one message (1–2000 characters) and up to 10 prior client messages (each at most 1000 characters) and returns `{reply}`; `/review` accepts no free-form learning facts and returns up to five personalized tasks from server-fetched due items; `/evaluate` accepts an exercise id plus a free-text answer (1–2000 characters) and returns structured `{accepted, score, feedback}` with score 0–1. Inputs and outputs are moderated. The daily quota is atomically reserved before a provider call; rejected unsafe input and provider failures are audited but do not consume the successful-call quota. Stable errors use `{detail: {code, message}}`.

Official API basis: [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create), [model catalog](https://developers.openai.com/api/docs/models), and [moderation guide](https://developers.openai.com/api/docs/guides/moderation).

### Multi-instance chat

After a successful database commit, REST mutations deliver locally and then publish `{event_id, instance_id, target_user_ids, payload}` to a Redis channel. Access-revocation events include the removed user. Each process subscribes during FastAPI lifespan and forwards only remote events to its local target sockets, ignoring its own instance id. Redis failures log and preserve local delivery without rolling back the REST mutation.

## Security and limits

- Practice session creation/completion is server-owned, transactional, expiring, and idempotent.
- AI input is trimmed and length-bounded; 20 requests/user/Bishkek day by default.
- No raw email/username is sent as a safety identifier; use a SHA-256 user-id digest.
- Pagination limit is 1–100 and offsets are non-negative.
- Search escapes/normalizes user input and never interpolates raw SQL.
- All new instants are aware UTC and database uniqueness is explicit in both metadata and migrations.
- PostgreSQL alone determines readiness. Redis reports `ok`, `unavailable`, or `disabled`, and OpenAI reports `configured` or `disabled`; neither optional dependency changes the readiness HTTP status.

## Approaches considered

1. Add features directly to existing gamification/exercise services. Lowest file count, but creates tightly coupled services and unsafe transaction boundaries.
2. Add focused modules for practice, review, daily goals, AI, and event brokering while reusing existing repositories. Chosen: clear ownership, independent testing, and incremental rollout.
3. Split into microservices. Rejected: operational cost and distributed transactions are disproportionate for the current project.

## Rollout

Each subsystem is introduced with a migration, RED/GREEN integration tests, and a separate commit. AI and Redis are optional at runtime; readiness reports their state without blocking core learning where appropriate.

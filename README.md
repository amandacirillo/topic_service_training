# Topic Service Training

> **Note:** This is a from-scratch recreation of an architectural pattern I built at my employer, not the original production code -- rebuilt with a fabricated/generic domain and no proprietary business logic, credentials, or internal resource identifiers.

A small Flask microservice for managing named "topic lists" and serving one
topic at a time to a downstream content-generation pipeline. This is a
from-scratch training example that demonstrates several real patterns from
an internal service, rebuilt with no proprietary code, data, names, or
credentials.

## What this simulates

Imagine an AI content pipeline that periodically needs "a topic" to write
about -- maybe for generating practice questions, sample essays, or quiz
prompts. Rather than hardcoding topics into the pipeline, it calls out to
this service, which owns curated lists of topics, tracks how often each one
has been used, and can pick the "next" one according to a configurable
strategy.

## Patterns demonstrated

### 1. Pluggable selection strategies (`app/strategies.py`)
Instead of an `if strategy == "x": ... elif strategy == "y": ...` chain, each
strategy is a plain function registered in a `STRATEGIES` dict:

- `least_used` -- always pick from whichever topics have the lowest usage
  count (ties broken randomly).
- `random` -- uniform random choice.
- `sequential` -- fewest uses first, ties broken by creation order.
- `weighted_random` -- probability weighted toward less-used topics, without
  fully excluding anything.

Adding a new strategy means writing one function and adding one dict entry --
no existing code has to change. See `tests/test_strategies.py` for how easy
this makes strategies to unit test in isolation (with plain fake objects,
no Flask app or database required).

### 2. Usage tracking + fairness + auto-deactivation (`app/models.py`, `app/api.py`)
Every time a topic is served, a `TopicUsage` row is recorded. Topic lists can
be marked `reusable=False`, in which case a topic is deactivated the moment
it's served -- turning the list into a one-time-use queue instead of a
rotating pool. This is a common need for "don't ask the same question twice"
scenarios.

### 3. Low-inventory alerting (`app/alerts.py`)
When a non-reusable list's active topic count drops below an absolute or
percentage threshold, an alert fires. The email/notification channel is
abstracted behind a `NotificationSender` protocol -- tests use
`NullNotificationSender` (which just records what would have been sent),
while a real deployment uses `SesNotificationSender`. This means the alerting
*logic* (the interesting, bug-prone part) is fully unit-testable without
touching AWS at all.

### 4. AI-suggests, human-approves workflow (`app/suggester.py`, `app/admin.py`)
An admin can ask the service to suggest new topics for a list. The service
builds a prompt from the list's name/description and existing topics (to
avoid duplicates), sends it to an LLM client, and shows the results in a
simple checkbox form -- nothing is persisted until a human approves specific
suggestions. The LLM call is behind an `LlmClient` protocol so the dedup and
prompt-building logic can be tested with a fake client that returns
canned JSON, with no API key or network access needed. A real client (OpenAI
SDK, a LiteLLM proxy, etc.) would just implement `complete(prompt) -> str`.

### 5. Simple shared-secret API auth (`app/auth.py`)
All `/api/*` routes require an `X-API-KEY` header (or `Authorization: Bearer
<key>`) matching a configured secret. `/health`, `/healthz`, and `/info` stay
open for load balancer checks and smoke tests. This is intentionally the
simplest form of service-to-service auth that still requires an explicit
credential -- a stepping stone before something like mTLS or signed JWTs.

### 6. Tag-driven, per-environment infrastructure (`infra/cdk/`)
A minimal AWS CDK stack (ECS Fargate + RDS Postgres + ALB) parameterized by
an `EnvironmentConfig` looked up by a short environment name (`dev` / `stg` /
`prd`). In a real pipeline that name comes from a parsed deploy tag or
branch, not a hardcoded map -- but "one small config object per environment"
is the reusable shape. See `infra/cdk/lib/environment.ts`.

## Project layout

```
app/
  models.py       SQLAlchemy models: TopicList, Topic, TopicUsage
  strategies.py   Pluggable topic-selection strategies
  alerts.py       Low-inventory alert logic + notification abstraction
  suggester.py    AI topic suggestion + dedup logic
  auth.py         API key auth decorator
  api.py          JSON API blueprint (/api/...)
  admin.py        Server-rendered admin UI blueprint (/admin/...)
  health.py       Unauthenticated health/info endpoints
  factory.py      Flask application factory
  settings.py     Env-var-driven configuration
templates/admin/  Jinja templates for the admin UI
tests/            pytest suite (in-memory SQLite, fakes for LLM/notifications)
infra/cdk/        Minimal CDK stack + per-environment config
main.py           Local dev entrypoint / WSGI app object
```

## Running locally

```bash
pip install -r requirements.txt -r requirements-dev.txt
python main.py
# or, with Docker:
docker compose up --build
```

Default dev API key is `local-dev-key` (see `app/settings.py` / `docker-compose.yml`).
Try it out:

```bash
curl -H "X-API-KEY: local-dev-key" -X POST http://localhost:5000/api/topic_lists \
  -H "Content-Type: application/json" -d '{"name": "Animals", "reusable": true}'

curl -H "X-API-KEY: local-dev-key" http://localhost:5000/api/topic_lists

curl -H "X-API-KEY: local-dev-key" \
  "http://localhost:5000/api/topic_lists/1/next_topic?strategy=least_used"
```

Or browse the admin UI at `http://localhost:5000/admin/` (no auth -- add some
in front of it, e.g. basic auth at the load balancer, before ever deploying
this for real).

## Running tests / lint / type-check

```bash
pytest -v
flake8 app tests main.py
mypy app main.py --ignore-missing-imports
```

All three run in CI on every push (see `.github/workflows/tests.yml`).

## Exercises

1. **Add a new strategy.** Implement a `least_recently_used` strategy that
   picks the topic whose most recent `TopicUsage.used_at` is oldest (falling
   back to "never used" topics first). Register it in `STRATEGIES` and add
   tests alongside the existing ones in `tests/test_strategies.py`.

2. **Per-list default strategy.** Right now the caller picks a strategy via
   `?strategy=...` on every request. Add a `default_strategy` column to
   `TopicList` so a list can have its own default, used when the query
   param is omitted.

3. **Rate limiting.** Add a simple per-API-key rate limit to `/api/*` routes
   (e.g. using an in-memory token bucket, or Flask-Limiter) and write tests
   that assert a 429 is returned once the limit is exceeded.

4. **Wire up a real LLM client.** Implement a concrete `LlmClient` in
   `app/suggester.py` that calls a real chat-completions API. Keep
   `build_prompt` / `parse_suggestions` / dedup logic unchanged and unit
   tested with the fake client -- only the new class should need network
   access or an API key.

5. **Undo an accidental deactivation.** `/api/topics/<id>/deactivate` has no
   inverse. Add a `/reactivate` endpoint, and consider: should reactivating
   a topic in a non-reusable list be allowed at all? Write a test that
   documents your decision either way.

6. **Alert on more than one threshold.** Currently `is_low_inventory` fires
   once when a list first crosses a threshold, and will fire again on
   *every* subsequent request while it stays below threshold (there's no
   "already alerted" tracking). Add a `last_alerted_at` column and only
   re-alert after a cooldown period; test the cooldown logic directly
   without needing to wait in real time.

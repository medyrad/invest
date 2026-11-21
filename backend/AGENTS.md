# Backend

## Overview

Django 5.2 plus Django REST Framework API for invest, on Python 3.14.10 and PostgreSQL. Each business area is a Django app under `apps/`; the browser reaches it same origin under `/api/v1/`.

## Key files

| File | Owns |
|---|---|
| `config/urls.py` | All `/api/v1/` routes; one view class per app, the action passed as a URL kwarg |
| `config/api.py` | Shared JSON error shape and the 400/403/404/500 handlers |
| `config/settings.py`, `config/env.py`, `config/secrets.py` | Settings read from the environment; secrets never in code |
| `apps/identity` | OTP sign in, sessions, locking |
| `apps/catalog` | Taxonomy, geography, value definitions, versioned reference import |
| `apps/core` | Opportunities, drafts, publication, discovery, cases, reporting |
| `apps/services` | The nine specialist services, advisories, reports |
| `apps/workspace` | Customer workspace files and downloads (scanned by clamd) |
| `apps/assistant` | S09 AI assistant: provider, orchestrator, tools, quota, evaluation |
| `../contracts/openapi.yaml` | API contract, checked against real responses by `tests/test_contract.py` |

## Commands

Run everything through Docker from the repo root (`make check`, `make test`); the host Python is not used. After a code change, rebuild the matching image first. Exact commands live in `docs/development.md`.

```sh
docker compose --env-file .env -f deploy/compose.yaml run --rm --user "$(id -u):$(id -g)" -v "$PWD/backend/apps:/app/apps" backend /app/.venv/bin/python manage.py makemigrations
```

## Conventions

- Dependencies are pinned exactly in `pyproject.toml` and locked with uv 0.11.32 (`uv.lock`); a lock mismatch fails the image build.
- Ruff: target py314, line length 100; `makemigrations --check` must stay clean.
- Tests are pytest with pytest-django in `tests/`, against a real PostgreSQL test database (`test_invest`), not SQLite.
- Data that drives behavior (schemas, field lists, advisories) lives as versioned JSON next to its app, not in code.

## Gotchas

- `contracts/openapi.yaml` holds JSON; the contract test reads it with `json.loads` from `/contracts` inside the container.
- The browser test backend (`browser-api`, localhost 8008) uses a separate URLConf that only accepts `INVEST_ENV=test`.
- Public start is refused with demo values, debug, or demo OTP; `PUBLIC_LAUNCH_ENABLED=true` is not allowed.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._

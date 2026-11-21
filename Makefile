COMPOSE = docker compose --env-file .env -f deploy/compose.yaml
.PHONY: env build up dev stop check test browser smoke
env:
	python3 scripts/dev_runtime.py prepare
build: env
	$(COMPOSE) build backend web test browser-api
up:
	python3 scripts/dev_runtime.py up
dev:
	python3 scripts/dev_runtime.py up --frontend-dev $(if $(BUILD),--build)
stop:
	$(COMPOSE) --profile test stop
check:
	$(COMPOSE) run --rm test /app/.venv/bin/ruff check . --no-cache
	$(COMPOSE) run --rm test /app/.venv/bin/ruff format --check . --no-cache
	$(COMPOSE) run --rm backend /app/.venv/bin/python manage.py makemigrations --check --dry-run
	$(COMPOSE) run --rm backend /app/.venv/bin/python manage.py check
	cd frontend && npm run lint && npm run typecheck
test:
	$(COMPOSE) run --rm test
browser:
	$(COMPOSE) stop browser-api
	$(COMPOSE) run --rm browser-api /app/.venv/bin/python -m tests.prepare_browser_db
	$(COMPOSE) run --rm browser-api /app/.venv/bin/python manage.py migrate --noinput
	$(COMPOSE) run --rm browser-api /app/.venv/bin/python manage.py import_reference
	$(COMPOSE) up -d browser-api
	cd frontend && npm run build && npm run test:e2e
smoke:
	python3 scripts/foundation_smoke.py

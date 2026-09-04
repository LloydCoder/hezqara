# Carenova AI — Makefile
# Usage: make <target>

.PHONY: help dev test lint deploy health

help:
	@echo "Carenova AI — Available commands:"
	@echo "  make dev      Start local development (Docker)"
	@echo "  make test     Run full backend test suite"
	@echo "  make lint     Run Ruff linter + type check"
	@echo "  make health   Check if Carenova is running"
	@echo "  make deploy   Deploy to EC2 (runs deploy.sh)"
	@echo "  make backup   Run database backup"

dev:
	docker compose -f infrastructure/docker/docker-compose.yml up

test:
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	cd backend && ruff check app/
	cd frontend && npm run type-check

health:
	curl -s http://localhost:8004/health | python3 -m json.tool

deploy:
	bash infrastructure/scripts/deploy.sh

backup:
	bash infrastructure/scripts/backup_db.sh

migrate:
	@echo "Apply migrations via Supabase dashboard or:"
	@echo "  supabase db push --db-url \$$DATABASE_URL"

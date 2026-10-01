# HEZQARA — developer and operations commands
.PHONY: help dev test lint health deploy backup migrate

help:
	@echo "HEZQARA commands:"
	@echo "  make dev      Start local development stack"
	@echo "  make test     Run backend tests"
	@echo "  make lint     Run Ruff + frontend type check"
	@echo "  make health   Check the local backend health endpoint"
	@echo "  make deploy   Run the HEZQARA deployment helper"
	@echo "  make backup   Run the database backup helper"
	@echo "  make migrate  Show the Supabase migration command"

dev:
	docker compose up

test:
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	cd backend && ruff check app tests
	cd frontend && npm run type-check

health:
	curl -fsS http://localhost:8004/health | python3 -m json.tool

deploy:
	bash ops/deploy.sh

backup:
	bash ops/backup_db.sh

migrate:
	@echo "Apply migrations through the configured Supabase deployment path:"
	@echo "  supabase db push --db-url \$$DATABASE_URL"

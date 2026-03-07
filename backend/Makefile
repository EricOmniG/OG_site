# ============================================================
#  OMNIGENIUS — Makefile
#  Common development and deployment commands
# ============================================================

.PHONY: help install dev build deploy deploy-staging logs test lint clean ssm-push

# Default target
help:
	@echo ""
	@echo "  Omnigenius API — available commands"
	@echo ""
	@echo "  Dev:"
	@echo "    make install       Install dependencies into venv"
	@echo "    make dev           Run local dev server (hot reload)"
	@echo "    make test          Run test suite"
	@echo "    make lint          Run ruff linter"
	@echo ""
	@echo "  AWS:"
	@echo "    make build         sam build (Lambda package)"
	@echo "    make deploy        Deploy to production"
	@echo "    make deploy-stg    Deploy to staging"
	@echo "    make logs          Tail Lambda logs (production)"
	@echo "    make logs-stg      Tail Lambda logs (staging)"
	@echo "    make ssm-push      Push .env values to SSM Parameter Store"
	@echo ""

# ── Local development ────────────────────────────────────────
install:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

dev:
	.venv/bin/uvicorn app.main:app \
		--host 0.0.0.0 \
		--port 8000 \
		--reload \
		--log-level debug

# ── Testing ──────────────────────────────────────────────────
test:
	.venv/bin/pytest tests/ -v --asyncio-mode=auto

lint:
	.venv/bin/ruff check app/ tests/
	.venv/bin/ruff format --check app/ tests/

# ── AWS SAM ──────────────────────────────────────────────────
build:
	sam build --use-container

deploy: build
	sam deploy --config-env default

deploy-stg: build
	sam deploy --config-env staging

logs:
	sam logs -n OmniGeniusFunction \
		--stack-name omnigenius-api \
		--tail

logs-stg:
	sam logs -n OmniGeniusFunction \
		--stack-name omnigenius-api-staging \
		--tail

# ── SSM Parameter Store ──────────────────────────────────────
# Push all values from .env to SSM as SecureString parameters
# Usage: make ssm-push STAGE=production
STAGE ?= production
ssm-push:
	@echo "Pushing .env to SSM /omnigenius/$(STAGE)/..."
	@while IFS= read -r line; do \
		[[ "$$line" =~ ^#.*$$ ]] && continue; \
		[[ -z "$$line" ]] && continue; \
		key=$$(echo "$$line" | cut -d= -f1); \
		val=$$(echo "$$line" | cut -d= -f2-); \
		[[ -z "$$val" ]] && continue; \
		echo "  Pushing $$key"; \
		aws ssm put-parameter \
			--name "/omnigenius/$(STAGE)/$$key" \
			--value "$$val" \
			--type SecureString \
			--overwrite \
			--region us-east-1 > /dev/null; \
	done < .env
	@echo "Done."

# ── Clean ─────────────────────────────────────────────────────
clean:
	rm -rf .aws-sam/ __pycache__ .pytest_cache .ruff_cache
	find . -name "*.pyc" -delete

# ── Flask (local dev) ─────────────────────────────────────────
flask:
	FLASK_PORT=5000 .venv/bin/python -m flask_app.run

# Run both servers simultaneously (requires tmux or two terminals)
dev-all:
	@echo "Starting FastAPI on :8000 and Flask on :5000"
	@trap 'kill %1 %2' EXIT; \
		.venv/bin/uvicorn app.main:app --reload --port 8000 & \
		FLASK_PORT=5000 .venv/bin/python -m flask_app.run &\
		wait

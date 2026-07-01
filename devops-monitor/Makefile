.PHONY: up down logs test test-cov lint dev install run-api run-dashboard ci

VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
FLAKE8 := $(VENV)/bin/flake8

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

test:
	$(PYTEST) tests/ -v --cov=api --cov-fail-under=75

test-cov: test

lint:
	$(FLAKE8) api/ dashboard/ tests/

dev:
	@echo "Starting API on :8000 and dashboard on :8501 (Ctrl+C to stop both)"
	@trap 'kill 0' INT TERM; \
	$(VENV)/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 & \
	$(VENV)/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501 & \
	wait

run-api:
	$(VENV)/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	$(VENV)/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

ci: lint test

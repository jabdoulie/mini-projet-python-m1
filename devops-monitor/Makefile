.PHONY: install test test-cov run-api run-dashboard docker-build docker-up docker-down docker-logs ci

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

test:
	$(VENV)/bin/pytest tests/ -v

test-cov:
	$(VENV)/bin/pytest tests/ -v --cov=api --cov-fail-under=75

run-api:
	$(VENV)/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	$(VENV)/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

ci: test-cov

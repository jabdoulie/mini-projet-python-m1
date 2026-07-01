# DevOps Monitoring Dashboard

Dashboard de monitoring DevOps avec une API FastAPI et un frontend Streamlit.

## Prérequis

- Python 3.12+
- Docker et Docker Compose (optionnel, recommandé)
- Make

## Installation locale (sans Docker)

```bash
cd devops-monitor
make install
```

Lancer l'API (terminal 1) :

```bash
make run-api
```

Lancer le dashboard (terminal 2) :

```bash
make run-dashboard
```

- API : http://localhost:8000
- Dashboard : http://localhost:8501
- Documentation OpenAPI : http://localhost:8000/docs

Clé API par défaut : `dev-api-key` (header `X-API-Key`).  
Variable d'environnement : `API_KEY`.

## Lancement avec Docker

```bash
cd devops-monitor
make docker-build
make docker-up
```

Arrêter les conteneurs :

```bash
make docker-down
```

## Tests

```bash
cd devops-monitor
make test
make test-cov   # couverture >= 75 % sur le package api
```

## Structure

```
devops-monitor/
├── api/              # Backend FastAPI
├── dashboard/        # Frontend Streamlit
├── tests/            # Tests pytest
├── Dockerfile.api
├── Dockerfile.dashboard
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## CI

Le pipeline GitHub Actions exécute les tests avec couverture et vérifie le build Docker.

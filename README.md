# DevOps Monitoring Dashboard

Système de monitoring temps réel en Python : API FastAPI + dashboard Streamlit, containerisé avec Docker et validé par un pipeline GitHub Actions.

## Architecture

### Vue d'ensemble

```mermaid
flowchart TB
    subgraph Dev["Développeur"]
        DEV[Git push / PR]
    end

    subgraph GH["GitHub"]
        REPO[(Repository)]
        CI[GitHub Actions\nci-cd.yml]
    end

    subgraph Local["Stack locale — Docker Compose"]
        subgraph API["devops-monitor-api :8000"]
            FAST[FastAPI + Uvicorn]
            MET[metrics.py\npsutil]
            POLL[poller.py\nhealth checks async]
            STORE[(Store serveurs\nen mémoire)]
            FAST --> MET
            FAST --> STORE
            POLL --> STORE
        end

        subgraph DASH["devops-monitor-dashboard :8501"]
            ST[Streamlit]
            TAB1[Onglet Métriques\nKPIs + graphique live]
            TAB2[Onglet Serveurs\ntableau + formulaire]
            ST --> TAB1
            ST --> TAB2
        end

        DASH -->|HTTP REST\n/metrics, /servers| API
    end

    subgraph Monitored["Serveurs monitorés"]
        S1[Serveur 1\nGET /health]
        S2[Serveur 2\nGET /health]
    end

    DEV --> REPO
    REPO --> CI
    CI -->|lint + pytest| API
    CI -->|docker compose build| Local
    POLL -->|httpx async| S1
    POLL -->|httpx async| S2
```

### Flux des données

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant D as Dashboard Streamlit
    participant A as API FastAPI
    participant P as Poller
    participant S as Serveur monitoré

    U->>D: Ouvre http://localhost:8501
    D->>A: GET /metrics (toutes les 2 s)
    A-->>D: cpu_percent, memory_percent, disk_percent
    D-->>U: KPIs + graphique (60 points)

    U->>D: Enregistre un serveur (formulaire)
    D->>A: POST /servers + X-API-Key
    A-->>D: Server créé (status unknown)

    loop Toutes les 10 s
        P->>S: GET /health
        S-->>P: 200 / erreur
        P->>A: Met à jour status UP/DEGRADED/DOWN
    end

    D->>A: GET /servers
    A-->>D: Liste avec statuts colorés
```

### CI/CD (local)

```mermaid
flowchart LR
    PUSH[Push / PR] --> TEST[Job test\nflake8 + pytest ≥ 75 %]
    TEST --> BUILD[Job build\nDocker images]
    BUILD --> LOCAL[Stack locale\nmake up]
```

### Structure du dépôt

```
devops-monitor/
├── api/                  # Backend FastAPI (port 8000)
│   ├── main.py           # Routes, WebSocket, lifespan
│   ├── metrics.py        # Métriques psutil
│   ├── poller.py         # Health checks async
│   └── Dockerfile        # Build multi-stage
├── dashboard/            # Frontend Streamlit (port 8501)
│   ├── app.py
│   └── Dockerfile
├── tests/                # pytest (couverture ≥ 75 %)
├── docker-compose.yml    # Stack locale
├── Makefile              # Commandes standardisées
└── .env.example          # Template des variables d'environnement
```

**Services :**

| Service | URL locale | Rôle |
|---------|------------|------|
| API | http://localhost:8000 | Métriques, serveurs, WebSocket |
| Dashboard | http://localhost:8501 | Visualisation temps réel |
| Docs OpenAPI | http://localhost:8000/docs | Documentation interactive |

## Prérequis

- Python 3.11+
- Docker et Docker Compose
- Make

## Lancement local (Docker — recommandé)

```bash
cd devops-monitor
cp .env.example .env    # ajuster API_KEY si besoin
make up                 # build + démarrage en arrière-plan
make test               # lancer les tests
make logs               # suivre les logs
make down               # arrêter et supprimer les volumes
```

## Lancement local (sans Docker)

```bash
cd devops-monitor
make install
make dev                # API (:8000) + dashboard (:8501) en parallèle
```

Ou dans deux terminaux :

```bash
make run-api
make run-dashboard
```

## Tests et qualité

```bash
make lint               # flake8
make test               # pytest + couverture ≥ 75 %
make ci                 # lint + test (identique à la CI)
```

## Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `API_KEY` | Clé d'accès pour `POST /servers` et `DELETE /servers/{id}` | `dev-api-key` |
| `API_BASE_URL` | URL de l'API vue par le dashboard | `http://api:8000` (Docker) ou `http://localhost:8000` (local) |

> Ne jamais commiter le fichier `.env`. Seul `.env.example` est versionné.

## CI/CD

Le workflow `.github/workflows/ci-cd.yml` exécute sur chaque push et PR :

1. **test** — `flake8` + `pytest --cov=api --cov-fail-under=75`
2. **build** — construction des images Docker (push sur `main` uniquement)

## Endpoints API

| Méthode | Path | Auth | Description |
|---------|------|------|-------------|
| GET | `/health` | public | Liveness probe |
| GET | `/metrics` | public | Snapshot CPU / mémoire / disque |
| WS | `/ws/metrics` | public | Stream JSON toutes les secondes |
| POST | `/servers` | API key | Enregistrer un serveur |
| GET | `/servers` | public | Lister les serveurs |
| DELETE | `/servers/{id}` | API key | Supprimer un serveur |
| POST | `/servers/{id}/check` | public | Health check manuel |

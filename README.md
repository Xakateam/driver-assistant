# Driver Assistant Backend

FastAPI backend for the Moscow Transport hackathon MVP: auth, driver profile,
vehicles, trips, balance, debts, notifications, recommendations, dashboard, and
ML adapters.

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker / Docker Compose
- Sentry

## Run

```bash
docker compose up --build
```

Local API:

```text
Swagger:  http://127.0.0.1:8000/docs
OpenAPI:  http://127.0.0.1:8000/api/v1/openapi.json
Health:   http://127.0.0.1:8000/health
Postgres: localhost:5433
```

Local dev without Docker:

```bash
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

## Environment

| Variable | Default | Description |
| --- | --- | --- |
| `PROJECT_NAME` | `Driver Assistant API` | FastAPI service name. |
| `VERSION` | `alpha` | API version shown in docs. |
| `API_V1_PREFIX` | `/api/v1` | API prefix and OpenAPI path prefix. |
| `DATABASE_URL` | `postgresql+psycopg://driver:driver@localhost:5433/driver_assistant` | SQLAlchemy PostgreSQL URL. |
| `JWT_SECRET_KEY` | `change-me` | Secret for demo JWT tokens. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime. |
| `BACKEND_CORS_ORIGINS` | `*` | Comma-separated CORS origins. |
| `ADMIN_API_KEY` | empty | Optional key for `/api/v1/admin/*`; send as `X-Admin-API-Key`. |
| `SENTRY_DSN` | empty | Enables Sentry when set. |
| `SENTRY_ENVIRONMENT` | `local` | Sentry environment name. |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.0` | Sentry tracing sample rate. |
| `ML_MODELS_DIR` | `ml_models` | Directory with ML artifacts. |
| `FIREBASE_PROJECT_ID` | empty | Firebase project id for FCM. |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | empty | Path to Firebase service account JSON. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | empty | Raw Firebase service account JSON. |
| `NOTIFICATION_SCHEDULER_ENABLED` | `true` | Enables in-process notification ticks. |
| `NOTIFICATION_TICK_INTERVAL_SECONDS` | `1800` | Notification tick interval. |
| `NOTIFICATION_ALLOWED_START_HOUR` | `9` | First hour when scheduled pushes may be sent. |
| `NOTIFICATION_ALLOWED_END_HOUR` | `21` | Hour when scheduled pushes stop. |
| `NOTIFICATION_TIMEZONE` | `Europe/Moscow` | Timezone for quiet hours. |
| `NOTIFICATION_DEDUP_WINDOW_MINUTES` | `180` | Rule dedupe window. |

## Useful Commands

```bash
python -m ruff check app tests
python -m pytest -q
```

Demo auth code is currently:

```text
1234
```

Most endpoints also fall back to the demo user when no bearer token is provided,
which keeps Swagger convenient during the hackathon.

# Driver Assistant Backend

Backend for the Moscow Transport hackathon case: a digital assistant for toll
road drivers. The service is built as a modular FastAPI monolith with
production-like boundaries: auth, users, vehicles, trips, billing,
notifications, recommendations, and ML adapters.

Current state: MVP-ready demo backend. It uses PostgreSQL storage with demo seed
data so the Android team can integrate immediately, while the project already
has Docker and ML adapter boundaries prepared for the next implementation step.

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Pydantic
- Uvicorn
- Docker / Docker Compose
- Sentry
- Optional ML runtime: sklearn/joblib, CatBoost, pandas, numpy

Planned next pieces: Alembic migrations, real JWT signing, randomized OTP, and
real FCM credentials.

## Project Structure

```text
app/
  main.py
  core/
    config.py
    database.py
    security.py
    logging.py
    exceptions.py
    pagination.py
  api/
    router.py
    deps.py
    v1/
      auth.py
      users.py
      vehicles.py
      trips.py
      balance.py
      dashboard.py
      notifications.py
      recommendations.py
      ml.py
      admin.py
  modules/
    auth/
      otp.py
      jwt.py
    users/
    vehicles/
    trips/
    billing/
    dashboard/
    notifications/
      providers/
    forecasting/
    ml/
    recommendations/
```

The repository is currently a working MVP. API endpoints use service layers and
PostgreSQL-backed demo data so Android can start integration before ML wiring is
finished.

## Run Locally

```bash
python -m uvicorn app.main:app --reload
```

Open:

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- API version: http://127.0.0.1:8000/api/v1/version

## Sentry

Sentry is disabled by default. Set `SENTRY_DSN` to enable FastAPI and Starlette
error/performance monitoring:

```bash
SENTRY_DSN=https://public-key@o0.ingest.sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

Leave `SENTRY_DSN` empty for local runs and tests without Sentry reporting.

## Run With Docker

```bash
docker compose up --build
```

This starts the API and PostgreSQL. The current MVP still stores demo data
in PostgreSQL. Local Postgres is exposed on `localhost:5433` to avoid conflicts
with a system Postgres on `5432`.

## Demo Flow

1. Request OTP:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/request-code \
  -H "Content-Type: application/json" \
  -d '{"phone":"+79991234567"}'
```

2. Verify OTP and copy `access_token`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/verify-code \
  -H "Content-Type: application/json" \
  -d '{"phone":"+79991234567","code":"1234"}'
```

3. Use the token:

```bash
curl http://127.0.0.1:8000/api/v1/dashboard \
  -H "Authorization: Bearer <access_token>"
```

For Swagger convenience, endpoints also fall back to a demo user when no bearer
token is provided.

## Core API Contract

Auth:

```text
POST /api/v1/auth/request-code
POST /api/v1/auth/verify-code
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/users/me
```

Vehicles:

```text
GET    /api/v1/vehicles
POST   /api/v1/vehicles
GET    /api/v1/vehicles/{vehicle_id}
PATCH  /api/v1/vehicles/{vehicle_id}
DELETE /api/v1/vehicles/{vehicle_id}
```

Trips and balance:

```text
GET  /api/v1/trips
GET  /api/v1/trips/{trip_id}
GET  /api/v1/balance
POST /api/v1/balance/top-up
GET  /api/v1/balance/transactions
GET  /api/v1/balance/autopay
PATCH /api/v1/balance/autopay
```

Dashboard:

```text
GET /api/v1/dashboard
```

Feed and debts:

```text
GET /api/v1/feed?type=all|trips|payments|overdues
GET /api/v1/debts
GET /api/v1/debts/summary
```

`/dashboard` is shaped for the mobile home screen and includes balance,
autopay, forecast, overdue summary, primary vehicle, recent trips,
notifications, and recommendations. Transponder-specific blocks are intentionally
not modeled yet.

Notifications:

```text
POST  /api/v1/notifications/devices/register
GET   /api/v1/notifications
GET   /api/v1/notifications/{notification_id}
PATCH /api/v1/notifications/{notification_id}/read
POST  /api/v1/notifications/{notification_id}/action
GET   /api/v1/notifications/rules
PATCH /api/v1/notifications/rules/{rule_id}
```

Recommendations and ML:

```text
GET  /api/v1/recommendations
POST /api/v1/recommendations/{recommendation_id}/accept
POST /api/v1/recommendations/{recommendation_id}/decline
POST /api/v1/ml/recalculate-me
POST /api/v1/admin/ml/recalculate-all
GET  /api/v1/admin/ml/status
POST /api/v1/admin/seed
POST /api/v1/admin/notifications/tick
```

## Notification Engine

Notifications are stored in PostgreSQL. Firebase Cloud Messaging is treated as a
delivery provider, not as the source of truth.

```text
Scheduler -> NotificationRules -> notifications table -> FCM provider -> Android
```

Planned notification types:

- `low_balance_forecast`
- `monthly_spend_forecast`
- `recurring_trip_reminder`
- `recommendation_available`
- `topup_success`
- `debt_warning`

The first version can use an in-process scheduler. Later it can be replaced by
Celery Beat, Redis Queue, or a separate worker without changing the public API.

## ML Integration Contract

ML artifacts from
[`322kirpich/ml_moscow_transport`](https://github.com/322kirpich/ml_moscow_transport/tree/main)
are stored under `ml_models/` and loaded lazily. If optional ML dependencies are
not installed, the API keeps working with deterministic fallback heuristics.

```text
ml_models/
  kmeans_model.joblib
  scaler.joblib
  spend_predictor.cbm
  ctr_model.cbm
  metadata.json
```

Install local ML dependencies only when real artifact execution is needed:

```bash
python -m pip install -e ".[ml]"
```

The release Docker image installs `.[ml]` and includes the artifacts.

Segmentation:

```text
input:  trip_frequency, avg_check, weekend_share, is_delayed_payment
output: ml_cluster_id, ml_cluster_name
```

Spend prediction:

```text
input:  trips_count, total_spent, ml_cluster_id
output: predicted_spend_next_month
```

Recommendation CTR:

```text
input:  current_balance, debt_amount, ml_cluster_id,
        predicted_spend_next_month, category_id
output: predicted_ctr
```

Backend storage additions on `users`:

```text
ml_cluster_id
ml_cluster_name
predicted_spend_next_month
favorite_route_name
ml_model_version
ml_updated_at
```

Recalculate current user:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ml/recalculate-me \
  -H "Authorization: Bearer <access_token>"
```

Check artifact/dependency status:

```text
GET /api/v1/admin/ml/status
```

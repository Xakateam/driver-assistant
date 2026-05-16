# Сириус: backend финансового ассистента водителя

FastAPI-сервис для MVP на хакатон: авторизация, профиль водителя, автомобили,
поездки, баланс, задолженности, уведомления, рекомендации, ML-интеграция,
дашборд и админ-панель для демо.

## Стек

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker / Docker Compose
- Firebase Cloud Messaging
- Sentry

## Быстрый запуск

```bash
docker compose up --build
```

Адреса локально:

```text
Swagger:  http://127.0.0.1:8000/docs
Admin:    http://127.0.0.1:8000/admin-panel
OpenAPI:  http://127.0.0.1:8000/api/v1/openapi.json
Health:   http://127.0.0.1:8000/health
Postgres: localhost:5433
```

Запуск без Docker:

```bash
python -m pip install -e ".[dev,ml]"
python -m uvicorn app.main:app --reload
```

## Переменные окружения

| Переменная | По умолчанию | Для чего нужна |
| --- | --- | --- |
| `PROJECT_NAME` | `Driver Assistant API` | Название сервиса в Swagger. |
| `VERSION` | `alpha` | Версия API. |
| `API_V1_PREFIX` | `/api/v1` | Префикс API. |
| `DATABASE_URL` | `postgresql+psycopg://driver:driver@localhost:5433/driver_assistant` | Подключение к PostgreSQL. |
| `JWT_SECRET_KEY` | `change-me` | Секрет для JWT. В production обязательно заменить. |
| `JWT_ALGORITHM` | `HS256` | Алгоритм подписи JWT. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Время жизни access token. |
| `BACKEND_CORS_ORIGINS` | `*` | Разрешенные CORS origins через запятую. |
| `ADMIN_API_KEY` | пусто | Опциональная защита `/api/v1/admin/*`; передается в `X-Admin-API-Key`. |
| `SENTRY_DSN` | пусто | Включает Sentry. |
| `SENTRY_ENVIRONMENT` | `local` | Окружение для Sentry. |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.0` | Доля trace-событий Sentry. |
| `ML_MODELS_DIR` | `ml_models` | Папка с ML-артефактами. |
| `FIREBASE_PROJECT_ID` | пусто | Firebase project id для FCM. |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | пусто | Путь к service account JSON. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | пусто | Service account JSON строкой. |
| `NOTIFICATION_SCHEDULER_ENABLED` | `true` | Включает фоновые уведомления. |
| `NOTIFICATION_TICK_INTERVAL_SECONDS` | `120` | Интервал проверки правил уведомлений. |
| `NOTIFICATION_ALLOWED_START_HOUR` | `9` | Начало окна фоновых push-уведомлений. |
| `NOTIFICATION_ALLOWED_END_HOUR` | `21` | Конец окна фоновых push-уведомлений. |
| `NOTIFICATION_TIMEZONE` | `Europe/Moscow` | Таймзона окна уведомлений. |
| `NOTIFICATION_DEDUP_WINDOW_MINUTES` | `180` | Окно дедупликации фоновых уведомлений. |

## Проверки

```bash
python -m ruff check app tests
python -m pytest -q
```

## Демо

- Код авторизации в MVP: `1234`.
- Для удобства Swagger часть endpoint'ов работает с demo user без bearer token.
- Админ-панель: `/admin-panel`.
- Ручная рассылка push: `POST /api/v1/admin/notifications/send`.
- Создание поездки/долга из админки сразу отправляет push пользователю.

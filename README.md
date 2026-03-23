# Timer Service

A webhook scheduling service. Create a timer with a URL and duration; when the timer fires, the URL is called via HTTP POST.

## Quick Start

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`.

---

## API

### `POST /timer`

Create a new timer.

**Request body:**
```json
{
  "url": "https://your-server.com/webhook",
  "hours": 0,
  "minutes": 5,
  "seconds": 0
}
```

**Response `201`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time_left": 300
}
```

- `time_left` — seconds until the webhook fires
- `hours + minutes + seconds` must sum to > 0
- `minutes` and `seconds` must be 0–59

---

### `GET /timer/{timer_id}`

Get remaining time on a timer.

**Response `200`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time_left": 142
}
```

- `time_left` is `0` when the timer has expired
- Returns `404` if the timer ID is unknown

---

### `GET /health`

Liveness probe. Returns `{"status": "ok"}`.

---

## Webhook Payload

When a timer fires, the service sends an HTTP `POST` to the configured URL with:

```json
{
  "timer_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Failed calls (5xx or network errors) are retried up to **3 times** with a 5-second delay. 4xx responses are not retried.

---

## Scaling

**Horizontal API scaling:**
```bash
docker compose up --scale api=3
```
Put Nginx / Traefik in front as a load balancer.

**Horizontal worker scaling:**
```bash
docker compose up --scale worker=3
```

All state lives in Redis, so any number of API or worker instances can run simultaneously.

---

## Persistence / Crash Recovery

- Celery tasks are stored in **Redis** with `task_acks_late=True` — the broker holds the task until a worker *acknowledges* successful execution.
- If a worker crashes mid-execution, the task is re-queued automatically.
- If a worker is down when a timer's ETA arrives, the task fires **immediately** when the worker comes back online.
- Redis itself is configured with `appendonly yes` (AOF persistence), so tasks survive a Redis restart.

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

No Redis or Celery broker needed — all external services are mocked.

---

## Assumptions/Decisions

- 
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.schemas import TimerCreateRequest
from app.main import app

client = TestClient(app)

class TestTimerCreateRequestSchema:

    def test_valid_input_computes_total_seconds(self):
        req = TimerCreateRequest(url="http://example.com/hook", hours=1, minutes=30, seconds=0)
        assert req.total_seconds() == 5400

    def test_seconds_only(self):
        req = TimerCreateRequest(url="http://example.com/hook", seconds=45)
        assert req.total_seconds() == 45

    def test_all_fields_zero_is_valid_schema(self):
        req = TimerCreateRequest(url="http://example.com/hook")
        assert req.total_seconds() == 0

    def test_negative_hours_rejected(self):
        with pytest.raises(Exception):
            TimerCreateRequest(url="http://example.com/hook", hours=-1)

    def test_negative_minutes_rejected(self):
        with pytest.raises(Exception):
            TimerCreateRequest(url="http://example.com/hook", minutes=-1)
    
    def test_negative_seconds_rejected(self):
        with pytest.raises(Exception):
            TimerCreateRequest(url="http://example.com/hook", seconds=-1)

    def test_minutes_over_59_rejected(self):
        with pytest.raises(Exception):
            TimerCreateRequest(url="http://example.com/hook", minutes=60)
    
    def test_seconds_over_59_rejected(self):
        with pytest.raises(Exception):
            TimerCreateRequest(url="http://example.com/hook", seconds=60)

    def test_invalid_url_rejected(self):
        with pytest.raises(Exception):
            TimerCreateRequest(url="not-a-url", seconds=10)

class TestCreateTimer:

    @patch("app.api.routes.fire_webhook")
    @patch("app.api.routes.get_redis")
    def test_returns_201_with_id_and_time_left(self, mock_get_redis, mock_fire_webhook):
        mock_get_redis.return_value = MagicMock()
        mock_fire_webhook.return_value = MagicMock()

        resp = client.post("/timer", json={"url": "http://example.com/hook", "seconds": 30})

        assert resp.status_code == 201
        body = resp.json()
        assert "id" in body
        assert body["time_left"] == 30

    @patch("app.api.routes.fire_webhook")
    @patch("app.api.routes.get_redis")
    def test_response_id_is_valid_uuid(self, mock_get_redis, mock_fire_webhook):
        mock_get_redis.return_value = MagicMock()
        mock_fire_webhook.return_value = MagicMock()

        resp = client.post("/timer", json={"url": "http://example.com/hook", "seconds": 10})
        uuid.UUID(resp.json()["id"])

    @patch("app.api.routes.fire_webhook")
    @patch("app.api.routes.get_redis")
    def test_time_left_reflects_all_duration_fields(self, mock_get_redis, mock_fire_webhook):
        mock_get_redis.return_value = MagicMock()
        mock_fire_webhook.return_value = MagicMock()

        resp = client.post(
            "/timer", 
            json={"url": "http://example.com/hook", "hours": 10, "minutes": 10, "seconds": 10},
        )
        assert resp.json()["time_left"] == 36610

    @patch("app.api.routes.fire_webhook")
    @patch("app.api.routes.get_redis")
    def test_celery_task_scheduled_with_eta(self, mock_get_redis, mock_fire_webhook):
        mock_get_redis.return_value = MagicMock()
        mock_apply_async = MagicMock()
        mock_fire_webhook.apply_async = mock_apply_async

        client.post("/timer", json={"url": "http://example.com/hook", "seconds": 50})

        mock_apply_async.assert_called_once()
        _, kwargs = mock_apply_async.call_args
        assert "eta" in kwargs
        assert isinstance(kwargs["eta"], datetime)
       
    @patch("app.api.routes.fire_webhook")
    @patch("app.api.routes.get_redis")
    def test_fire_at_timestamp_stored_in_redis(self, mock_get_redis, mock_fire_webhook):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_fire_webhook.return_value = MagicMock()

        resp = client.post("/timer", json={"url": "http://example.com/hook", "seconds": 10})
        timer_id = resp.json()["id"]

        mock_redis.set.assert_called_once()
        key_arg = mock_redis.set.call_args[0][0]
        assert timer_id in key_arg

    def test_zero_duration_rejected_with_400(self):
        resp = client.post(
            "/timer", 
            json={"url": "http://example.com/hook", "hours": 0, "minutes": 0, "seconds": 0},
        )
        assert resp.status_code == 400

    def test_invalid_url_rejected_with_422(self):
        resp = client.post(
            "/timer", 
            json={"url": "not-a-url", "hours": 1},
        )
        assert resp.status_code == 422

    def test_negative_seconds_rejected_with_422(self):
        resp = client.post(
            "/timer", 
            json={"url": "http://example.com/hook", "seconds": -5},
        )
        assert resp.status_code == 422

    def test_minutes_over_59_rejected_with_422(self):
        resp = client.post(
            "/timer", 
            json={"url": "http://example.com/hook", "minutes": 60},
        )
        assert resp.status_code == 422

    def test_non_integer_seconds_rejected_with_422(self):
        resp = client.post(
            "/timer", 
            json={"url": "http://example.com/hook", "seconds": "abc"},
        )
        assert resp.status_code == 422

class TestGetTimer:

    @patch("app.api.routes.get_redis")
    def test_returns_time_left_for_active_timer(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        future = datetime.now(timezone.utc) + timedelta(seconds=120)
        mock_redis.get.return_value = future.isoformat()

        resp = client.get(f"/timer/{uuid.uuid4()}")

        assert resp.status_code == 200
        assert 119 <= resp.json()["time_left"] <= 120

    @patch("app.api.routes.get_redis")
    def test_returns_timer_returns_zero(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        past = datetime.now(timezone.utc) - timedelta(seconds=5)
        mock_redis.get.return_value = past.isoformat()

        resp = client.get(f"/timer/{uuid.uuid4()}")

        assert resp.status_code == 200
        assert resp.json()["time_left"] == 0
    
    @patch("app.api.routes.get_redis")
    def test_unknown_timer_returns_404(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = None

        resp = client.get(f"/timer/{uuid.uuid4()}")

        assert resp.status_code == 404

    @patch("app.api.routes.get_redis")
    def test_response_contains_correct_id(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        future = datetime.now(timezone.utc) + timedelta(seconds=60)
        mock_redis.get.return_value = future.isoformat()

        timer_id = str(uuid.uuid4())
        resp = client.get(f"/timer/{timer_id}")

        assert resp.json()["id"] == timer_id


class TestFireWebhookTask:

    @patch("app.tasks.webhook.get_redis")
    @patch("app.tasks.webhook.httpx.Client")
    def test_successful_webhook_call(self, mock_client_cls, mock_get_redis):
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_get_redis.return_value = mock_redis

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response

        from app.tasks.webhook import fire_webhook
        result = fire_webhook.run(url="http://example.com/hook", timer_id="abc-123")

        assert result["status"] == "ok"
        assert result["http_status"] == 200

    @patch("app.tasks.webhook.get_redis")
    @patch("app.tasks.webhook.httpx.Client")
    def test_idempotency_guard_prevents_double_fire(self, mock_client_cls, mock_get_redis):
        mock_redis = MagicMock()
        mock_redis.set.return_value = None
        mock_get_redis.return_value = mock_redis

        from app.tasks.webhook import fire_webhook
        result = fire_webhook.run(url="http://example.com/hook", timer_id="abc-123")

        assert result["status"] == "already_fired"
        mock_client_cls.assert_not_called()

    @patch("app.tasks.webhook.get_redis")
    @patch("app.tasks.webhook.httpx.Client")
    def test_4xx_does_not_retry_and_releases_no_lock(self, mock_client_cls, mock_get_redis):
        import httpx as _httpx

        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_get_redis.return_value = mock_redis

        mock_http_response = MagicMock()
        mock_http_response.status_code = 404
        error = _httpx.HTTPStatusError(
            "not found", request=MagicMock(), response=mock_http_response
        )
        mock_http_response.raise_for_status.side_effect = error
        mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_http_response

        from app.tasks.webhook import fire_webhook
        result = fire_webhook.run(url="http://example.com/hook", timer_id="abc-123")

        assert result["status"] == "client_error"
        assert result["http_status"] == 404
        mock_client_cls.delete.assert_not_called()

    @patch("app.tasks.webhook.get_redis")
    @patch("app.tasks.webhook.httpx.Client")
    def test_5xx_releases_lock_for_retry(self, mock_client_cls, mock_get_redis):
        import httpx as _httpx

        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_get_redis.return_value = mock_redis

        mock_http_response = MagicMock()
        mock_http_response.status_code = 500
        error = _httpx.HTTPStatusError(
            "internal error", request=MagicMock(), response=mock_http_response
        )
        mock_http_response.raise_for_status.side_effect = error
        mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_http_response

        from app.tasks.webhook import fire_webhook
        with pytest.raises(Exception):
            fire_webhook.run(url="http://example.com/hook", timer_id="abc-123")

        mock_redis.delete.assert_called_once()
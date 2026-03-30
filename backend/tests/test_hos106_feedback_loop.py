"""Tests for HOS-106 — WhatsApp Feedback Loop (👍/👎 → MemoryService).

Covers:
- parse_feedback() — emoji + text aliases for thumbs-up / thumbs-down
- FeedbackType enum values
- Twilio inbound webhook routing: 👍/👎 → feedback ack TwiML, NOT action log
- Background task _bg_store_feedback: calls MemoryService.learn_from_feedback
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.schemas.webhook import FeedbackType
from app.services.action_logger import parse_feedback


# ===========================================================================
# parse_feedback — unit tests
# ===========================================================================

class TestParseFeedback:
    """Verify all recognised thumbs-up / thumbs-down aliases."""

    # -- Thumbs-up --

    def test_thumbs_up_emoji(self):
        assert parse_feedback("👍") == FeedbackType.thumbs_up

    def test_checkmark_emoji(self):
        assert parse_feedback("✅") == FeedbackType.thumbs_up

    def test_yes_lowercase(self):
        assert parse_feedback("yes") == FeedbackType.thumbs_up

    def test_good_lowercase(self):
        assert parse_feedback("good") == FeedbackType.thumbs_up

    def test_correct_lowercase(self):
        assert parse_feedback("correct") == FeedbackType.thumbs_up

    def test_parfait_french(self):
        assert parse_feedback("parfait") == FeedbackType.thumbs_up

    def test_ok_alias(self):
        assert parse_feedback("ok") == FeedbackType.thumbs_up

    def test_oui_french(self):
        assert parse_feedback("oui") == FeedbackType.thumbs_up

    def test_thumbs_up_with_whitespace(self):
        assert parse_feedback("  👍  ") == FeedbackType.thumbs_up

    # -- Thumbs-down --

    def test_thumbs_down_emoji(self):
        assert parse_feedback("👎") == FeedbackType.thumbs_down

    def test_cross_emoji(self):
        assert parse_feedback("❌") == FeedbackType.thumbs_down

    def test_no_lowercase(self):
        assert parse_feedback("no") == FeedbackType.thumbs_down

    def test_bad_lowercase(self):
        assert parse_feedback("bad") == FeedbackType.thumbs_down

    def test_wrong_lowercase(self):
        assert parse_feedback("wrong") == FeedbackType.thumbs_down

    def test_incorrect_lowercase(self):
        assert parse_feedback("incorrect") == FeedbackType.thumbs_down

    def test_faux_french(self):
        assert parse_feedback("faux") == FeedbackType.thumbs_down

    def test_non_french(self):
        assert parse_feedback("non") == FeedbackType.thumbs_down

    # -- Not a feedback signal --

    def test_accept_is_not_feedback(self):
        assert parse_feedback("accept") == FeedbackType.none

    def test_reject_is_not_feedback(self):
        assert parse_feedback("reject") == FeedbackType.none

    def test_arbitrary_text_returns_none(self):
        assert parse_feedback("Why did you recommend 2 servers?") == FeedbackType.none

    def test_empty_string_returns_none(self):
        assert parse_feedback("") == FeedbackType.none

    def test_case_insensitive_good(self):
        assert parse_feedback("GOOD") == FeedbackType.thumbs_up

    def test_case_insensitive_wrong(self):
        assert parse_feedback("WRONG") == FeedbackType.thumbs_down


# ===========================================================================
# Webhook integration — feedback routing
# ===========================================================================

def _make_webhook_app() -> FastAPI:
    from app.api.routes.webhook import router

    app = FastAPI()
    app.include_router(router)
    return app


async def _fake_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    yield session


@pytest.fixture
def feedback_client(monkeypatch):
    """TestClient with signature validation skipped and DB mocked."""
    monkeypatch.setenv("TWILIO_SKIP_SIGNATURE_VALIDATION", "true")

    from app.db.session import get_db

    app = _make_webhook_app()
    app.dependency_overrides[get_db] = _fake_db

    with TestClient(app) as client:
        yield client


class TestFeedbackWebhookRouting:
    """Verify that 👍/👎 messages are routed to the feedback ack, not action log."""

    def test_thumbs_up_emoji_returns_feedback_ack(self, feedback_client):
        with patch("app.api.routes.webhook._bg_store_feedback", new=AsyncMock()):
            resp = feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "👍", "To": "+14155238886"},
            )
        assert resp.status_code == 200
        assert "improve future forecasts" in resp.text or "Thanks for the feedback" in resp.text

    def test_thumbs_down_emoji_returns_feedback_ack(self, feedback_client):
        with patch("app.api.routes.webhook._bg_store_feedback", new=AsyncMock()):
            resp = feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "👎", "To": "+14155238886"},
            )
        assert resp.status_code == 200
        assert "inaccurate" in resp.text or "adjust future" in resp.text

    def test_yes_alias_returns_thumbs_up_ack(self, feedback_client):
        with patch("app.api.routes.webhook._bg_store_feedback", new=AsyncMock()):
            resp = feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "yes", "To": "+14155238886"},
            )
        assert resp.status_code == 200
        assert "improve future forecasts" in resp.text or "Thanks" in resp.text

    def test_wrong_alias_returns_thumbs_down_ack(self, feedback_client):
        with patch("app.api.routes.webhook._bg_store_feedback", new=AsyncMock()):
            resp = feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "wrong", "To": "+14155238886"},
            )
        assert resp.status_code == 200
        assert "inaccurate" in resp.text or "adjust" in resp.text

    def test_feedback_returns_xml_content_type(self, feedback_client):
        with patch("app.api.routes.webhook._bg_store_feedback", new=AsyncMock()):
            resp = feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "👍", "To": "+14155238886"},
            )
        assert "application/xml" in resp.headers.get("content-type", "")

    def test_feedback_does_not_call_action_logger(self, feedback_client):
        """Action logger must NOT be invoked for feedback messages."""
        mock_log = AsyncMock()
        with patch("app.api.routes.webhook.ActionLoggerService.log_action", mock_log), \
             patch("app.api.routes.webhook._bg_store_feedback", new=AsyncMock()):
            feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "👍", "To": "+14155238886"},
            )
        mock_log.assert_not_called()

    def test_accept_still_routes_to_action_logger_not_feedback(self, feedback_client):
        """'accept' must NOT be treated as feedback — routes to ActionLoggerService."""
        mock_log = AsyncMock(
            return_value={"status": "logged", "recommendation_id": str(uuid.uuid4()), "action": "accepted"}
        )
        with patch("app.api.routes.webhook.ActionLoggerService.log_action", mock_log):
            resp = feedback_client.post(
                "/webhooks/twilio/inbound",
                data={"From": "+33600000001", "Body": "accept", "To": "+14155238886"},
            )
        assert resp.status_code == 200
        mock_log.assert_called_once()


# ===========================================================================
# _bg_store_feedback — background task unit tests
# ===========================================================================

class TestBgStoreFeedback:
    """Verify feedback is stored in MemoryService with correct polarity."""

    @pytest.mark.asyncio
    async def test_thumbs_up_calls_learn_from_feedback_with_followed(self):
        from app.api.routes.webhook import _bg_store_feedback

        profile = MagicMock()
        profile.tenant_id = "hotel-test"

        db = AsyncMock()
        profile_result = MagicMock()
        profile_result.scalars.return_value.first.return_value = profile
        db.execute = AsyncMock(return_value=profile_result)

        with patch("app.services.memory_service.MemoryService") as MockMemory:
            mock_mem_instance = AsyncMock()
            MockMemory.return_value = mock_mem_instance

            await _bg_store_feedback("+33600000001", FeedbackType.thumbs_up, db)

            mock_mem_instance.learn_from_feedback.assert_awaited_once_with(
                "hotel-test", "latest_alert", "followed"
            )

    @pytest.mark.asyncio
    async def test_thumbs_down_calls_learn_from_feedback_with_rejected(self):
        from app.api.routes.webhook import _bg_store_feedback

        profile = MagicMock()
        profile.tenant_id = "hotel-test"

        db = AsyncMock()
        profile_result = MagicMock()
        profile_result.scalars.return_value.first.return_value = profile
        db.execute = AsyncMock(return_value=profile_result)

        with patch("app.services.memory_service.MemoryService") as MockMemory:
            mock_mem_instance = AsyncMock()
            MockMemory.return_value = mock_mem_instance

            await _bg_store_feedback("+33600000001", FeedbackType.thumbs_down, db)

            mock_mem_instance.learn_from_feedback.assert_awaited_once_with(
                "hotel-test", "latest_alert", "rejected"
            )

    @pytest.mark.asyncio
    async def test_unknown_phone_uses_unknown_tenant_id(self):
        from app.api.routes.webhook import _bg_store_feedback

        db = AsyncMock()
        profile_result = MagicMock()
        profile_result.scalars.return_value.first.return_value = None  # no profile found
        db.execute = AsyncMock(return_value=profile_result)

        with patch("app.services.memory_service.MemoryService") as MockMemory:
            mock_mem_instance = AsyncMock()
            MockMemory.return_value = mock_mem_instance

            # Should not raise; falls back to tenant_id="unknown"
            await _bg_store_feedback("+33600000099", FeedbackType.thumbs_up, db)

            mock_mem_instance.learn_from_feedback.assert_awaited_once_with(
                "unknown", "latest_alert", "followed"
            )

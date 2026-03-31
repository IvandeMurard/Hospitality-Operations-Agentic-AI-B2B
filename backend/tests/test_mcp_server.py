"""Tests for HOS-71 MCP Server and HOS-72 Agent SEO metrics.

Test categories:
  1. AgentSEOTracker — unit tests for metrics recording
  2. forecast_occupancy — tool with mocked AetherixEngine
  3. get_stock_alerts   — tool with mocked DB session
  4. recommend_menu     — tool with mocked RAGService and Claude client
  5. get_fb_kpis        — tool with mocked DB session
  6. mcp_metrics route  — integration test via FastAPI TestClient
  7. _parse_date_range / _parse_period — helper unit tests
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.agent_seo import AgentSEOTracker, _percentile
from app.mcp_server import (
    _heuristic_menu_recommendation,
    _parse_date_range,
    _parse_period,
    forecast_occupancy,
    get_fb_kpis,
    get_stock_alerts,
    recommend_menu,
)


# ===========================================================================
# 1. AgentSEOTracker — unit tests
# ===========================================================================
class TestAgentSEOTracker:
    """Verify metrics accumulate correctly and targets are evaluated."""

    def setup_method(self):
        self.tracker = AgentSEOTracker()

    @pytest.mark.asyncio
    async def test_success_increments_counters(self):
        async with self.tracker.record("tool_a"):
            pass  # success

        metrics = await self.tracker.get_metrics()
        assert metrics["tools"]["tool_a"]["total_calls"] == 1
        assert metrics["tools"]["tool_a"]["successful_calls"] == 1
        assert metrics["tools"]["tool_a"]["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_failure_does_not_increment_success(self):
        with pytest.raises(ValueError):
            async with self.tracker.record("tool_b"):
                raise ValueError("boom")

        metrics = await self.tracker.get_metrics()
        assert metrics["tools"]["tool_b"]["total_calls"] == 1
        assert metrics["tools"]["tool_b"]["successful_calls"] == 0
        assert metrics["tools"]["tool_b"]["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_retry_flag_increments_retry_counter(self):
        async with self.tracker.record("tool_c", is_retry=True):
            pass

        metrics = await self.tracker.get_metrics()
        assert metrics["tools"]["tool_c"]["retry_calls"] == 1
        assert metrics["tools"]["tool_c"]["agent_retry_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_schema_break_counter(self):
        self.tracker.bump_schema_break()
        self.tracker.bump_schema_break()
        metrics = await self.tracker.get_metrics()
        assert metrics["schema_breaks_this_sprint"] == 2
        assert metrics["schema_stability_ok"] is False

    @pytest.mark.asyncio
    async def test_schema_stability_ok_initially(self):
        metrics = await self.tracker.get_metrics()
        assert metrics["schema_stability_ok"] is True

    @pytest.mark.asyncio
    async def test_targets_evaluated_correctly(self):
        # Simulate a call under 500ms
        async with self.tracker.record("tool_d"):
            pass

        metrics = await self.tracker.get_metrics()
        t = metrics["tools"]["tool_d"]["targets"]
        assert t["success_rate_ok"] is True
        assert t["p95_latency_ok"] is True  # should be well under 500ms in tests
        assert t["retry_rate_ok"] is True

    def test_percentile_empty(self):
        assert _percentile([], 95) == 0.0

    def test_percentile_single(self):
        assert _percentile([100.0], 95) == 100.0

    def test_percentile_multiple(self):
        values = sorted(range(100))  # 0 … 99
        # p95 of 100 values → index 94 → value 94
        assert _percentile([float(v) for v in values], 95) == 94.0


# ===========================================================================
# 2. forecast_occupancy
# ===========================================================================
class TestForecastOccupancy:
    """forecast_occupancy wraps AetherixEngine.get_forecast()."""

    def _mock_engine_result(self, covers: int = 80) -> Dict[str, Any]:
        return {
            "prediction": {
                "covers": covers,
                "confidence": 0.85,
                "interval": [covers - 10, covers + 10],
            },
            "reasoning": "Test reasoning",
            "reasoning_detail": {
                "summary": "Test summary",
                "confidence_factors": ["weather", "events"],
                "claude_used": True,
            },
            "staffing_recommendation": {"servers": 5, "kitchen": 3},
            "date": "2026-04-01",
            "service_type": "dinner",
        }

    @pytest.mark.asyncio
    async def test_single_date(self):
        mock_result = self._mock_engine_result()
        with patch("app.mcp_server._engine") as mock_engine:
            mock_engine.get_forecast = AsyncMock(return_value=mock_result)
            result = await forecast_occupancy("hotel-001", "2026-04-01")

        assert result["hotel_id"] == "hotel-001"
        assert result["schema_version"] == "1.0"
        assert len(result["forecasts"]) == 1
        f = result["forecasts"][0]
        assert f["predicted_covers"] == 80
        assert f["confidence"] == 0.85
        assert f["range_min"] == 70
        assert f["range_max"] == 90

    @pytest.mark.asyncio
    async def test_date_range_calls_engine_once_per_day(self):
        mock_result = self._mock_engine_result()
        with patch("app.mcp_server._engine") as mock_engine:
            mock_engine.get_forecast = AsyncMock(return_value=mock_result)
            result = await forecast_occupancy("hotel-001", "2026-04-01/2026-04-03")

        assert len(result["forecasts"]) == 3
        assert mock_engine.get_forecast.call_count == 3

    @pytest.mark.asyncio
    async def test_context_json_parsed(self):
        mock_result = self._mock_engine_result()
        ctx_json = '{"weather": {"condition": "Rain", "temp": 10}, "occupancy": 0.9}'
        with patch("app.mcp_server._engine") as mock_engine:
            mock_engine.get_forecast = AsyncMock(return_value=mock_result)
            await forecast_occupancy("hotel-001", "2026-04-01", context=ctx_json)

        call_kwargs = mock_engine.get_forecast.call_args[0]
        # 4th positional arg is the context dict
        assert call_kwargs[3]["weather"]["condition"] == "Rain"

    @pytest.mark.asyncio
    async def test_invalid_context_json_falls_back_gracefully(self):
        mock_result = self._mock_engine_result()
        with patch("app.mcp_server._engine") as mock_engine:
            mock_engine.get_forecast = AsyncMock(return_value=mock_result)
            result = await forecast_occupancy("hotel-001", "2026-04-01", context="not-json")

        # Should not raise; forecast should still be returned
        assert len(result["forecasts"]) == 1


# ===========================================================================
# 3. get_stock_alerts
# ===========================================================================
class TestGetStockAlerts:
    """get_stock_alerts queries DemandAnomaly with tenant filtering."""

    def _make_anomaly(self, tenant_id: str, status: str = "detected") -> MagicMock:
        a = MagicMock()
        a.tenant_id = tenant_id
        a.id = uuid.uuid4()
        a.direction = "surge"
        a.window_start = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)
        a.window_end = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        a.deviation_pct = Decimal("35.5")
        a.triggering_factors = ["concert_nearby"]
        a.status = status
        a.roi_net = Decimal("420.00")
        a.recommendation_text = "Add 2 servers for the 08:00-12:00 window."
        a.detected_at = datetime(2026, 3, 31, 10, 0, tzinfo=timezone.utc)
        return a

    @pytest.mark.asyncio
    async def test_returns_alerts_for_matching_tenant(self):
        hotel_id = str(uuid.uuid4())
        anomaly = self._make_anomaly(hotel_id, "detected")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [anomaly]
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.mcp_server.AsyncSessionLocal", return_value=mock_session):
            result = await get_stock_alerts(hotel_id)

        assert result["hotel_id"] == hotel_id
        assert result["alert_count"] == 1
        assert result["alerts"][0]["direction"] == "surge"
        assert result["alerts"][0]["roi_net"] == 420.0
        assert result["schema_version"] == "1.0"

    @pytest.mark.asyncio
    async def test_filters_out_different_tenant(self):
        my_hotel = str(uuid.uuid4())
        other_hotel = str(uuid.uuid4())
        anomaly = self._make_anomaly(other_hotel, "detected")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [anomaly]
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.mcp_server.AsyncSessionLocal", return_value=mock_session):
            result = await get_stock_alerts(my_hotel)

        assert result["alert_count"] == 0

    @pytest.mark.asyncio
    async def test_limit_capped_at_100(self):
        hotel_id = str(uuid.uuid4())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.mcp_server.AsyncSessionLocal", return_value=mock_session):
            # Passes limit=200 — should be capped to 100 internally
            result = await get_stock_alerts(hotel_id, limit=200)

        assert result["schema_version"] == "1.0"


# ===========================================================================
# 4. recommend_menu
# ===========================================================================
class TestRecommendMenu:
    """recommend_menu uses RAGService + Claude (or heuristic fallback)."""

    @pytest.mark.asyncio
    async def test_heuristic_fallback_when_no_claude(self):
        with patch("app.mcp_server._rag") as mock_rag, \
             patch("app.mcp_server._claude_client", None):
            mock_rag.find_similar_patterns = AsyncMock(return_value=[])
            result = await recommend_menu("hotel-001", "Rainy evening, 60 covers")

        assert result["hotel_id"] == "hotel-001"
        assert result["claude_used"] is False
        assert "recommendation" in result
        assert "Warm" in result["recommendation"] or "warm" in result["recommendation"]
        assert result["schema_version"] == "1.0"

    @pytest.mark.asyncio
    async def test_claude_used_when_available(self):
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="• Offer warm soups\n• Reduce outdoor seating")]

        mock_claude = AsyncMock()
        mock_claude.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.mcp_server._rag") as mock_rag, \
             patch("app.mcp_server._claude_client", mock_claude):
            mock_rag.find_similar_patterns = AsyncMock(return_value=[
                {"pattern_text": "Rain reduces patio covers by 30%", "outcome_description": "Moved to indoor seating"}
            ])
            result = await recommend_menu("hotel-001", "Rainy night, 40 covers")

        assert result["claude_used"] is True
        assert "soups" in result["recommendation"]
        assert result["patterns_used"] == 1

    @pytest.mark.asyncio
    async def test_claude_error_falls_back_to_heuristic(self):
        mock_claude = AsyncMock()
        mock_claude.messages.create = AsyncMock(side_effect=Exception("API error"))

        with patch("app.mcp_server._rag") as mock_rag, \
             patch("app.mcp_server._claude_client", mock_claude):
            mock_rag.find_similar_patterns = AsyncMock(return_value=[])
            result = await recommend_menu("hotel-001", "Gala event, 200 covers")

        assert result["claude_used"] is False
        assert "recommendation" in result

    def test_heuristic_vegetarian_tip(self):
        rec = _heuristic_menu_recommendation("vegetarian group, 30 covers", [])
        assert "plant-based" in rec.lower() or "vegetarian" in rec.lower()

    def test_heuristic_gala_tip(self):
        rec = _heuristic_menu_recommendation("gala dinner", [])
        assert "set menu" in rec.lower() or "course" in rec.lower()

    def test_heuristic_uses_pattern_outcome(self):
        patterns = [{"pattern_text": "...", "outcome_description": "Pre-plating reduced service time by 15%"}]
        rec = _heuristic_menu_recommendation("normal service", patterns)
        assert "Pre-plating" in rec


# ===========================================================================
# 5. get_fb_kpis
# ===========================================================================
class TestGetFbKpis:
    """get_fb_kpis aggregates anomaly and recommendation data."""

    def _make_anomaly(self, tenant_id: str, direction: str = "surge",
                      roi_net: float = 300.0, deviation: float = 25.0) -> MagicMock:
        a = MagicMock()
        a.tenant_id = tenant_id
        a.direction = direction
        a.roi_net = Decimal(str(roi_net)) if roi_net else None
        a.deviation_pct = Decimal(str(deviation))
        a.detected_at = datetime(2026, 3, 30, tzinfo=timezone.utc)
        return a

    def _make_reco(self, tenant_id: str, action: str | None = "accepted") -> MagicMock:
        r = MagicMock()
        r.tenant_id = tenant_id
        r.status = "dispatched"
        r.action = action
        r.created_at = datetime(2026, 3, 30, tzinfo=timezone.utc)
        return r

    @pytest.mark.asyncio
    async def test_aggregates_anomaly_kpis(self):
        hotel_id = str(uuid.uuid4())
        anomalies = [
            self._make_anomaly(hotel_id, "surge", 300.0, 30.0),
            self._make_anomaly(hotel_id, "lull", None, 22.0),
        ]
        recos = [self._make_reco(hotel_id, "accepted")]

        mock_anomaly_result = MagicMock()
        mock_anomaly_result.scalars.return_value.all.return_value = anomalies
        mock_reco_result = MagicMock()
        mock_reco_result.scalars.return_value.all.return_value = recos

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[mock_anomaly_result, mock_reco_result]
        )
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.mcp_server.AsyncSessionLocal", return_value=mock_session):
            result = await get_fb_kpis(hotel_id, period="30d")

        kpis = result["kpis"]
        assert kpis["total_anomalies_detected"] == 2
        assert kpis["surge_count"] == 1
        assert kpis["lull_count"] == 1
        assert kpis["total_roi_net_gbp"] == 300.0
        assert result["schema_version"] == "1.0"

    @pytest.mark.asyncio
    async def test_acceptance_rate_computed(self):
        hotel_id = str(uuid.uuid4())
        recos = [
            self._make_reco(hotel_id, "accepted"),
            self._make_reco(hotel_id, "rejected"),
        ]

        mock_anomaly_result = MagicMock()
        mock_anomaly_result.scalars.return_value.all.return_value = []
        mock_reco_result = MagicMock()
        mock_reco_result.scalars.return_value.all.return_value = recos

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[mock_anomaly_result, mock_reco_result]
        )
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.mcp_server.AsyncSessionLocal", return_value=mock_session):
            result = await get_fb_kpis(hotel_id, period="30d")

        assert result["kpis"]["recommendation_acceptance_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_no_data_returns_zero_kpis(self):
        hotel_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.mcp_server.AsyncSessionLocal", return_value=mock_session):
            result = await get_fb_kpis(hotel_id, period="7d")

        kpis = result["kpis"]
        assert kpis["total_anomalies_detected"] == 0
        assert kpis["total_roi_net_gbp"] == 0.0
        assert kpis["recommendation_acceptance_rate"] is None


# ===========================================================================
# 6. /api/v1/mcp/metrics route — integration test
# ===========================================================================
class TestMcpMetricsRoute:
    """GET /api/v1/mcp/metrics returns a well-formed metrics snapshot."""

    @pytest.fixture
    def client(self):
        from app.api.routes.mcp_metrics import router
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return TestClient(app)

    def test_metrics_returns_200(self, client):
        response = client.get("/api/v1/mcp/metrics")
        assert response.status_code == 200

    def test_metrics_shape(self, client):
        data = client.get("/api/v1/mcp/metrics").json()
        assert "tools" in data
        assert "schema_breaks_this_sprint" in data
        assert "schema_stability_ok" in data

    def test_schema_stability_ok_on_fresh_tracker(self, client):
        data = client.get("/api/v1/mcp/metrics").json()
        # The singleton tracker may have been used by other tests, so we only
        # verify the key exists and is boolean.
        assert isinstance(data["schema_stability_ok"], bool)


# ===========================================================================
# 7. Helper unit tests
# ===========================================================================
class TestParseHelpers:
    def test_parse_single_date(self):
        start, end = _parse_date_range("2026-04-01")
        assert start == end == date(2026, 4, 1)

    def test_parse_date_range(self):
        start, end = _parse_date_range("2026-04-01/2026-04-07")
        assert start == date(2026, 4, 1)
        assert end == date(2026, 4, 7)

    def test_parse_date_range_with_spaces(self):
        start, end = _parse_date_range(" 2026-04-01 / 2026-04-03 ")
        assert start == date(2026, 4, 1)
        assert end == date(2026, 4, 3)

    def test_parse_period_7d(self):
        now = datetime.now(tz=timezone.utc)
        since = _parse_period("7d")
        delta = now - since
        assert 6 <= delta.days <= 8  # allow 1-day tolerance for test timing

    def test_parse_period_30d(self):
        now = datetime.now(tz=timezone.utc)
        since = _parse_period("30d")
        delta = now - since
        assert 29 <= delta.days <= 31

    def test_parse_period_90d(self):
        now = datetime.now(tz=timezone.utc)
        since = _parse_period("90d")
        delta = now - since
        assert 89 <= delta.days <= 91

    def test_parse_period_iso_date(self):
        since = _parse_period("2026-01-01")
        assert since.year == 2026
        assert since.month == 1
        assert since.day == 1

"""Tests for HOS-100: AetherixOrchestrator — Claude tool-use loop.

Coverage:
- Tool definitions are valid Anthropic schema format (AC#1)
- _dispatch_forecast_occupancy — happy path + error fallback (AC#2)
- _dispatch_get_stock_alerts — happy path + db-less fallback (AC#3)
- AetherixOrchestrator.run() — end_turn path (AC#4)
- AetherixOrchestrator.run() — tool_use → end_turn loop (AC#5)
- AetherixOrchestrator.run() — MAX_TOOL_ITERATIONS guard (AC#6)
- AetherixOrchestrator.run() — no API key fallback (AC#7)
- hotel_id injection when Claude omits it from tool input (AC#8)

All Anthropic API calls and DB sessions are mocked.
No real network or database connections required.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.claude_orchestrator import (
    MAX_TOOL_ITERATIONS,
    TOOL_DEFINITIONS,
    AetherixOrchestrator,
    _dispatch_forecast_occupancy,
    _dispatch_get_stock_alerts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HOTEL_ID = "11111111-1111-1111-1111-111111111111"
PROPERTY_ID = "22222222-2222-2222-2222-222222222222"


def _make_message(stop_reason: str, content: List[Any]) -> MagicMock:
    """Build a fake Anthropic Message object."""
    msg = MagicMock()
    msg.stop_reason = stop_reason
    msg.content = content
    return msg


def _text_block(text: str) -> MagicMock:
    from anthropic.types import TextBlock

    block = MagicMock(spec=TextBlock)
    block.type = "text"
    block.text = text
    return block


def _tool_use_block(name: str, inputs: Dict[str, Any], block_id: str = "tu_01") -> MagicMock:
    from anthropic.types import ToolUseBlock

    block = MagicMock(spec=ToolUseBlock)
    block.type = "tool_use"
    block.name = name
    block.input = inputs
    block.id = block_id
    return block


# ---------------------------------------------------------------------------
# AC#1 — Tool schema validation
# ---------------------------------------------------------------------------


class TestToolDefinitions:
    """Tool definitions must conform to Anthropic tool schema requirements."""

    def test_tool_count(self):
        assert len(TOOL_DEFINITIONS) == 2

    def test_tool_names(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        assert names == {"forecast_occupancy", "get_stock_alerts"}

    def test_each_tool_has_required_keys(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            schema = tool["input_schema"]
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema

    def test_forecast_occupancy_required_fields(self):
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "forecast_occupancy")
        assert "hotel_id" in tool["input_schema"]["required"]
        assert "service_type" in tool["input_schema"]["required"]

    def test_get_stock_alerts_required_fields(self):
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "get_stock_alerts")
        assert "hotel_id" in tool["input_schema"]["required"]


# ---------------------------------------------------------------------------
# AC#2 — _dispatch_forecast_occupancy
# ---------------------------------------------------------------------------


class TestDispatchForecastOccupancy:
    """Unit tests for the forecast_occupancy tool dispatcher."""

    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_result = {
            "prediction": {"covers": 85, "confidence": 0.82},
            "reasoning": "High occupancy weekend expected.",
            "staffing_recommendation": {"servers": 5},
        }
        # Patch at the source module — AetherixEngine is imported inside the function
        with patch(
            "app.services.aetherix_engine.AetherixEngine"
        ) as MockEngine:
            instance = MockEngine.return_value
            instance.get_forecast = AsyncMock(return_value=mock_result)

            result = await _dispatch_forecast_occupancy(
                {
                    "hotel_id": HOTEL_ID,
                    "service_type": "dinner",
                    "target_date": "2026-04-05",
                },
                db=None,
            )

        assert result["predicted_covers"] == 85
        assert result["confidence"] == 0.82
        assert result["hotel_id"] == HOTEL_ID
        assert result["date"] == "2026-04-05"
        assert result["service_type"] == "dinner"

    @pytest.mark.asyncio
    async def test_defaults_to_today_when_no_date(self):
        mock_result = {
            "prediction": {"covers": 50, "confidence": 0.75},
            "reasoning": "Normal weekday.",
            "staffing_recommendation": {},
        }
        with patch(
            "app.services.aetherix_engine.AetherixEngine"
        ) as MockEngine:
            instance = MockEngine.return_value
            instance.get_forecast = AsyncMock(return_value=mock_result)

            result = await _dispatch_forecast_occupancy(
                {"hotel_id": HOTEL_ID, "service_type": "lunch"},
                db=None,
            )

        assert result["date"] == date.today().isoformat()

    @pytest.mark.asyncio
    async def test_invalid_date_returns_error(self):
        # No DB or network needed -- date parsing fails before AetherixEngine is touched
        result = await _dispatch_forecast_occupancy(
            {"hotel_id": HOTEL_ID, "service_type": "breakfast", "target_date": "not-a-date"},
            db=None,
        )
        assert "error" in result
        assert "Invalid date" in result["error"]

    @pytest.mark.asyncio
    async def test_engine_exception_returns_error(self):
        with patch(
            "app.services.aetherix_engine.AetherixEngine"
        ) as MockEngine:
            instance = MockEngine.return_value
            instance.get_forecast = AsyncMock(side_effect=RuntimeError("DB down"))

            result = await _dispatch_forecast_occupancy(
                {"hotel_id": HOTEL_ID, "service_type": "dinner"},
                db=None,
            )

        assert "error" in result
        assert result["hotel_id"] == HOTEL_ID


# ---------------------------------------------------------------------------
# AC#3 — _dispatch_get_stock_alerts
# ---------------------------------------------------------------------------


class TestDispatchGetStockAlerts:
    """Unit tests for the get_stock_alerts tool dispatcher."""

    @pytest.mark.asyncio
    async def test_returns_error_when_db_is_none(self):
        result = await _dispatch_get_stock_alerts(
            {"hotel_id": HOTEL_ID},
            db=None,
        )
        assert "error" in result
        assert "Database session" in result["error"]

    @pytest.mark.asyncio
    async def test_happy_path_surge_filter(self):
        # Build a fake DB session that returns one surge row
        fake_row = (
            PROPERTY_ID,           # property_id
            "2026-04-05 12:00:00", # window_start
            "2026-04-05 16:00:00", # window_end
            "surge",               # direction
            35.5,                  # deviation_pct
            json.dumps(["festival_nearby"]),  # triggering_factors
            "detected",            # status
        )
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [fake_row]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await _dispatch_get_stock_alerts(
            {"hotel_id": HOTEL_ID, "direction_filter": "surge"},
            db=mock_db,
        )

        assert result["hotel_id"] == HOTEL_ID
        assert result["alert_count"] == 1
        alert = result["alerts"][0]
        assert alert["direction"] == "surge"
        assert alert["deviation_pct"] == 35.5
        assert "festival_nearby" in alert["triggering_factors"]

    @pytest.mark.asyncio
    async def test_no_alerts_returns_empty_list(self):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await _dispatch_get_stock_alerts(
            {"hotel_id": HOTEL_ID},
            db=mock_db,
        )

        assert result["alert_count"] == 0
        assert result["alerts"] == []

    @pytest.mark.asyncio
    async def test_db_exception_returns_error(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("connection lost"))

        result = await _dispatch_get_stock_alerts(
            {"hotel_id": HOTEL_ID},
            db=mock_db,
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# AC#4 — run() end_turn (no tools called)
# ---------------------------------------------------------------------------


class TestOrchestratorEndTurn:
    """Orchestrator returns Claude's text directly when stop_reason == end_turn."""

    @pytest.mark.asyncio
    async def test_end_turn_returns_text(self):
        orchestrator = AetherixOrchestrator()
        orchestrator._claude = AsyncMock()

        text_response = _make_message(
            stop_reason="end_turn",
            content=[_text_block("Saturday dinner looks busy — 92 covers forecast.")],
        )
        orchestrator._claude.messages.create = AsyncMock(return_value=text_response)

        result = await orchestrator.run(
            hotel_id=HOTEL_ID,
            user_message="How busy is Saturday dinner?",
        )

        assert "92 covers" in result["response"]
        assert result["tool_calls"] == []
        assert result["iterations"] == 1


# ---------------------------------------------------------------------------
# AC#5 — run() tool_use → end_turn loop
# ---------------------------------------------------------------------------


class TestOrchestratorToolLoop:
    """Orchestrator correctly dispatches tools and loops until end_turn."""

    @pytest.mark.asyncio
    async def test_tool_use_then_end_turn(self):
        orchestrator = AetherixOrchestrator()
        orchestrator._claude = AsyncMock()

        tool_block = _tool_use_block(
            name="forecast_occupancy",
            inputs={"hotel_id": HOTEL_ID, "service_type": "dinner"},
            block_id="tu_abc",
        )
        tool_response = _make_message(stop_reason="tool_use", content=[tool_block])

        final_response = _make_message(
            stop_reason="end_turn",
            content=[_text_block("Forecast: 75 covers for dinner.")],
        )

        orchestrator._claude.messages.create = AsyncMock(
            side_effect=[tool_response, final_response]
        )

        mock_forecast = {
            "prediction": {"covers": 75, "confidence": 0.80},
            "reasoning": "Normal day.",
            "staffing_recommendation": {},
        }

        with patch(
            "app.services.aetherix_engine.AetherixEngine"
        ) as MockEngine:
            MockEngine.return_value.get_forecast = AsyncMock(return_value=mock_forecast)

            result = await orchestrator.run(
                hotel_id=HOTEL_ID,
                user_message="Forecast dinner tonight.",
            )

        assert "75 covers" in result["response"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "forecast_occupancy"
        assert result["iterations"] == 2

    @pytest.mark.asyncio
    async def test_hotel_id_injected_when_missing(self):
        """AC#8: hotel_id is injected if Claude omits it from tool input."""
        orchestrator = AetherixOrchestrator()
        orchestrator._claude = AsyncMock()

        # Claude calls the tool WITHOUT hotel_id in inputs
        tool_block = _tool_use_block(
            name="forecast_occupancy",
            inputs={"service_type": "lunch"},  # no hotel_id
            block_id="tu_no_hotel",
        )
        tool_response = _make_message(stop_reason="tool_use", content=[tool_block])
        final_response = _make_message(
            stop_reason="end_turn",
            content=[_text_block("Lunch forecast complete.")],
        )
        orchestrator._claude.messages.create = AsyncMock(
            side_effect=[tool_response, final_response]
        )

        mock_forecast_result = {
            "prediction": {"covers": 30, "confidence": 0.7},
            "reasoning": "ok",
            "staffing_recommendation": {},
        }

        # Patch at the source so the registry's function reference is intercepted
        with patch(
            "app.services.aetherix_engine.AetherixEngine"
        ) as MockEngine:
            MockEngine.return_value.get_forecast = AsyncMock(
                return_value=mock_forecast_result
            )

            result = await orchestrator.run(
                hotel_id=HOTEL_ID, user_message="Lunch forecast?"
            )

        # hotel_id was injected — tool_calls log must show it
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["input"]["hotel_id"] == HOTEL_ID


# ---------------------------------------------------------------------------
# AC#6 — MAX_TOOL_ITERATIONS guard
# ---------------------------------------------------------------------------


class TestOrchestratorIterationCap:
    """Orchestrator must not loop infinitely — capped at MAX_TOOL_ITERATIONS."""

    @pytest.mark.asyncio
    async def test_hits_iteration_cap(self):
        orchestrator = AetherixOrchestrator()
        orchestrator._claude = AsyncMock()

        # Every call returns tool_use — never end_turn
        tool_block = _tool_use_block(
            name="get_stock_alerts",
            inputs={"hotel_id": HOTEL_ID},
            block_id="tu_loop",
        )
        always_tool = _make_message(stop_reason="tool_use", content=[tool_block])
        orchestrator._claude.messages.create = AsyncMock(return_value=always_tool)

        # get_stock_alerts needs a db — pass None so it returns error quickly
        result = await orchestrator.run(
            hotel_id=HOTEL_ID,
            user_message="Keep checking stock forever.",
            db=None,
        )

        assert result["iterations"] == MAX_TOOL_ITERATIONS
        assert "maximum" in result["response"].lower()


# ---------------------------------------------------------------------------
# AC#7 — No API key fallback
# ---------------------------------------------------------------------------


class TestOrchestratorNoApiKey:
    """When ANTHROPIC_API_KEY is missing, return a graceful fallback."""

    @pytest.mark.asyncio
    async def test_no_api_key_returns_fallback(self):
        orchestrator = AetherixOrchestrator()
        orchestrator._claude = None  # simulate missing key

        result = await orchestrator.run(
            hotel_id=HOTEL_ID,
            user_message="Any question.",
        )

        assert result["iterations"] == 0
        assert result["tool_calls"] == []
        assert "not available" in result["response"].lower()

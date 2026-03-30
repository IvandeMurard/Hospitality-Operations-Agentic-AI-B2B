"""Claude tool-use orchestrator for Aetherix F&B operations.

Adapts the agentic tool-use loop pattern (linq-resy-agent style) for the
Aetherix hospitality context.  Claude drives the conversation and calls
internal Aetherix services via structured tool definitions.

Loop invariant (HOS-100):
    1. Send user message + conversation history to Claude with tools attached.
    2. If stop_reason == "tool_use": dispatch each tool block, collect results,
       append assistant turn + tool results to history, go to 1.
    3. If stop_reason == "end_turn": return final text response.

Tool registry (Phase 0):
    - forecast_occupancy  — Prophet + RAG + Claude reasoning (AetherixEngine)
    - get_stock_alerts    — Demand anomaly alerts (AnomalyDetectionService)

Architecture constraints (CLAUDE.md):
    - Fat Backend: all logic lives here, not in the route layer.
    - Claude Sonnet as primary LLM (Decision #1).
    - Multi-LLM fallback prepared via `LLMProvider` protocol (Decision #9).
    - Max tool loop depth capped at MAX_TOOL_ITERATIONS to prevent runaway loops.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from anthropic import AsyncAnthropic
from anthropic.types import (
    ContentBlock,
    Message,
    TextBlock,
    ToolUseBlock,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Safety cap: maximum Claude ↔ tool round-trips per request.
MAX_TOOL_ITERATIONS = 8

# ---------------------------------------------------------------------------
# System prompt — F&B hospitality context
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are Aetherix, an expert AI copilot embedded in hotel F&B operations.
Your role is to assist hotel managers with proactive, data-driven decisions
about restaurant covers forecasting, staffing, stock risk and demand anomalies.

PERSONALITY & TONE:
- Concise, professional, and actionable — managers are busy.
- Always quantify recommendations (covers, headcount, € impact when available).
- Surface uncertainty honestly: if confidence is low, say so.
- Human-in-the-loop: never make decisions for the manager, recommend and explain.

OPERATIONAL CONTEXT:
- Data sources: PMS occupancy data (Apaleo), local events, weather forecasts,
  Prophet time-series model, pgvector RAG patterns (495+ F&B historical patterns).
- Memory: per-property Private Memory (operational_memory table) stores past
  manager feedback to improve future recommendations.
- Alerts are sent proactively via WhatsApp — keep explanations WhatsApp-friendly
  (short paragraphs, no markdown tables).

TOOL USAGE RULES:
- Always call forecast_occupancy before making staffing or stock recommendations.
- Call get_stock_alerts to identify demand surges that put inventory at risk.
- If you need both forecast and alerts for a complete picture, call both tools.
- Do not hallucinate data — only use what the tools return.
- When a tool returns an error, acknowledge it and reason from available data.

RESPONSE FORMAT:
- Lead with the key recommendation or finding.
- Follow with a 1-2 sentence rationale grounded in the tool output.
- End with a clear action item for the manager (e.g., "Recommend adding 2 servers
  for the Saturday dinner service").
"""

# ---------------------------------------------------------------------------
# Anthropic tool schemas
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "forecast_occupancy",
        "description": (
            "Forecast restaurant covers (occupancy) for a specific hotel property "
            "and date using the Prophet time-series model enriched with RAG patterns, "
            "weather, and local events. Returns predicted covers, confidence interval, "
            "reasoning explanation, and staffing recommendation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_id": {
                    "type": "string",
                    "description": "UUID of the hotel / tenant property.",
                },
                "target_date": {
                    "type": "string",
                    "description": (
                        "ISO-8601 date to forecast (YYYY-MM-DD). "
                        "Defaults to today if not provided."
                    ),
                },
                "service_type": {
                    "type": "string",
                    "enum": ["breakfast", "lunch", "dinner", "all_day"],
                    "description": "Meal service to forecast.",
                },
                "context": {
                    "type": "object",
                    "description": (
                        "Optional context overrides: occupancy (0-1 float), "
                        "weather condition string, list of event names."
                    ),
                    "properties": {
                        "occupancy": {"type": "number"},
                        "weather": {
                            "type": "object",
                            "properties": {"condition": {"type": "string"}},
                        },
                        "events": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["hotel_id", "service_type"],
        },
    },
    {
        "name": "get_stock_alerts",
        "description": (
            "Return active demand anomaly alerts for a hotel property. "
            "Demand surges (>20% above baseline) indicate stock-at-risk windows "
            "where inventory may run short. Returns a list of alert windows with "
            "direction (surge/lull), deviation %, and triggering factors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_id": {
                    "type": "string",
                    "description": "UUID of the hotel / tenant property.",
                },
                "property_id": {
                    "type": "string",
                    "description": (
                        "UUID of the specific restaurant property. "
                        "Required when the hotel has multiple F&B outlets."
                    ),
                },
                "direction_filter": {
                    "type": "string",
                    "enum": ["surge", "lull", "both"],
                    "description": (
                        "Filter alerts by direction. 'surge' returns only "
                        "demand surges (stock-at-risk). Defaults to 'both'."
                    ),
                },
            },
            "required": ["hotel_id"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatchers
# ---------------------------------------------------------------------------


async def _dispatch_forecast_occupancy(
    inputs: Dict[str, Any],
    db: Optional[AsyncSession],
) -> Dict[str, Any]:
    """Call AetherixEngine.get_forecast() and return structured result."""
    from app.services.aetherix_engine import AetherixEngine

    hotel_id = inputs["hotel_id"]
    service_type = inputs.get("service_type", "dinner")
    context = inputs.get("context", {})

    raw_date = inputs.get("target_date")
    if raw_date:
        try:
            target_date = date.fromisoformat(raw_date)
        except ValueError:
            return {"error": f"Invalid date format: {raw_date!r}. Expected YYYY-MM-DD."}
    else:
        target_date = date.today()

    try:
        engine = AetherixEngine()
        result = await engine.get_forecast(hotel_id, target_date, service_type, context)
        return {
            "hotel_id": hotel_id,
            "date": target_date.isoformat(),
            "service_type": service_type,
            "predicted_covers": result["prediction"]["covers"],
            "confidence": result["prediction"]["confidence"],
            "reasoning": result.get("reasoning", ""),
            "staffing_recommendation": result.get("staffing_recommendation", {}),
        }
    except Exception as exc:
        logger.exception("forecast_occupancy tool error for hotel %s", hotel_id)
        return {"error": str(exc), "hotel_id": hotel_id}


async def _dispatch_get_stock_alerts(
    inputs: Dict[str, Any],
    db: Optional[AsyncSession],
) -> Dict[str, Any]:
    """Query demand_anomalies for active surge/lull alerts.

    Falls back to AnomalyDetectionService.detect_for_property() if a db
    session is provided; otherwise returns a lightweight SQL query result.
    """
    hotel_id: str = inputs["hotel_id"]
    property_id: Optional[str] = inputs.get("property_id")
    direction_filter: str = inputs.get("direction_filter", "both")

    if db is None:
        return {
            "error": "Database session required for get_stock_alerts.",
            "hotel_id": hotel_id,
        }

    try:
        from sqlalchemy import text

        direction_clause = ""
        params: Dict[str, Any] = {
            "tenant_id": hotel_id,
            "cutoff": date.today().isoformat(),
        }

        if direction_filter in ("surge", "lull"):
            direction_clause = "AND direction = :direction"
            params["direction"] = direction_filter

        if property_id:
            property_clause = "AND property_id = :property_id"
            params["property_id"] = property_id
        else:
            property_clause = ""

        stmt = text(
            f"""
            SELECT property_id, window_start, window_end,
                   direction, deviation_pct, triggering_factors, status
            FROM demand_anomalies
            WHERE tenant_id  = :tenant_id
              AND window_end >= :cutoff
              AND status     = 'detected'
              {direction_clause}
              {property_clause}
            ORDER BY window_start ASC
            LIMIT 20
            """
        )
        result = await db.execute(stmt, params)
        rows = result.fetchall()

        alerts = []
        for row in rows:
            factors = row[5]
            if isinstance(factors, str):
                try:
                    factors = json.loads(factors)
                except json.JSONDecodeError:
                    pass
            alerts.append(
                {
                    "property_id": str(row[0]),
                    "window_start": str(row[1]),
                    "window_end": str(row[2]),
                    "direction": row[3],
                    "deviation_pct": float(row[4]),
                    "triggering_factors": factors,
                    "status": row[6],
                }
            )

        return {
            "hotel_id": hotel_id,
            "alert_count": len(alerts),
            "alerts": alerts,
        }

    except Exception as exc:
        logger.exception("get_stock_alerts tool error for hotel %s", hotel_id)
        return {"error": str(exc), "hotel_id": hotel_id}


# ---------------------------------------------------------------------------
# Tool dispatcher registry
# ---------------------------------------------------------------------------

_TOOL_REGISTRY = {
    "forecast_occupancy": _dispatch_forecast_occupancy,
    "get_stock_alerts": _dispatch_get_stock_alerts,
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class AetherixOrchestrator:
    """Claude-driven tool-use loop for Aetherix F&B operations.

    Usage::

        orchestrator = AetherixOrchestrator()
        reply = await orchestrator.run(
            hotel_id="uuid-...",
            user_message="What's the forecast for dinner on Saturday?",
            db=db_session,
        )
    """

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self._claude: Optional[AsyncAnthropic] = (
            AsyncAnthropic(api_key=api_key) if api_key else None
        )
        self._model = "claude-sonnet-4-6"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        hotel_id: str,
        user_message: str,
        db: Optional[AsyncSession] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run the tool-use loop and return the final response.

        Args:
            hotel_id:             Property / tenant UUID (injected into tool calls).
            user_message:         The manager's question or command.
            db:                   AsyncSession for DB-backed tools (get_stock_alerts).
            conversation_history: Prior turns in [{"role": ..., "content": ...}] format.
                                  Pass None to start a fresh conversation.

        Returns:
            dict with keys:
                - "response": final assistant text
                - "tool_calls": list of {"name", "input", "result"} per tool invoked
                - "iterations": number of Claude ↔ tool round-trips
        """
        if not self._claude:
            return self._unavailable_fallback(user_message)

        messages: List[Dict[str, Any]] = list(conversation_history or [])
        messages.append({"role": "user", "content": user_message})

        tool_calls_log: List[Dict[str, Any]] = []
        iterations = 0

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            response: Message = await self._claude.messages.create(
                model=self._model,
                system=_SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
                max_tokens=1024,
            )

            if response.stop_reason == "end_turn":
                final_text = self._extract_text(response.content)
                return {
                    "response": final_text,
                    "tool_calls": tool_calls_log,
                    "iterations": iterations,
                }

            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if not isinstance(block, ToolUseBlock):
                        continue

                    tool_name: str = block.name
                    tool_input: Dict[str, Any] = dict(block.input)

                    # Inject hotel_id if not provided by Claude
                    if "hotel_id" not in tool_input:
                        tool_input["hotel_id"] = hotel_id

                    dispatcher = _TOOL_REGISTRY.get(tool_name)
                    if dispatcher is None:
                        tool_result = {"error": f"Unknown tool: {tool_name!r}"}
                    else:
                        tool_result = await dispatcher(tool_input, db)

                    tool_calls_log.append(
                        {
                            "name": tool_name,
                            "input": tool_input,
                            "result": tool_result,
                        }
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(tool_result, default=str),
                        }
                    )

                # Append assistant turn (with tool_use blocks) + user turn (tool results)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop_reason (e.g. max_tokens) — surface the partial text
                logger.warning(
                    "Unexpected stop_reason=%r after %d iterations",
                    response.stop_reason,
                    iterations,
                )
                return {
                    "response": self._extract_text(response.content)
                    or f"[Stopped: {response.stop_reason}]",
                    "tool_calls": tool_calls_log,
                    "iterations": iterations,
                }

        logger.warning("Tool-use loop hit MAX_TOOL_ITERATIONS=%d", MAX_TOOL_ITERATIONS)
        return {
            "response": (
                "I reached the maximum number of reasoning steps. "
                "Please try a more specific question."
            ),
            "tool_calls": tool_calls_log,
            "iterations": iterations,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(content: List[ContentBlock]) -> str:
        """Return the concatenated text from all TextBlock items."""
        return " ".join(b.text for b in content if isinstance(b, TextBlock)).strip()

    @staticmethod
    def _unavailable_fallback(user_message: str) -> Dict[str, Any]:
        """Graceful response when ANTHROPIC_API_KEY is not configured."""
        logger.warning("AetherixOrchestrator: ANTHROPIC_API_KEY not set — returning fallback")
        return {
            "response": (
                "Aetherix AI is not available right now "
                "(API key not configured). Please contact support."
            ),
            "tool_calls": [],
            "iterations": 0,
        }

"""Aetherix MCP Server — agent-callable F&B operations primitives (HOS-71).

Exposes four tools that other agents (Claude, Codex, Cursor, Apaleo Copilot, …)
can call via the Model Context Protocol:

  forecast_occupancy   — predict F&B covers for a hotel / date range
  get_stock_alerts     — list active demand anomalies (pending alerts)
  recommend_menu       — RAG-backed menu recommendation for context
  get_fb_kpis          — aggregated F&B KPIs for a period

Architecture:
  - FastMCP (SSE + Streamable-HTTP transports) mounted into the main FastAPI app
    at /mcp (see app/main.py).
  - Each tool is instrumented via AgentSEOTracker for HOS-72 metrics.
  - No JWT auth at the MCP layer — authenticate at the infrastructure layer
    (API key header / VPN) when exposing publicly.
  - Schema stability: BREAKING changes require a version bump (Agent SEO policy).

[Source: CLAUDE.md §Pivot stratégique — Agent-First, HOS-71, HOS-72]
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic
from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, text
from sqlalchemy.future import select

from app.db.models import DemandAnomaly, StaffingRecommendation
from app.db.session import AsyncSessionLocal
from app.middleware.agent_seo import tracker
from app.services.aetherix_engine import AetherixEngine
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Aetherix",
    instructions=(
        "Aetherix is a specialised F&B operations AI for hotels. "
        "Use these tools to forecast covers, check demand alerts, get menu "
        "recommendations, and retrieve F&B KPIs for a given hotel."
    ),
)

# Shared service singletons (cheap to construct; stateless beyond config)
_engine = AetherixEngine()
_rag = RAGService()
_claude_client: Optional[AsyncAnthropic] = (
    AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    if os.getenv("ANTHROPIC_API_KEY")
    else None
)


# ---------------------------------------------------------------------------
# Helper: parse a date_range string into (start, end)
# ---------------------------------------------------------------------------
def _parse_date_range(date_range: str) -> tuple[date, date]:
    """Parse 'YYYY-MM-DD' or 'YYYY-MM-DD/YYYY-MM-DD' into (start, end)."""
    if "/" in date_range:
        parts = date_range.split("/", 1)
        return date.fromisoformat(parts[0].strip()), date.fromisoformat(parts[1].strip())
    single = date.fromisoformat(date_range.strip())
    return single, single


def _parse_period(period: str) -> datetime:
    """Return a UTC datetime marking the start of a relative period string.

    Accepted values: '7d', '30d', '90d', or an ISO-8601 date.
    """
    period = period.strip().lower()
    now = datetime.now(tz=timezone.utc)
    if period.endswith("d"):
        days = int(period[:-1])
        return now - timedelta(days=days)
    # Fallback: treat as ISO date
    return datetime.fromisoformat(period).replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Tool 1: forecast_occupancy
# ---------------------------------------------------------------------------
@mcp.tool()
async def forecast_occupancy(
    hotel_id: str,
    date_range: str,
    service_type: str = "dinner",
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Forecast F&B covers for a hotel over a date range.

    Args:
        hotel_id:    Tenant/property identifier (e.g. "hotel-paris-001").
        date_range:  Single date "YYYY-MM-DD" or range "YYYY-MM-DD/YYYY-MM-DD".
        service_type: Meal service — "breakfast", "lunch", or "dinner" (default).
        context:     Optional JSON string with external context:
                     {"weather": {"condition": "Rain", "temp": 12},
                      "events": [...], "occupancy": 0.85}

    Returns:
        Dict with keys: hotel_id, forecasts (list per day), summary.
        Each forecast entry: date, service_type, predicted_covers, confidence,
        range_min, range_max, reasoning_summary, staffing_recommendation.

    Schema version: 1.0 — breaking changes require a version bump.
    """
    async with tracker.record("forecast_occupancy"):
        ctx: Dict[str, Any] = {}
        if context:
            try:
                ctx = json.loads(context)
            except json.JSONDecodeError:
                ctx = {}

        ctx.setdefault("weather", {"condition": "Unknown", "temp": None})
        ctx.setdefault("events", [])
        ctx.setdefault("occupancy", None)

        start_date, end_date = _parse_date_range(date_range)

        forecasts: List[Dict[str, Any]] = []
        current = start_date
        while current <= end_date:
            result = await _engine.get_forecast(hotel_id, current, service_type, ctx)
            pred = result["prediction"]
            reasoning_detail = result.get("reasoning_detail", {})
            summary = reasoning_detail.get("summary") or str(result.get("reasoning", ""))
            interval = pred.get("interval", [pred.get("covers", 0), pred.get("covers", 0)])

            forecasts.append(
                {
                    "date": current.isoformat(),
                    "service_type": service_type,
                    "predicted_covers": pred.get("covers", pred.get("predicted_covers", 0)),
                    "confidence": pred.get("confidence", 0.0),
                    "range_min": interval[0],
                    "range_max": interval[1],
                    "reasoning_summary": summary,
                    "staffing_recommendation": result.get("staffing_recommendation", {}),
                    "claude_used": reasoning_detail.get("claude_used", False),
                }
            )
            current += timedelta(days=1)

        return {
            "hotel_id": hotel_id,
            "service_type": service_type,
            "date_range": date_range,
            "forecasts": forecasts,
            "schema_version": "1.0",
        }


# ---------------------------------------------------------------------------
# Tool 2: get_stock_alerts
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_stock_alerts(
    hotel_id: str,
    status_filter: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Return active demand anomaly alerts for a hotel.

    An "alert" is a detected demand surge or lull that has not yet been
    dispatched to the manager. Agents should surface these to trigger
    staffing adjustments or inventory pre-ordering.

    Args:
        hotel_id:      Tenant identifier.
        status_filter: Comma-separated statuses to include.
                       Default: "detected,roi_positive,ready_to_push".
        limit:         Maximum number of alerts to return (default 20, max 100).

    Returns:
        Dict with keys: hotel_id, alert_count, alerts (list).
        Each alert: id, direction, window_start, window_end, deviation_pct,
        triggering_factors, status, roi_net, recommendation_text.

    Schema version: 1.0
    """
    async with tracker.record("get_stock_alerts"):
        limit = min(limit, 100)

        if status_filter:
            statuses = [s.strip() for s in status_filter.split(",")]
        else:
            statuses = ["detected", "roi_positive", "ready_to_push"]

        async with AsyncSessionLocal() as db:
            stmt = (
                select(DemandAnomaly)
                .where(
                    DemandAnomaly.status.in_(statuses),
                )
                .order_by(DemandAnomaly.detected_at.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            anomalies = result.scalars().all()

            # Filter by hotel_id: tenant_id stored as UUID or string depending
            # on the environment. We do a string-based comparison as a
            # flexible fallback (works for both UUID and string tenant_ids).
            alerts = []
            for a in anomalies:
                if str(a.tenant_id) != str(hotel_id):
                    continue
                alerts.append(
                    {
                        "id": str(a.id),
                        "direction": a.direction,
                        "window_start": a.window_start.isoformat() if a.window_start else None,
                        "window_end": a.window_end.isoformat() if a.window_end else None,
                        "deviation_pct": float(a.deviation_pct) if a.deviation_pct else None,
                        "triggering_factors": a.triggering_factors or [],
                        "status": a.status,
                        "roi_net": float(a.roi_net) if a.roi_net is not None else None,
                        "recommendation_text": a.recommendation_text,
                        "detected_at": a.detected_at.isoformat() if a.detected_at else None,
                    }
                )

        return {
            "hotel_id": hotel_id,
            "alert_count": len(alerts),
            "alerts": alerts,
            "schema_version": "1.0",
        }


# ---------------------------------------------------------------------------
# Tool 3: recommend_menu
# ---------------------------------------------------------------------------
@mcp.tool()
async def recommend_menu(
    hotel_id: str,
    context: str,
) -> Dict[str, Any]:
    """Generate a contextual menu recommendation for a hotel.

    Uses RAG to retrieve similar historical F&B patterns, then asks Claude
    to produce a concrete menu suggestion based on the supplied context.
    Falls back to a heuristic recommendation when ANTHROPIC_API_KEY is absent.

    Args:
        hotel_id: Tenant identifier.
        context:  Natural language description of the situation, e.g.
                  "80 covers for a gala dinner tonight, 40% international guests,
                   rainy weather, vegetarian-heavy group."

    Returns:
        Dict with keys: hotel_id, recommendation, reasoning, patterns_used,
        claude_used, schema_version.

    Schema version: 1.0
    """
    async with tracker.record("recommend_menu"):
        # RAG: retrieve similar historical patterns
        context_str = f"hotel:{hotel_id} {context}"
        patterns: List[Dict] = await _rag.find_similar_patterns(context_str, "dinner")

        patterns_summary = (
            "\n".join(
                f"- {p.get('pattern_text', '')} "
                f"[outcome: {p.get('outcome_description', '')}]"
                for p in patterns[:5]
            )
            if patterns
            else "No similar historical patterns found."
        )

        if _claude_client:
            prompt = (
                "You are the F&B operations AI for a hotel. "
                "Based on the historical patterns below and the manager's context, "
                "provide a concise, actionable menu recommendation (3-5 bullet points).\n\n"
                f"Context: {context}\n\n"
                f"Historical patterns:\n{patterns_summary}\n\n"
                "Respond with a structured recommendation."
            )
            try:
                message = await _claude_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=400,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                recommendation = message.content[0].text.strip()
                claude_used = True
            except Exception as exc:
                logger.warning("Claude API error in recommend_menu: %s", exc)
                recommendation = _heuristic_menu_recommendation(context, patterns)
                claude_used = False
        else:
            recommendation = _heuristic_menu_recommendation(context, patterns)
            claude_used = False

        return {
            "hotel_id": hotel_id,
            "recommendation": recommendation,
            "reasoning": f"Based on {len(patterns)} similar historical patterns.",
            "patterns_used": len(patterns),
            "claude_used": claude_used,
            "schema_version": "1.0",
        }


def _heuristic_menu_recommendation(context: str, patterns: List[Dict]) -> str:
    """Fallback recommendation when Claude is unavailable."""
    context_lower = context.lower()
    tips = []
    if "rainy" in context_lower or "rain" in context_lower:
        tips.append("Offer warm comfort dishes (soups, stews, hot appetizers).")
    if "vegetarian" in context_lower or "vegan" in context_lower:
        tips.append("Feature at least 2 prominent plant-based mains on the set menu.")
    if "gala" in context_lower or "event" in context_lower or "banquet" in context_lower:
        tips.append("Prepare a 3-course set menu with pre-plated starters for faster service.")
    if "international" in context_lower:
        tips.append("Include allergen cards in English and French; avoid heavy spices by default.")
    if patterns:
        top = patterns[0]
        outcome = top.get("outcome_description", "")
        if outcome:
            tips.append(f"Historical pattern suggests: {outcome}")
    if not tips:
        tips.append("Follow standard service protocols. No specific contextual adjustments identified.")
    return "\n".join(f"• {t}" for t in tips)


# ---------------------------------------------------------------------------
# Tool 4: get_fb_kpis
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_fb_kpis(
    hotel_id: str,
    period: str = "30d",
) -> Dict[str, Any]:
    """Return aggregated F&B KPIs for a hotel over a period.

    KPIs returned:
      - total_anomalies_detected
      - surge_count / lull_count
      - total_roi_net          (£ — sum of net ROI across ROI-positive anomalies)
      - recommendation_acceptance_rate  (% recommendations accepted by manager)
      - recommendations_dispatched
      - avg_deviation_pct      (average demand deviation from baseline)

    Args:
        hotel_id: Tenant identifier.
        period:   Relative period — "7d", "30d" (default), "90d" — or an
                  ISO-8601 date string marking the start of the period.

    Returns:
        Dict with keys: hotel_id, period, kpis, schema_version.

    Schema version: 1.0
    """
    async with tracker.record("get_fb_kpis"):
        since = _parse_period(period)

        async with AsyncSessionLocal() as db:
            # --- Anomaly KPIs ---
            anomaly_rows = await db.execute(
                select(DemandAnomaly).where(
                    DemandAnomaly.detected_at >= since,
                )
            )
            anomalies = [
                a for a in anomaly_rows.scalars().all()
                if str(a.tenant_id) == str(hotel_id)
            ]

            total_anomalies = len(anomalies)
            surge_count = sum(1 for a in anomalies if a.direction == "surge")
            lull_count = sum(1 for a in anomalies if a.direction == "lull")

            roi_positives = [
                a for a in anomalies
                if a.roi_net is not None and float(a.roi_net) > 0
            ]
            total_roi_net = sum(float(a.roi_net) for a in roi_positives)

            avg_deviation = (
                sum(float(a.deviation_pct) for a in anomalies if a.deviation_pct)
                / total_anomalies
                if total_anomalies > 0
                else 0.0
            )

            # --- Recommendation KPIs ---
            reco_rows = await db.execute(
                select(StaffingRecommendation).where(
                    StaffingRecommendation.created_at >= since,
                )
            )
            recos = [
                r for r in reco_rows.scalars().all()
                if str(r.tenant_id) == str(hotel_id)
            ]

            dispatched = sum(1 for r in recos if r.status in ("dispatched", "accepted", "rejected"))
            accepted = sum(1 for r in recos if r.action == "accepted")
            actioned = sum(1 for r in recos if r.action in ("accepted", "rejected"))
            acceptance_rate = (accepted / actioned) if actioned > 0 else None

        return {
            "hotel_id": hotel_id,
            "period": period,
            "kpis": {
                "total_anomalies_detected": total_anomalies,
                "surge_count": surge_count,
                "lull_count": lull_count,
                "total_roi_net_gbp": round(total_roi_net, 2),
                "recommendations_dispatched": dispatched,
                "recommendation_acceptance_rate": (
                    round(acceptance_rate, 4) if acceptance_rate is not None else None
                ),
                "avg_deviation_pct": round(avg_deviation, 2),
            },
            "schema_version": "1.0",
        }

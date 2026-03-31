"""MCP Agent SEO metrics endpoint (HOS-72).

GET /api/v1/mcp/metrics — returns per-tool success rate, p95 latency,
agent retry rate and schema stability counter.

These metrics are machine-legible so that agent orchestrators (Apaleo Copilot,
Claude, etc.) can rank Aetherix tools by reliability ("Agent SEO").

Targets (per CLAUDE.md):
  tool_success_rate  > 99.5 %
  p95_latency        < 500 ms
  agent_retry_rate   < 1 %
  schema_breaks      = 0 / sprint

[Source: CLAUDE.md §Pivot stratégique — Agent-First, HOS-72]
"""
from __future__ import annotations

from fastapi import APIRouter

from app.middleware.agent_seo import tracker

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/metrics", summary="Agent SEO metrics for MCP tools")
async def get_mcp_metrics():
    """Return per-tool Agent SEO metrics.

    Response shape::

        {
          "tools": {
            "forecast_occupancy": {
              "total_calls": 120,
              "successful_calls": 120,
              "success_rate": 1.0,
              "retry_calls": 0,
              "agent_retry_rate": 0.0,
              "p95_latency_ms": 312.4,
              "targets": {
                "success_rate_ok": true,
                "p95_latency_ok": true,
                "retry_rate_ok": true
              }
            },
            ...
          },
          "schema_breaks_this_sprint": 0,
          "schema_stability_ok": true
        }
    """
    return await tracker.get_metrics()

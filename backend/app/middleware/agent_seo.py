"""Agent SEO metrics tracker for MCP tool calls.

Instruments the four KPIs required by HOS-71 / HOS-72:
  - tool_success_rate  : successful calls / total calls per tool  (target > 99.5 %)
  - p95_latency        : 95th-percentile response time in ms       (target < 500 ms)
  - agent_retry_rate   : calls tagged as retries / total calls     (target < 1 %)
  - schema_stability   : breaking-change counter (incremented manually) (target 0 / sprint)

All state is in-memory (reset on process restart). Metrics are exposed via
GET /api/v1/mcp/metrics (see app/api/routes/mcp_metrics.py).

[Source: CLAUDE.md §Pivot stratégique — Agent-First, HOS-71, HOS-72]
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List


class AgentSEOTracker:
    """Thread-safe (asyncio) in-memory metrics store.

    Usage (inside an MCP tool handler)::

        async with tracker.record("forecast_occupancy") as ctx:
            result = await _do_work()
            return result

    The context manager records latency and marks the call as success when the
    block exits without raising an exception.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # Per-tool counters
        self._total: Dict[str, int] = defaultdict(int)
        self._success: Dict[str, int] = defaultdict(int)
        self._retry: Dict[str, int] = defaultdict(int)
        # Per-tool latency samples (ms), keep last 1000 per tool
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        # Breaking-change counter (incremented via bump_schema_break)
        self._schema_breaks: int = 0

    @asynccontextmanager
    async def record(
        self, tool_name: str, *, is_retry: bool = False
    ) -> AsyncIterator[None]:
        """Async context manager that records a single tool call.

        Args:
            tool_name: MCP tool identifier (e.g. "forecast_occupancy").
            is_retry:  Set True when the caller is an agent retry attempt.

        Raises:
            Re-raises any exception from the wrapped block after recording the
            failure (call is counted as failed).
        """
        start = time.perf_counter()
        async with self._lock:
            self._total[tool_name] += 1
            if is_retry:
                self._retry[tool_name] += 1

        try:
            yield
            # Success path
            elapsed_ms = (time.perf_counter() - start) * 1000
            async with self._lock:
                self._success[tool_name] += 1
                samples = self._latencies[tool_name]
                samples.append(elapsed_ms)
                if len(samples) > 1000:
                    del samples[:-1000]
        except Exception:
            # Failure path — latency is still recorded for p95 accuracy
            elapsed_ms = (time.perf_counter() - start) * 1000
            async with self._lock:
                samples = self._latencies[tool_name]
                samples.append(elapsed_ms)
                if len(samples) > 1000:
                    del samples[:-1000]
            raise

    def bump_schema_break(self) -> None:
        """Increment the schema-stability counter (call on any breaking API change)."""
        self._schema_breaks += 1

    async def get_metrics(self) -> Dict:
        """Return a snapshot of all metrics (safe to call concurrently)."""
        async with self._lock:
            tools: Dict[str, Dict] = {}
            all_tool_names = set(self._total) | set(self._latencies)
            for name in all_tool_names:
                total = self._total[name]
                success = self._success[name]
                retry = self._retry[name]
                samples = sorted(self._latencies[name])

                success_rate = (success / total) if total > 0 else 1.0
                retry_rate = (retry / total) if total > 0 else 0.0
                p95_latency_ms = _percentile(samples, 95) if samples else 0.0

                tools[name] = {
                    "total_calls": total,
                    "successful_calls": success,
                    "success_rate": round(success_rate, 6),
                    "retry_calls": retry,
                    "agent_retry_rate": round(retry_rate, 6),
                    "p95_latency_ms": round(p95_latency_ms, 2),
                    "targets": {
                        "success_rate_ok": success_rate >= 0.995,
                        "p95_latency_ok": p95_latency_ms < 500,
                        "retry_rate_ok": retry_rate < 0.01,
                    },
                }

            return {
                "tools": tools,
                "schema_breaks_this_sprint": self._schema_breaks,
                "schema_stability_ok": self._schema_breaks == 0,
            }


def _percentile(sorted_values: List[float], pct: int) -> float:
    """Nearest-rank percentile over a pre-sorted list."""
    if not sorted_values:
        return 0.0
    k = max(0, int(len(sorted_values) * pct / 100) - 1)
    return sorted_values[k]


# ---------------------------------------------------------------------------
# Singleton — shared across the FastMCP tools and the metrics route
# ---------------------------------------------------------------------------
tracker = AgentSEOTracker()

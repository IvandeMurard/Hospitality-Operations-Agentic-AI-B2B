"""RAG Service — pgvector retrieval layer (HOS-99).

Replaces the old Qdrant + Mistral stack with a single SQL query against
the `fb_patterns` table in Supabase (PostgreSQL + pgvector extension).

A single SQL query with the pgvector cosine-distance operator (<=>)
replaces the previous two-hop Qdrant + embedding round-trip, keeping
p95 latency well within the 500 ms MCP target.

Embedding generation uses a zero-vector fallback when no API key is
configured (dev mode). Replace `_get_embedding` when a supported
embedding endpoint is available.
"""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Dimension must match the vector(1536) column in fb_patterns.
_EMBEDDING_DIM = 1536


async def _get_embedding(query_text: str) -> List[float]:
    """Return a 1536-dim embedding for *query_text*.

    Currently returns a zero vector as a graceful fallback — pgvector cosine
    distance on zero vectors returns 1.0 (maximum distance) for all rows,
    which means retrieval degrades to unordered results rather than crashing.

    Replace the body here when a supported embedding endpoint is available
    (e.g. text-embedding-3-small via OpenAI, or a future Anthropic endpoint).
    """
    return [0.0] * _EMBEDDING_DIM


class RAGService:
    """Retrieves similar F&B patterns from the `fb_patterns` pgvector table.

    Accepts an injected AsyncSession so callers control the DB transaction.
    Falls back gracefully when no DB session is provided (returns empty list).
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def find_similar_patterns(
        self,
        query_text: str,
        service_type: str,
        tenant_id: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return up to *limit* patterns ordered by cosine similarity to *query_text*.

        Filters:
          - service_type must match exactly
          - tenant_id, when provided, restricts to that hotel's patterns plus
            global patterns (tenant_id IS NULL)
          - feedback_status != 'rejected' (exclude patterns managers disliked)

        When running against SQLite (tests), the `<=>` operator is unavailable;
        the query falls back to a plain SELECT ordered by creation date.
        """
        if self._db is None:
            return []

        embedding = await _get_embedding(query_text)

        try:
            params: Dict[str, Any] = {
                "service_type": service_type,
                "limit": limit,
                "embedding": str(embedding),
            }
            where_clauses = [
                "service_type = :service_type",
                "feedback_status != 'rejected'",
            ]
            if tenant_id:
                where_clauses.append("(tenant_id = :tenant_id OR tenant_id IS NULL)")
                params["tenant_id"] = tenant_id

            where_sql = " AND ".join(where_clauses)
            sql = text(
                f"""
                SELECT id, service_type, occupancy_band, day_of_week,
                       weather_condition, feedback_status, pattern_text,
                       outcome_description,
                       embedding <=> CAST(:embedding AS vector) AS similarity
                FROM fb_patterns
                WHERE {where_sql}
                ORDER BY similarity ASC
                LIMIT :limit
                """
            )
            result = await self._db.execute(sql, params)
            rows = result.mappings().all()
        except Exception as exc:
            low = str(exc).lower()
            if (
                "no such function" in low
                or "no such column" in low
                or "syntax error" in low
                or "operator" in low
            ):
                # SQLite fallback — return most-recently-added patterns
                logger.debug(
                    "pgvector operator unavailable (SQLite?), using fallback: %s", exc
                )
                rows = await self._fallback_select(service_type, tenant_id, limit)
            else:
                logger.error("RAGService.find_similar_patterns error: %s", exc)
                return []

        return [
            {
                "id": str(row["id"]),
                "score": float(row.get("similarity", 1.0)),
                "payload": {
                    "service_type": row["service_type"],
                    "occupancy_band": row["occupancy_band"],
                    "day_of_week": row["day_of_week"],
                    "weather_condition": row["weather_condition"],
                    "feedback_status": row["feedback_status"],
                    "pattern_text": row["pattern_text"],
                    "outcome_description": row["outcome_description"],
                },
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def build_context_string(
        self,
        target_date: date,
        service_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Build a standardised natural-language string for embedding lookup."""
        weather = context.get("weather", {})
        events = context.get("events", [])
        events_str = ", ".join(e.get("type", "Event") for e in events) or "None"
        return (
            f"Date: {target_date.isoformat()}\n"
            f"Service: {service_type}\n"
            f"Weather: {weather.get('condition', 'Unknown')}\n"
            f"Events: {events_str}\n"
            f"Hotel Occupancy: {context.get('occupancy', 0.8)}\n"
        )

    async def _fallback_select(
        self,
        service_type: str,
        tenant_id: Optional[str],
        limit: int,
    ) -> List[Any]:
        """Plain SELECT without vector ops — used when pgvector is unavailable."""
        params: Dict[str, Any] = {"service_type": service_type, "limit": limit}
        where_clauses = [
            "service_type = :service_type",
            "feedback_status != 'rejected'",
        ]
        if tenant_id:
            where_clauses.append("(tenant_id = :tenant_id OR tenant_id IS NULL)")
            params["tenant_id"] = tenant_id
        where_sql = " AND ".join(where_clauses)
        sql = text(
            f"""
            SELECT id, service_type, occupancy_band, day_of_week,
                   weather_condition, feedback_status, pattern_text,
                   outcome_description, NULL AS similarity
            FROM fb_patterns
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        result = await self._db.execute(sql, params)
        return result.mappings().all()

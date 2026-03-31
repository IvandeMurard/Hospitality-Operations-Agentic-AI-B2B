"""RAG Service — pgvector retrieval layer (HOS-99).

Replaces the old Qdrant + Mistral stack with a single SQL query against
the `fb_patterns` table in Supabase (PostgreSQL + pgvector extension).

A single SQL cosine-distance query replaces the two-hop
Qdrant -> embedding round-trip, keeping p95 latency well within the
500 ms MCP target.

Embedding generation: Mistral (mistral-embed, 1024d) with zero-vector
fallback in dev/test when MISTRAL_API_KEY is absent.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Mistral embedding dimension
_EMBEDDING_DIM = 1024


class RAGService:
    """Retrieves similar F&B patterns from the `fb_patterns` pgvector table.

    Uses AsyncSessionLocal internally — no session injection required.
    Falls back gracefully to empty list when DB is unavailable or pgvector
    operator is missing (e.g. SQLite in unit tests).
    """

    def __init__(self) -> None:
        from mistralai.client import Mistral  # lazy import — optional dependency
        mistral_key = os.getenv("MISTRAL_API_KEY")
        self._mistral = Mistral(api_key=mistral_key) if mistral_key else None

    async def get_embedding(self, text_: str) -> List[float]:
        """Return a 1024-dimensional Mistral embedding, or zeros in dev/test."""
        if not self._mistral:
            return [0.0] * _EMBEDDING_DIM
        response = await asyncio.to_thread(
            self._mistral.embeddings.create,
            model="mistral-embed",
            inputs=[text_],
        )
        return response.data[0].embedding

    @staticmethod
    def _vec_literal(embedding: List[float]) -> str:
        return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"

    async def find_similar_patterns(
        self,
        query_text: str,
        service_type: str,
        tenant_id: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return up to *limit* patterns ordered by cosine similarity.

        Filters:
          - service_type must match exactly
          - tenant_id, when provided, restricts to that hotel's patterns plus
            global patterns (tenant_id IS NULL)
          - feedback_status != 'rejected' (exclude patterns managers disliked)

        When running against SQLite (tests), the `<=>` operator is unavailable;
        the query falls back to a plain SELECT ordered by creation date.

        Returns dicts with keys: id, score, pattern_text, outcome_description,
        payload (alias for full row data — kept for backward compatibility with
        callers that do `p.get('payload', p)`).
        """
        embedding = await self.get_embedding(query_text)
        vec = self._vec_literal(embedding)

        try:
            async with AsyncSessionLocal() as session:
                params: Dict[str, Any] = {
                    "service_type": service_type,
                    "limit": limit,
                    "vec": vec,
                }
                where_clauses = [
                    "service_type = :service_type",
                    "feedback_status != 'rejected'",
                ]
                if tenant_id:
                    where_clauses.append(
                        "(tenant_id = :tenant_id OR tenant_id IS NULL)"
                    )
                    params["tenant_id"] = tenant_id

                where_sql = " AND ".join(where_clauses)
                sql = text(
                    f"""
                    SELECT id, service_type, occupancy_band, day_of_week,
                           weather_condition, feedback_status,
                           pattern_text, outcome_description,
                           embedding <=> CAST(:vec AS vector) AS similarity
                    FROM fb_patterns
                    WHERE {where_sql}
                    ORDER BY similarity ASC
                    LIMIT :limit
                    """
                )
                result = await session.execute(sql, params)
                rows = result.mappings().all()

        except Exception as exc:
            err = str(exc).lower()
            if any(
                kw in err
                for kw in ("no such function", "no such column", "syntax error", "operator", "no such table")
            ):
                # SQLite fallback — return date-ordered patterns (no vector ops)
                logger.debug("pgvector unavailable (%s), using fallback", exc)
                rows = await self._fallback_select(service_type, tenant_id, limit)
            else:
                logger.error("RAGService.find_similar_patterns error: %s", exc)
                return []

        return [
            {
                "id": str(row["id"]),
                "score": float(row.get("similarity", 1.0)),
                # Top-level convenience keys
                "pattern_text": row.get("pattern_text", ""),
                "outcome_description": row.get("outcome_description", ""),
                # Nested payload for backward compat (reasoning_service uses p.get('payload', p))
                "payload": {
                    "service_type": row.get("service_type"),
                    "occupancy_band": row.get("occupancy_band"),
                    "day_of_week": row.get("day_of_week"),
                    "weather_condition": row.get("weather_condition"),
                    "feedback_status": row.get("feedback_status"),
                    "pattern_text": row.get("pattern_text", ""),
                    "outcome_description": row.get("outcome_description", ""),
                },
            }
            for row in rows
        ]

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
            where_clauses.append(
                "(tenant_id = :tenant_id OR tenant_id IS NULL)"
            )
            params["tenant_id"] = tenant_id
        where_sql = " AND ".join(where_clauses)
        sql = text(
            f"""
            SELECT id, service_type, occupancy_band, day_of_week,
                   weather_condition, feedback_status,
                   pattern_text, outcome_description,
                   NULL AS similarity
            FROM fb_patterns
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        async with AsyncSessionLocal() as session:
            result = await session.execute(sql, params)
            return result.mappings().all()

    def build_context_string(
        self,
        target_date: date,
        service_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Build a standardised natural-language string for embedding lookup."""
        weather = context.get("weather", {})
        events = context.get("events", [])
        events_str = (
            ", ".join(e.get("type", "Event") for e in events) or "None"
        )
        return (
            f"Date: {target_date.isoformat()}\n"
            f"Service: {service_type}\n"
            f"Weather: {weather.get('condition', 'Unknown')}\n"
            f"Events: {events_str}\n"
            f"Hotel Occupancy: {context.get('occupancy', 0.8)}\n"
        )

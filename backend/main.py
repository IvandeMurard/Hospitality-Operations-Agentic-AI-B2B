# -*- coding: utf-8 -*-
# LOAD ENVIRONMENT VARIABLES FIRST
from pathlib import Path
from dotenv import load_dotenv

# Find .env file (project root)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
print(f"[STARTUP] Loaded .env from: {env_path} (exists: {env_path.exists()})")

# IMPORT UTF-8 CONFIG FIRST - before any other imports
import backend.utf8_config  # noqa: F401

import os
import sys
import io

import uuid
from datetime import datetime, timezone
from fastapi import HTTPException


def get_debug_log_path() -> str | None:
    """Get debug log path from environment or use relative path.
    Returns None if file logging is disabled (for Docker/production)."""
    if os.getenv("DISABLE_FILE_LOGGING", "").lower() in ("true", "1", "yes"):
        return None
    return os.getenv("DEBUG_LOG_PATH", str(Path(__file__).parent.parent / "debug.log"))


def _write_debug_log(message: str) -> None:
    """Write to debug log file if file logging is enabled."""
    debug_log_path = get_debug_log_path()
    if debug_log_path is None:
        return
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"{message} - {datetime.now()}\n")
            f.flush()
    except Exception:
        pass  # Silently ignore file logging errors in production

"""
F&B Operations Agent - FastAPI Backend
MVP Phase 1 - Entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="F&B Operations Agent API",
    description="AI-powered staffing forecasting for restaurants",
    version="0.1.0"
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    import sys
    import logging
    
    logger = logging.getLogger("uvicorn")
    logger.info(f"[MIDDLEWARE] Request: {request.method} {request.url.path}")
    _write_debug_log(f"[MIDDLEWARE] Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(f"[MIDDLEWARE] Response: {response.status_code}")
    _write_debug_log(f"[MIDDLEWARE] Response: {response.status_code}")
    
    return response

# CORS for frontend
# Allow all origins in development, restrict in production
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "F&B Operations Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/test/claude")
async def test_claude():
    """Test Claude API connection"""
    from backend.utils.claude_client import ClaudeClient
    async with ClaudeClient() as client:
        return await client.test_connection()

@app.get("/test/qdrant")
async def test_qdrant():
    """Test Qdrant connection"""
    from .utils.qdrant_client import QdrantManager
    client = QdrantManager()
    return await client.test_connection()

# ============================================
# PHASE 1: Prediction Endpoints
# ============================================

from backend.models.schemas import (
    PredictionRequest,
    PredictionResponse,
    Reasoning,
    StaffRecommendation,
    StaffDelta
)
from backend.agents.demand_predictor import get_demand_predictor

@app.post("/predict", response_model=PredictionResponse)
async def create_prediction(request: PredictionRequest):
    """
    Create a staffing prediction
    
    Phase 1: Basic prediction (mocked data)
    Phase 2: Full integration (real patterns, APIs)
    """
    import logging
    logger = logging.getLogger("uvicorn")
    
    try:
        logger.info(f"[PREDICT] Request: {request.service_date} ({request.service_type})")
        _write_debug_log(f"[PREDICT] Request: {request.service_date} ({request.service_type})")
        
        # Get demand predictor
        predictor = get_demand_predictor()
        
        # Generate prediction
        result = await predictor.predict(request)
        logger.info(f"[PREDICT] Result: {result.get('predicted_covers')} covers")
        
        # TODO Hour 3-4: Add reasoning engine + staff recommender
        # For now, return basic structure
        
        # Extract reasoning from predictor result (now includes Claude-generated reasoning)
        reasoning_data = result.get("reasoning", {})
        patterns_from_result = reasoning_data.get("patterns_used", [])
        
        reasoning = Reasoning(
            summary=reasoning_data.get("summary", f"{int(result['confidence']*100)}% confidence"),
            patterns_used=patterns_from_result[:3] if patterns_from_result else [],
            confidence_factors=reasoning_data.get("confidence_factors", ["Historical patterns"])
        )
        
        # Create StaffRecommendation object from dynamic calculation
        staff_data = result.get("staff_recommendation", {})
        staff_recommendation = StaffRecommendation(
            servers=StaffDelta(
                recommended=staff_data.get("servers", {}).get("recommended", 7),
                usual=staff_data.get("servers", {}).get("usual", 7),
                delta=staff_data.get("servers", {}).get("delta", 0)
            ),
            hosts=StaffDelta(
                recommended=staff_data.get("hosts", {}).get("recommended", 2),
                usual=staff_data.get("hosts", {}).get("usual", 2),
                delta=staff_data.get("hosts", {}).get("delta", 0)
            ),
            kitchen=StaffDelta(
                recommended=staff_data.get("kitchen", {}).get("recommended", 3),
                usual=staff_data.get("kitchen", {}).get("usual", 3),
                delta=staff_data.get("kitchen", {}).get("delta", 0)
            ),
            rationale=staff_data.get("rationale", ""),
            covers_per_staff=staff_data.get("covers_per_staff", 0.0)
        )
        
        # Return PredictionResponse
        return PredictionResponse(
            prediction_id=f"pred_{uuid.uuid4().hex[:8]}",
            service_date=request.service_date,
            service_type=request.service_type,
            predicted_covers=result["predicted_covers"],
            confidence=result["confidence"],
            reasoning=reasoning,
            staff_recommendation=staff_recommendation,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
    except ValueError as e:
        error_detail = str(e).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        logger.warning(f"[PREDICT] ValueError: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)
    except Exception as e:
        error_detail = str(e).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        logger.error(f"[PREDICT] Error: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
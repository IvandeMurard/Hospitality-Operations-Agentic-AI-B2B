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


def get_debug_log_path() -> str:
    """Get debug log path from environment or use relative path"""
    return os.getenv("DEBUG_LOG_PATH", str(Path(__file__).parent.parent / "debug.log"))

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
    debug_log_path = get_debug_log_path()
    
    # Try multiple logging methods
    logger = logging.getLogger("uvicorn")
    logger.error(f"[MIDDLEWARE] Request: {request.method} {request.url.path}")
    sys.stderr.write(f"[MIDDLEWARE] Request: {request.method} {request.url.path}\n")
    sys.stderr.flush()
    
    # Write to file with explicit error handling
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[MIDDLEWARE] Request: {request.method} {request.url.path} - {datetime.now()}\n")
            f.flush()
    except Exception as e:
        logger.error(f"Error writing to debug.log: {e}")
        sys.stderr.write(f"ERROR writing debug.log: {e}\n")
        sys.stderr.flush()
    
    response = await call_next(request)
    
    logger.error(f"[MIDDLEWARE] Response: {response.status_code}")
    sys.stderr.write(f"[MIDDLEWARE] Response: {response.status_code}\n")
    sys.stderr.flush()
    
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[MIDDLEWARE] Response: {response.status_code} - {datetime.now()}\n")
            f.flush()
    except Exception as e:
        logger.error(f"Error writing to debug.log: {e}")
        sys.stderr.write(f"ERROR writing debug.log: {e}\n")
        sys.stderr.flush()
    
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
        "message": "F&B Operations Agent API",
        "status": "Phase 1 - Backend Development",
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
    import sys
    sys.stderr.write("\n" + "="*100 + "\n")
    sys.stderr.write("*** ENDPOINT /predict CALLED ***\n")
    sys.stderr.write("="*100 + "\n")
    sys.stderr.flush()
    try:
        import sys
        import traceback
        import logging
        logger = logging.getLogger("uvicorn")
        
        log_msg = f"[MAIN] *** ENDPOINT CALLED *** Received prediction request: {request.service_date} ({request.service_type})"
        logger.error(log_msg)
        sys.stderr.write(f"\n{'='*80}\n")
        sys.stderr.write(f"{log_msg}\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        debug_log_path = get_debug_log_path()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(f"{log_msg} - {datetime.now()}\n")
                f.flush()
        except Exception as e:
            logger.error(f"Error writing to debug.log: {e}")
            sys.stderr.write(f"ERROR writing debug.log: {e}\n")
            sys.stderr.flush()
        
        # Get demand predictor
        log_msg = "[MAIN] Getting demand predictor..."
        logger.error(log_msg)
        sys.stderr.write(f"{log_msg}\n")
        sys.stderr.flush()
        debug_log_path = get_debug_log_path()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(f"{log_msg} - {datetime.now()}\n")
                f.flush()
        except Exception as e:
            logger.error(f"Error writing to debug.log: {e}")
            sys.stderr.write(f"ERROR writing debug.log: {e}\n")
            sys.stderr.flush()
        # FORCE RELOAD MODULE - Clear cache
        import importlib
        import backend.agents.demand_predictor
        importlib.reload(backend.agents.demand_predictor)
        from backend.agents.demand_predictor import get_demand_predictor
        
        predictor = get_demand_predictor()
        log_msg = f"[MAIN] Got predictor instance: {type(predictor).__name__}"
        logger.error(log_msg)
        sys.stderr.write(f"{log_msg}\n")
        sys.stderr.flush()
        debug_log_path = get_debug_log_path()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(f"{log_msg} - {datetime.now()}\n")
                f.flush()
        except Exception as e:
            logger.error(f"Error writing to debug.log: {e}")
            sys.stderr.write(f"ERROR writing debug.log: {e}\n")
            sys.stderr.flush()
        
        # Generate prediction
        log_msg = "[MAIN] Calling predictor.predict()..."
        logger.error(log_msg)
        sys.stderr.write(f"{log_msg}\n")
        sys.stderr.flush()
        debug_log_path = get_debug_log_path()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(f"{log_msg} - {datetime.now()}\n")
                f.flush()
        except Exception as e:
            logger.error(f"Error writing to debug.log: {e}")
            sys.stderr.write(f"ERROR writing debug.log: {e}\n")
            sys.stderr.flush()
        try:
            result = await predictor.predict(request)
            print(f"[MAIN] Prediction result: {result.get('predicted_covers')} covers", file=sys.stderr, flush=True)
            patterns_count = len(result.get('reasoning', {}).get('patterns_used', []))
            print(f"[MAIN] Patterns in result: {patterns_count}", file=sys.stderr, flush=True)
            if patterns_count > 0:
                first_pattern = result.get('reasoning', {}).get('patterns_used', [])[0]
                if hasattr(first_pattern, 'event_type'):
                    print(f"[MAIN] First pattern: {first_pattern.event_type} - {first_pattern.actual_covers} covers", file=sys.stderr, flush=True)
                else:
                    print(f"[MAIN] First pattern (dict): {first_pattern.get('event_type')} - {first_pattern.get('actual_covers')} covers", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[MAIN] ERROR in predictor.predict(): {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            raise
        
        # TODO Hour 3-4: Add reasoning engine + staff recommender
        # For now, return basic structure
        
        # Extract reasoning from predictor result (now includes Claude-generated reasoning)
        reasoning_data = result.get("reasoning", {})
        
        patterns_from_result = reasoning_data.get("patterns_used", [])
        print(f"[MAIN] DEBUG: patterns_used from result: {len(patterns_from_result)} patterns", flush=True)
        if patterns_from_result:
            first_pattern = patterns_from_result[0]
            if hasattr(first_pattern, 'event_type'):
                print(f"[MAIN] DEBUG: First pattern object: {first_pattern.event_type} - {first_pattern.actual_covers} covers", flush=True)
            else:
                print(f"[MAIN] DEBUG: First pattern dict: {first_pattern.get('event_type')} - {first_pattern.get('actual_covers')} covers", flush=True)
        
        reasoning = Reasoning(
            summary=reasoning_data.get("summary", f"{int(result['confidence']*100)}% confidence"),
            patterns_used=patterns_from_result[:3] if patterns_from_result else [],  # Top 3 patterns
            confidence_factors=reasoning_data.get("confidence_factors", ["Historical patterns"])
        )
        
        print(f"[MAIN] DEBUG: Final reasoning.patterns_used: {len(reasoning.patterns_used)} patterns", flush=True)
        if reasoning.patterns_used:
            print(f"[MAIN] DEBUG: Final first pattern: {reasoning.patterns_used[0].event_type} - {reasoning.patterns_used[0].actual_covers} covers", flush=True)
        
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
        # Validation errors (422)
        error_detail = str(e).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        print(f"[MAIN] ValueError: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)
    except Exception as e:
        # Safely encode error message to avoid encoding issues
        error_detail = str(e).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        import traceback
        print(f"[MAIN] Exception occurred:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
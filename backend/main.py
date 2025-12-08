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

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "healthy"}

@app.get("/test/claude")
async def test_claude():
    """Test Claude API connection"""
    from utils.claude_client import ClaudeClient
    client = ClaudeClient()
    return await client.test_connection()

@app.get("/test/qdrant")
async def test_qdrant():
    """Test Qdrant connection"""
    from utils.qdrant_client import QdrantManager
    client = QdrantManager()
    return await client.test_connection()

# TODO Phase 1: Implement endpoints
# - POST /predict
# - GET /patterns
# - POST /feedback

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

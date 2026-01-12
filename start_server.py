#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de lancement du serveur FastAPI
Charge les variables d'environnement et démarre uvicorn
"""
import os
import sys
from pathlib import Path

# Load .env file (project root, consistent with backend/main.py)
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"Loading environment from {env_file}")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("✓ Environment variables loaded")
else:
    print(f"Warning: .env file not found at {env_file}")

# Run uvicorn
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("Starting F&B Operations Agent API Server")
    print("="*60 + "\n")
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

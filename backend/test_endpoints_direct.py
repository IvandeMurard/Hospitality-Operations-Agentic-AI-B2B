"""
Test direct des endpoints via les clients (sans serveur HTTP)
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.claude_client import ClaudeClient
from utils.qdrant_client import QdrantManager

async def test_all():
    """Teste tous les endpoints via leurs clients"""
    results = []
    
    print("\n" + "="*70)
    print("TESTS DIRECTS DES ENDPOINTS (via clients)")
    print("="*70)
    
    # Test 1: GET /
    print("\n" + "="*70)
    print("TEST: GET / (Root endpoint)")
    print("="*70)
    root_response = {
        "message": "F&B Operations Agent API",
        "status": "Phase 1 - Backend Development",
        "docs": "/docs"
    }
    print("Réponse JSON:")
    print(json.dumps(root_response, indent=2, ensure_ascii=False))
    results.append({
        "endpoint": "GET /",
        "status": "success",
        "status_code": 200,
        "response": root_response
    })
    
    # Test 2: GET /health
    print("\n" + "="*70)
    print("TEST: GET /health (Health check)")
    print("="*70)
    health_response = {"status": "healthy"}
    print("Réponse JSON:")
    print(json.dumps(health_response, indent=2, ensure_ascii=False))
    results.append({
        "endpoint": "GET /health",
        "status": "success",
        "status_code": 200,
        "response": health_response
    })
    
    # Test 3: GET /test/claude
    print("\n" + "="*70)
    print("TEST: GET /test/claude (Test Claude API)")
    print("="*70)
    try:
        async with ClaudeClient() as client:
            claude_response = await client.test_connection()
        print("Réponse JSON:")
        print(json.dumps(claude_response, indent=2, ensure_ascii=False))
        results.append({
            "endpoint": "GET /test/claude",
            "status": "success" if claude_response.get("status") == "success" else "error",
            "status_code": 200,
            "response": claude_response
        })
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e)
        }
        print("Réponse JSON:")
        print(json.dumps(error_response, indent=2, ensure_ascii=False))
        results.append({
            "endpoint": "GET /test/claude",
            "status": "error",
            "status_code": 500,
            "response": error_response
        })
    
    # Test 4: GET /test/qdrant
    print("\n" + "="*70)
    print("TEST: GET /test/qdrant (Test Qdrant)")
    print("="*70)
    try:
        manager = QdrantManager()
        qdrant_response = await manager.test_connection()
        print("Réponse JSON:")
        print(json.dumps(qdrant_response, indent=2, ensure_ascii=False))
        results.append({
            "endpoint": "GET /test/qdrant",
            "status": "success" if qdrant_response.get("status") == "success" else "error",
            "status_code": 200,
            "response": qdrant_response
        })
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e)
        }
        print("Réponse JSON:")
        print(json.dumps(error_response, indent=2, ensure_ascii=False))
        results.append({
            "endpoint": "GET /test/qdrant",
            "status": "error",
            "status_code": 500,
            "response": error_response
        })
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = len(results) - success_count
    
    for result in results:
        status_icon = "✓" if result.get("status") == "success" else "✗"
        print(f"{status_icon} {result['endpoint']}: {result.get('status', 'unknown')}")
    
    print(f"\nTotal: {len(results)} endpoints testés")
    print(f"Succès: {success_count}")
    print(f"Erreurs: {error_count}")
    
    # Export JSON complet
    print("\n" + "="*70)
    print("EXPORT JSON COMPLET DE TOUTES LES RÉPONSES")
    print("="*70)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results

if __name__ == "__main__":
    asyncio.run(test_all())


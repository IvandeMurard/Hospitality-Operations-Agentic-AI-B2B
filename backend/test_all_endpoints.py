"""
Script pour tester tous les endpoints de l'API et afficher les réponses JSON
"""

import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_endpoint(method: str, path: str, description: str) -> Dict[str, Any]:
    """Teste un endpoint et retourne le résultat"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"Endpoint: {method} {path}")
    print(f"{'='*70}")
    
    try:
        url = f"{BASE_URL}{path}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url)
            else:
                return {
                    "endpoint": f"{method} {path}",
                    "status": "error",
                    "error": f"Méthode {method} non supportée dans ce script"
                }
        
        result = {
            "endpoint": f"{method} {path}",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": None
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text
        
        # Affichage formaté
        print(f"Status Code: {response.status_code}")
        print(f"\nRéponse JSON:")
        print(json.dumps(result["response"], indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            result["status"] = "success"
            print(f"\n✓ Succès")
        else:
            result["status"] = "error"
            print(f"\n✗ Erreur (code {response.status_code})")
        
        return result
        
    except httpx.ConnectError:
        error_msg = "Impossible de se connecter au serveur. Assurez-vous que le serveur FastAPI est démarré (uvicorn main:app)"
        print(f"\n✗ {error_msg}")
        return {
            "endpoint": f"{method} {path}",
            "status": "error",
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Erreur: {type(e).__name__}: {str(e)}"
        print(f"\n✗ {error_msg}")
        return {
            "endpoint": f"{method} {path}",
            "status": "error",
            "error": error_msg
        }

async def main():
    """Teste tous les endpoints"""
    print("\n" + "="*70)
    print("TESTS DE TOUS LES ENDPOINTS DE L'API")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print("Assurez-vous que le serveur est démarré avec: uvicorn main:app --reload")
    
    results = []
    
    # Liste de tous les endpoints à tester
    endpoints = [
        ("GET", "/", "Root endpoint - Informations de l'API"),
        ("GET", "/health", "Health check endpoint"),
        ("GET", "/test/claude", "Test connexion Claude API"),
        ("GET", "/test/qdrant", "Test connexion Qdrant"),
    ]
    
    for method, path, description in endpoints:
        result = await test_endpoint(method, path, description)
        results.append(result)
    
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
    print("EXPORT JSON COMPLET")
    print("="*70)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results

if __name__ == "__main__":
    asyncio.run(main())


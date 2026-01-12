#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour tester le demand_predictor directement
"""
import sys
import asyncio
from datetime import date

# Test d'import
print("=" * 60)
print("TEST 1: Import du module")
print("=" * 60)

try:
    from backend.agents.demand_predictor import DemandPredictorAgent
    from backend.models.schemas import PredictionRequest, ServiceType
    print("✓ Imports réussis")
except Exception as e:
    print(f"✗ Erreur d'import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test d'instanciation
print("\n" + "=" * 60)
print("TEST 2: Instanciation de l'agent")
print("=" * 60)

try:
    agent = DemandPredictorAgent()
    print("✓ Agent créé")
except Exception as e:
    print(f"✗ Erreur d'instanciation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test de prédiction
print("\n" + "=" * 60)
print("TEST 3: Exécution d'une prédiction")
print("=" * 60)

async def test_prediction():
    try:
        request = PredictionRequest(
            restaurant_id="test-restaurant",
            service_date=date(2024, 6, 15),  # Samedi
            service_type=ServiceType.DINNER
        )
        
        print(f"Request: {request.restaurant_id}, {request.service_date}, {request.service_type}")
        print("\n" + "-" * 60)
        print("Exécution de la prédiction (regardez les prints de debug):")
        print("-" * 60 + "\n")
        
        result = await agent.predict(request)
        
        print("\n" + "-" * 60)
        print("RÉSULTAT:")
        print("-" * 60)
        print(f"Predicted covers: {result['predicted_covers']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Patterns: {len(result.get('patterns', []))} patterns")
        
        if result.get('patterns'):
            print("\nPremier pattern:")
            p = result['patterns'][0]
            print(f"  - Date: {p.date}")
            print(f"  - Type: {p.event_type}")
            print(f"  - Covers: {p.actual_covers}")
        
        if result.get('reasoning'):
            print("\nReasoning:")
            print(f"  - Summary: {result['reasoning'].get('summary', 'N/A')}")
        
        print("\n✓ Prédiction réussie")
        return result
        
    except Exception as e:
        print(f"\n✗ Erreur de prédiction: {e}")
        import traceback
        traceback.print_exc()
        return None

# Exécuter le test
print("Démarrage du test asynchrone...\n")
result = asyncio.run(test_prediction())

print("\n" + "=" * 60)
print("FIN DES TESTS")
print("=" * 60)

if result:
    print("\n✓ Tous les tests ont réussi")
    print("\nSi vous voyez les prints de debug (*** USING NEW CONTEXTUAL GENERATION LOGIC ***),")
    print("cela confirme que le nouveau code s'exécute correctement.")
else:
    print("\n✗ Échec des tests")

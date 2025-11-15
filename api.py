from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from agents.analyzer import AnalyzerAgent
from agents.pattern_search import PatternSearcher
from agents.predictor import PredictorAgent

# Initialiser FastAPI
app = FastAPI(
    title="F&B Operations Agent API",
    description="API de prédiction F&B (covers + staff + confiance) basée sur Qdrant + Mistral",
    version="1.0.0",
)

# Instancier les agents une seule fois (réutilisés à chaque requête)
analyzer = AnalyzerAgent()
pattern_searcher = PatternSearcher()
predictor = PredictorAgent()


# ---------- Modèles d'entrée / sortie ----------

class PredictionRequest(BaseModel):
    date: str           # ex: "2024-11-15"
    events: str         # ex: "Soirée DJ, promo cocktails, match de foot à 600m"
    weather: str        # ex: "Pluie faible, 12°C"


class PredictionResponse(BaseModel):
    date: str
    events: str
    weather: str
    expected_covers: int
    recommended_staff: int
    confidence: int
    key_factors: List[str]


# ---------- Endpoint principal ----------

@app.post("/predict", response_model=PredictionResponse)
def predict_covers(req: PredictionRequest) -> PredictionResponse:
    """
    Endpoint de prédiction :
    - Input : date future, événements prévus, météo
    - Process : Analyzer -> Qdrant vector search -> Predictor
    - Output : covers, staff, score de confiance
    """

    # 1) Construire une description compréhensible par l’agent
    event_description = (
        f"Date: {req.date}. "
        f"Events: {req.events}. "
        f"Weather forecast: {req.weather}."
    )

    # 2) Analyse + embedding
    analysis = analyzer.analyze(event_description)

    # 3) Recherche des patterns similaires dans Qdrant
    similar_patterns = pattern_searcher.search_similar_patterns(
        analysis["embedding"],
        limit=3,
    )

    # 4) Prédiction (covers / staff / confiance)
    prediction = predictor.predict(
        event_description=event_description,
        features=analysis["features"],
        similar_patterns=similar_patterns,
    )

    # (Optionnel pour l’API : génération audio)
    # voice_file = predictor.generate_voice_output(event_description, prediction)

    # 5) Normaliser la réponse
    return PredictionResponse(
        date=req.date,
        events=req.events,
        weather=req.weather,
        expected_covers=int(prediction["expected_covers"]),
        recommended_staff=int(prediction["recommended_staff"]),
        confidence=int(prediction["confidence"]),
        key_factors=prediction["key_factors"],
    )

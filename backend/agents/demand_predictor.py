"""
Demand Predictor Agent
Predicts restaurant covers based on patterns, events, weather
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import uuid
import random
import os
from pathlib import Path

from ..models.schemas import (
    PredictionRequest,
    Pattern,
    ServiceType
)
from .reasoning_engine import get_reasoning_engine
from mistralai import Mistral
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


def get_debug_log_path() -> str | None:
    """Get debug log path from environment or use relative path.
    Returns None if file logging is disabled (for Docker/production)."""
    if os.getenv("DISABLE_FILE_LOGGING", "").lower() in ("true", "1", "yes"):
        return None
    return os.getenv("DEBUG_LOG_PATH", str(Path(__file__).parent.parent.parent / "debug.log"))


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


from .staff_recommender import StaffRecommenderAgent


class DemandPredictorAgent:
    """
    Agent responsible for predicting restaurant demand (covers)
    
    Uses:
    - Historical pattern matching (mock in Phase 1, Qdrant in Phase 2)
    - External context (events, weather)
    - Claude AI for reasoning
    """
    
    def __init__(self):
        """Initialize predictor agent"""
        self.staff_recommender = StaffRecommenderAgent()
        
        # Initialize Qdrant client
        self.qdrant_client = None
        self.mistral_client = None
        self._init_vector_clients()
    
    def _init_vector_clients(self):
        """Initialize Qdrant and Mistral clients for vector search"""
        try:
            # Load .env from project root if it exists (for local dev)
            # In production (Docker/HuggingFace), env vars are injected directly
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent.parent / ".env"
            if env_path.exists():
                _write_debug_log(f"[INIT] Loading .env from: {env_path}")
                load_dotenv(dotenv_path=env_path, override=True)
            else:
                _write_debug_log("[INIT] No .env file found, using system environment variables")
            
            # Get environment variables (from .env file or system env)
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            
            _write_debug_log(f"[INIT] QDRANT_URL found: {bool(qdrant_url)}")
            _write_debug_log(f"[INIT] QDRANT_API_KEY found: {bool(qdrant_api_key)}")
            _write_debug_log(f"[INIT] MISTRAL_API_KEY found: {bool(mistral_api_key)}")
            
            if qdrant_url and qdrant_api_key:
                try:
                    self.qdrant_client = QdrantClient(
                        url=qdrant_url,
                        api_key=qdrant_api_key
                    )
                    # Test connection by getting collections
                    collections = self.qdrant_client.get_collections()
                    _write_debug_log(f"[INIT] Qdrant client initialized successfully. Collections: {[c.name for c in collections.collections]}")
                except Exception as e:
                    _write_debug_log(f"[INIT] Qdrant connection failed: {e}")
                    self.qdrant_client = None
            else:
                _write_debug_log("[INIT] Qdrant credentials missing")
                self.qdrant_client = None
            
            if mistral_api_key:
                try:
                    self.mistral_client = Mistral(api_key=mistral_api_key)
                    _write_debug_log("[INIT] Mistral client initialized successfully")
                except Exception as e:
                    _write_debug_log(f"[INIT] Mistral client init failed: {e}")
                    self.mistral_client = None
            else:
                _write_debug_log("[INIT] Mistral API key not found or empty")
                self.mistral_client = None
                
        except Exception as e:
            _write_debug_log(f"[INIT] Vector client init failed: {e}")
            import traceback
            _write_debug_log(f"[INIT] Traceback: {traceback.format_exc()}")
            self.qdrant_client = None
            self.mistral_client = None
    
    async def predict(self, request: PredictionRequest) -> Dict:
        """
        Main prediction method
        
        Args:
            request: PredictionRequest with restaurant_id, service_date, service_type
            
        Returns:
            Dict with predicted_covers, confidence, patterns, reasoning
        """
        import logging
        logger = logging.getLogger("uvicorn")
        
        logger.info(f"[PREDICT] Starting prediction for {request.restaurant_id} on {request.service_date}")
        _write_debug_log(f"[PREDICT] Starting prediction for {request.restaurant_id}")
        
        # Step 1: Fetch external context
        context = await self._fetch_external_context(request)
        
        # Step 2: Find similar patterns
        similar_patterns = await self._find_similar_patterns(request, context)
        logger.info(f"[PREDICT] Found {len(similar_patterns)} similar patterns")
        
        # Step 3: Calculate prediction
        prediction = await self._calculate_prediction(similar_patterns, context)
        
        # Step 4: Calculate staff recommendation
        staff_result = await self.staff_recommender.recommend(
            predicted_covers=prediction["predicted_covers"],
            restaurant_id=request.restaurant_id
        )
        prediction["staff_recommendation"] = staff_result
        
        # Step 5: Generate reasoning with Claude
        reasoning_engine = get_reasoning_engine()
        reasoning = await reasoning_engine.generate_reasoning(
            predicted_covers=prediction["predicted_covers"],
            confidence=prediction["confidence"],
            patterns=similar_patterns,
            context=context,
            service_date=request.service_date,
            service_type=request.service_type
        )
        
        # Combine prediction + reasoning
        prediction["reasoning"] = reasoning
        
        return prediction
    
    async def _fetch_external_context(self, request: PredictionRequest) -> Dict:
        """
        Fetch external context: events, weather, holidays
        
        Phase 1: MOCKED data (no real APIs yet)
        Phase 2: Integrate PredictHQ, Weather API
        """
        # Determine day type
        day_of_week = request.service_date.strftime("%A")
        is_weekend = request.service_date.weekday() in [5, 6]
        is_friday = request.service_date.weekday() == 4
        
        # Generate realistic events based on day
        events = self._generate_mock_events(request.service_date, is_weekend)
        
        # Generate realistic weather
        weather = self._generate_mock_weather(request.service_date, is_weekend)
        
        # Check if holiday
        is_holiday = self._is_mock_holiday(request.service_date)
        holiday_name = self._get_holiday_name(request.service_date) if is_holiday else None
        
        return {
            "day_of_week": day_of_week,
            "events": events,
            "weather": weather,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "day_type": "weekend" if is_weekend else "friday" if is_friday else "weekday"
        }
    
    def _generate_mock_events(self, service_date: date, is_weekend: bool) -> List[Dict]:
        """Generate realistic mock events based on date"""
        events = []
        
        # Seed random with date for deterministic results
        random.seed(service_date.toordinal())
        
        # Weekend = higher chance of events
        event_probability = 0.7 if is_weekend else 0.3
        
        if random.random() < event_probability:
            event_types = [
                {
                    "type": "Concert",
                    "names": ["Coldplay", "Taylor Swift", "Ed Sheeran", "Beyonce"],
                    "attendance_range": (30000, 60000),
                    "distance_range": (1.5, 5.0),
                    "impact": "high"
                },
                {
                    "type": "Sports Match",
                    "names": ["PSG vs Marseille", "France vs England", "Champions League Final"],
                    "attendance_range": (40000, 80000),
                    "distance_range": (2.0, 6.0),
                    "impact": "high"
                },
                {
                    "type": "Theater Show",
                    "names": ["Hamilton", "Les Miserables", "Phantom of the Opera"],
                    "attendance_range": (1000, 3000),
                    "distance_range": (0.5, 2.0),
                    "impact": "medium"
                },
                {
                    "type": "Conference",
                    "names": ["Tech Summit", "Marketing Expo", "Healthcare Forum"],
                    "attendance_range": (500, 2000),
                    "distance_range": (0.2, 1.5),
                    "impact": "medium"
                }
            ]
            
            event_type = random.choice(event_types)
            
            event = {
                "type": event_type["type"],
                "name": random.choice(event_type["names"]),
                "distance_km": round(random.uniform(*event_type["distance_range"]), 1),
                "expected_attendance": random.randint(*event_type["attendance_range"]),
                "start_time": "20:00" if event_type["type"] in ["Concert", "Theater Show"] else "19:00",
                "impact": event_type["impact"]
            }
            
            events.append(event)
            
            # 20% chance of second event on weekends
            if is_weekend and random.random() < 0.2:
                second_type = random.choice([t for t in event_types if t != event_type])
                second_event = {
                    "type": second_type["type"],
                    "name": random.choice(second_type["names"]),
                    "distance_km": round(random.uniform(*second_type["distance_range"]), 1),
                    "expected_attendance": random.randint(*second_type["attendance_range"]),
                    "start_time": "21:00",
                    "impact": second_type["impact"]
                }
                events.append(second_event)
        
        return events
    
    def _generate_mock_weather(self, service_date: date, is_weekend: bool) -> Dict:
        """Generate realistic mock weather based on date"""
        random.seed(service_date.toordinal() + 1000)
        
        conditions = [
            ("Clear", 0.4),
            ("Partly Cloudy", 0.3),
            ("Cloudy", 0.15),
            ("Rain", 0.10),
            ("Heavy Rain", 0.03),
            ("Snow", 0.02)
        ]
        
        rand = random.random()
        cumulative = 0
        selected_condition = "Clear"
        
        for condition, prob in conditions:
            cumulative += prob
            if rand <= cumulative:
                selected_condition = condition
                break
        
        # Temperature varies by month
        month = service_date.month
        if month in [12, 1, 2]:
            temp_range = (0, 10)
        elif month in [3, 4, 5]:
            temp_range = (10, 20)
        elif month in [6, 7, 8]:
            temp_range = (20, 30)
        else:
            temp_range = (10, 20)
        
        temperature = random.randint(*temp_range)
        
        precipitation = {
            "Clear": 0,
            "Partly Cloudy": random.randint(0, 10),
            "Cloudy": random.randint(10, 30),
            "Rain": random.randint(40, 70),
            "Heavy Rain": random.randint(70, 100),
            "Snow": random.randint(30, 60)
        }.get(selected_condition, 0)
        
        wind_speed = random.randint(5, 25)
        
        return {
            "condition": selected_condition,
            "temperature": temperature,
            "precipitation": precipitation,
            "wind_speed": wind_speed
        }
    
    def _is_mock_holiday(self, service_date: date) -> bool:
        """Check if date is a holiday"""
        holidays = [
            (12, 24), (12, 25),  # Christmas Eve & Day
            (12, 31), (1, 1),    # New Year's
            (7, 14),  # Bastille Day
            (11, 11), # Veterans Day
            (5, 1),   # Labor Day
        ]
        
        return (service_date.month, service_date.day) in holidays
    
    def _get_holiday_name(self, service_date: date) -> Optional[str]:
        """Get holiday name if date is a holiday"""
        holidays = {
            (12, 24): "Christmas Eve",
            (12, 25): "Christmas",
            (12, 31): "New Year's Eve",
            (1, 1): "New Year's Day",
            (7, 14): "Bastille Day",
            (11, 11): "Veterans Day",
            (5, 1): "Labor Day",
        }
        
        return holidays.get((service_date.month, service_date.day))
    
    def _build_context_string(self, request: PredictionRequest, context: Dict) -> str:
        """Build context string for embedding (same format as seed_qdrant.py)"""
        events_str = ", ".join([e["type"] for e in context.get("events", [])]) or "None"
        weather = context.get("weather", {})
        
        # Format date as YYYY-MM-DD string (same as seed_qdrant.py)
        date_str = request.service_date.strftime("%Y-%m-%d")
        
        # Get service type as string (handle enum)
        service_type_str = request.service_type.value if hasattr(request.service_type, 'value') else str(request.service_type)
        
        return f"""Date: {date_str} ({context['day_of_week']})
Service: {service_type_str}
Day type: {context['day_type']}
Hotel occupancy: 0.75
Guests in house: 150
Weather: {weather.get('condition', 'Unknown')}, {weather.get('temperature', 'N/A')}°C
Events nearby: {events_str}
Holiday: {context.get('holiday_name', 'None') if context.get('is_holiday') else 'None'}"""

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Mistral"""
        response = self.mistral_client.embeddings.create(
            model="mistral-embed",
            inputs=[text]
        )
        return response.data[0].embedding

    def _search_qdrant(self, embedding: List[float], service_type: str, limit: int = 5) -> List:
        """Search Qdrant for similar patterns"""
        try:
            # Build filter for service type
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="service_type",
                        match=MatchValue(value=service_type)
                    )
                ]
            )
            
            results = self.qdrant_client.search(
                collection_name="fb_patterns",
                query_vector=embedding,
                query_filter=search_filter,
                limit=limit
            )
            
            return results
        except Exception as e:
            # Try without filter if filter fails
            _write_debug_log(f"[PATTERNS] Filter search failed: {e}, trying without filter")
            try:
                results = self.qdrant_client.search(
                    collection_name="fb_patterns",
                    query_vector=embedding,
                    limit=limit
                )
                # Filter results manually by service_type
                filtered_results = [r for r in results if r.payload.get("service_type") == service_type]
                return filtered_results[:limit]
            except Exception as e2:
                _write_debug_log(f"[PATTERNS] Search without filter also failed: {e2}")
                raise e2

    def _qdrant_hit_to_pattern(self, hit) -> Pattern:
        """Convert Qdrant search hit to Pattern object"""
        payload = hit.payload
        
        # Build event description
        events = payload.get("events", [])
        if events:
            event_desc = f"{events[0]} nearby"
        elif payload.get("is_holiday"):
            event_desc = f"{payload.get('holiday_name', 'Holiday')} service"
        else:
            event_desc = f"Regular {payload.get('day_type', 'weekday')} service"
        
        return Pattern(
            pattern_id=payload.get("pattern_id", f"pat_{hit.id}"),
            date=datetime.strptime(payload["date"], "%Y-%m-%d").date(),
            event_type=event_desc,
            actual_covers=payload["actual_covers"],
            similarity=round(hit.score, 2),
            metadata={
                "day_of_week": payload.get("day_of_week"),
                "weather": payload.get("weather_condition"),
                "events": len(events),
                "holiday": payload.get("holiday_name") if payload.get("is_holiday") else None,
                "source": "qdrant"
            }
        )
    
    async def _generate_mock_patterns(
        self,
        request: PredictionRequest,
        context: Dict
    ) -> List[Pattern]:
        """
        Generate mock patterns (fallback when Qdrant unavailable)
        Original Phase 1 logic preserved for resilience
        """
        random.seed(request.service_date.toordinal() + 2000)
        
        # Base covers vary by day type
        if context['day_type'] == 'weekend':
            base_covers = random.randint(130, 160)
        elif context['day_type'] == 'friday':
            base_covers = random.randint(120, 145)
        else:
            base_covers = random.randint(100, 130)
        
        # Adjust for events
        if context['events']:
            event_boost = len(context['events']) * 15
            base_covers += event_boost
        
        # Adjust for weather
        if context['weather']['condition'] == 'Rain':
            base_covers -= 10
        elif context['weather']['condition'] == 'Heavy Rain':
            base_covers -= 20
        
        # SPECIAL CASE: Holidays
        if context['is_holiday']:
            holiday_name = context['holiday_name']
            if holiday_name in ["Christmas Eve", "Christmas"]:
                base_covers = random.randint(40, 70)
            elif holiday_name == "New Year's Eve":
                base_covers = random.randint(180, 220)
            elif holiday_name == "New Year's Day":
                base_covers = random.randint(50, 80)
        
        # Generate 3 patterns around this base
        patterns = []
        for i in range(3):
            months_ago = random.randint(3, 12)
            pattern_date = request.service_date - timedelta(days=30 * months_ago)
            pattern_covers = base_covers + random.randint(-10, 10)
            
            if context['events']:
                event_desc = f"{context['events'][0]['type']} nearby"
            elif context['is_holiday']:
                event_desc = f"{context['holiday_name']} service"
            elif context['weather']['condition'] in ['Rain', 'Heavy Rain']:
                event_desc = f"Rainy {context['day_of_week']}"
            else:
                event_desc = f"Regular {context['day_type']} service"
            
            pattern = Pattern(
                pattern_id=f"mock_{i+1:03d}",
                date=pattern_date,
                event_type=event_desc,
                actual_covers=max(30, pattern_covers),
                similarity=round(random.uniform(0.85, 0.95), 2),
                metadata={
                    "day_of_week": context['day_of_week'],
                    "weather": context['weather']['condition'],
                    "events": len(context['events']),
                    "holiday": context['holiday_name'] if context['is_holiday'] else None,
                    "source": "mock"
                }
            )
            patterns.append(pattern)
        
        patterns.sort(key=lambda p: p.similarity, reverse=True)
        return patterns
    
    async def _find_similar_patterns(
        self, 
        request: PredictionRequest, 
        context: Dict
    ) -> List[Pattern]:
        """
        Find similar patterns using Qdrant vector search
        
        Falls back to mock generation if Qdrant unavailable
        """
        import logging
        logger = logging.getLogger("uvicorn")
        
        # Try Qdrant search first
        if self.qdrant_client and self.mistral_client:
            try:
                _write_debug_log("[PATTERNS] Using Qdrant vector search")
                logger.info("[PATTERNS] Using Qdrant vector search")
                
                # Build context string (same format as seeded patterns)
                context_str = self._build_context_string(request, context)
                _write_debug_log(f"[PATTERNS] Context: {context_str[:100]}...")
                
                # Get embedding
                embedding = self._get_embedding(context_str)
                
                # Get service type as string and map to Qdrant values
                service_type = request.service_type.value if hasattr(request.service_type, 'value') else str(request.service_type)
                # Map brunch to breakfast (closest match in Qdrant patterns)
                if service_type == "brunch":
                    service_type = "breakfast"
                
                # Search Qdrant
                hits = self._search_qdrant(embedding, service_type, limit=5)
                
                if hits:
                    patterns = [self._qdrant_hit_to_pattern(hit) for hit in hits]
                    logger.info(f"[PATTERNS] Found {len(patterns)} patterns from Qdrant")
                    _write_debug_log(f"[PATTERNS] Found {len(patterns)} patterns, top score: {patterns[0].similarity}")
                    return patterns
                else:
                    logger.warning("[PATTERNS] No Qdrant results, falling back to mock")
                    _write_debug_log("[PATTERNS] No Qdrant results, using fallback")
                    
            except Exception as e:
                logger.error(f"[PATTERNS] Qdrant search failed: {e}")
                _write_debug_log(f"[PATTERNS] Qdrant error: {e}, using fallback")
        
        # FALLBACK: Generate mock patterns (existing logic)
        _write_debug_log("[PATTERNS] Using mock pattern generation (fallback)")
        logger.info("[PATTERNS] Using mock pattern generation")
        return await self._generate_mock_patterns(request, context)
    
    async def _calculate_prediction(
        self,
        patterns: List[Pattern],
        context: Dict
    ) -> Dict:
        """Calculate weighted prediction based on similar patterns"""
        
        if not patterns:
            return {
                "predicted_covers": 120,
                "confidence": 0.60,
                "method": "fallback"
            }
        
        # Weighted average calculation
        total_weight = sum(p.similarity for p in patterns)
        weighted_sum = sum(p.actual_covers * p.similarity for p in patterns)
        predicted_covers = int(weighted_sum / total_weight)
        
        # Average similarity = confidence proxy
        avg_similarity = total_weight / len(patterns)
        confidence = round(avg_similarity, 2)
        
        return {
            "predicted_covers": predicted_covers,
            "confidence": confidence,
            "method": "weighted_average",
            "patterns_count": len(patterns)
        }


# Singleton instance
_demand_predictor = None


def get_demand_predictor() -> DemandPredictorAgent:
    """Get demand predictor singleton"""
    global _demand_predictor
    if _demand_predictor is None:
        _demand_predictor = DemandPredictorAgent()
    return _demand_predictor

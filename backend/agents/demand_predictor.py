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
    
    async def _find_similar_patterns(
        self, 
        request: PredictionRequest, 
        context: Dict
    ) -> List[Pattern]:
        """
        Generate CONTEXTUAL patterns that match current situation
        
        Phase 1: Smart mock data based on context
        Phase 2: Real Qdrant vector search with embeddings
        """
        _write_debug_log("[PATTERNS] Generating contextual patterns")
        
        # Seed for deterministic but varied results
        random.seed(request.service_date.toordinal() + 2000)
        
        # Base covers vary by day type
        if context['day_type'] == 'weekend':
            base_covers = random.randint(130, 160)
        elif context['day_type'] == 'friday':
            base_covers = random.randint(120, 145)
        else:  # weekday
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
            # Historical date: 3-12 months ago
            months_ago = random.randint(3, 12)
            pattern_date = request.service_date - timedelta(days=30 * months_ago)
            
            # Vary covers slightly around base
            pattern_covers = base_covers + random.randint(-10, 10)
            
            # Event type description
            if context['events']:
                event_desc = f"{context['events'][0]['type']} nearby"
            elif context['is_holiday']:
                event_desc = f"{context['holiday_name']} service"
            elif context['weather']['condition'] in ['Rain', 'Heavy Rain']:
                event_desc = f"Rainy {context['day_of_week']}"
            else:
                event_desc = f"Regular {context['day_type']} service"
            
            pattern = Pattern(
                pattern_id=f"pat_{i+1:03d}",
                date=pattern_date,
                event_type=event_desc,
                actual_covers=max(30, pattern_covers),  # Min 30 covers
                similarity=round(random.uniform(0.85, 0.95), 2),
                metadata={
                    "day_of_week": context['day_of_week'],
                    "weather": context['weather']['condition'],
                    "events": len(context['events']),
                    "holiday": context['holiday_name'] if context['is_holiday'] else None
                }
            )
            
            patterns.append(pattern)
        
        # Sort by similarity
        patterns.sort(key=lambda p: p.similarity, reverse=True)
        
        return patterns
    
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

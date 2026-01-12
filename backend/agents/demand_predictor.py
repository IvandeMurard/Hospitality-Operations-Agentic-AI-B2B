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


def get_debug_log_path() -> str:
    """Get debug log path from environment or use relative path"""
    return os.getenv("DEBUG_LOG_PATH", str(Path(__file__).parent.parent.parent / "debug.log"))
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
        import sys
        import logging
        logger = logging.getLogger("uvicorn")
        log_msg1 = f"[PREDICT] *** METHOD CALLED *** Starting prediction for {request.restaurant_id} on {request.service_date} ({request.service_type})"
        log_msg2 = "[PREDICT] *** USING NEW CONTEXTUAL CODE VERSION ***"
        logger.error(log_msg1)
        logger.error(log_msg2)
        sys.stderr.write(f"{log_msg1}\n")
        sys.stderr.write(f"{log_msg2}\n")
        sys.stderr.flush()
        debug_log_path = get_debug_log_path()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"{log_msg1} - {datetime.now()}\n{log_msg2} - {datetime.now()}\n")
                f.flush()
        except Exception as e:
            logger.error(f"Error writing to debug.log: {e}")
            sys.stderr.write(f"ERROR writing debug.log: {e}\n")
            sys.stderr.flush()
        
        # Step 1: Fetch external context
        context = await self._fetch_external_context(request)
        
        # Step 2: Find similar patterns (NOW CONTEXTUAL!)
        sys.stderr.write(f"[PREDICT] *** ABOUT TO CALL _find_similar_patterns ***\n")
        sys.stderr.flush()
        logger.error("[PREDICT] *** ABOUT TO CALL _find_similar_patterns ***")
        
        similar_patterns = []
        try:
            similar_patterns = await self._find_similar_patterns(request, context)
            
            # Success logging
            sys.stderr.write(f"[PREDICT] *** _find_similar_patterns RETURNED {len(similar_patterns)} patterns ***\n")
            sys.stderr.flush()
            logger.error(f"[PREDICT] *** _find_similar_patterns RETURNED {len(similar_patterns)} patterns ***")
            
            if similar_patterns:
                for idx, p in enumerate(similar_patterns):
                    pattern_info = f"  Pattern {idx+1}: {p.event_type} - {p.actual_covers} covers - Date: {p.date} - Similarity: {p.similarity}"
                    sys.stderr.write(f"{pattern_info}\n")
                    logger.error(pattern_info)
            else:
                sys.stderr.write("[PREDICT] WARNING: No patterns returned!\n")
                logger.warning("[PREDICT] WARNING: No patterns returned!")
                
        except Exception as e:
            # Detailed error logging with full traceback
            import traceback
            error_msg = f"[PREDICT] *** EXCEPTION in _find_similar_patterns ***"
            sys.stderr.write(f"\n{'='*80}\n")
            sys.stderr.write(f"{error_msg}\n")
            sys.stderr.write(f"Exception Type: {type(e).__name__}\n")
            sys.stderr.write(f"Exception Message: {str(e)}\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write("Full Traceback:\n")
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.flush()
            
            logger.error(error_msg)
            logger.error(f"Exception Type: {type(e).__name__}")
            logger.error(f"Exception Message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Write to debug.log for persistence
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"{error_msg} - {datetime.now()}\n")
                    f.write(f"Exception: {type(e).__name__}: {str(e)}\n")
                    f.write(f"Traceback:\n{traceback.format_exc()}\n")
                    f.write(f"{'='*80}\n")
            except:
                pass
            
            raise
        
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
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        print("  [CONTEXT] Fetching external context...", file=sys.stderr, flush=True)
        
        # Determine day type
        day_of_week = request.service_date.strftime("%A")
        is_weekend = request.service_date.weekday() in [5, 6]
        is_friday = request.service_date.weekday() == 4
        
        # Generate realistic events based on day
        events = self._generate_mock_events(request.service_date, is_weekend)
        print(f"  [CONTEXT] Generated {len(events)} events")
        
        # Generate realistic weather
        weather = self._generate_mock_weather(request.service_date, is_weekend)
        print(f"  [CONTEXT] Weather: {weather['condition']}, {weather['temperature']}C")
        
        # Check if holiday
        is_holiday = self._is_mock_holiday(request.service_date)
        holiday_name = self._get_holiday_name(request.service_date) if is_holiday else None
        print(f"  [CONTEXT] Holiday: {is_holiday} ({holiday_name if holiday_name else 'None'})")
        
        context = {
            "day_of_week": day_of_week,
            "events": events,
            "weather": weather,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "day_type": "weekend" if is_weekend else "friday" if is_friday else "weekday"
        }
        
        print(f"  [CONTEXT] OK - {context['day_of_week']} ({context['day_type']}), {len(context['events'])} events")
        return context
    
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
        import sys
        import logging
        logger = logging.getLogger("uvicorn")
        
        # CRITICAL: This print MUST appear if method is called
        CRITICAL_MSG = "*** _find_similar_patterns CALLED - NEW CODE VERSION ***"
        logger.error(CRITICAL_MSG)
        sys.stderr.write("\n" + "=" * 100 + "\n")
        sys.stderr.write(CRITICAL_MSG + "\n")
        sys.stderr.write("=" * 100 + "\n")
        sys.stderr.flush()
        
        log_msg = "  [PATTERNS] *** GENERATING CONTEXTUAL PATTERNS - NEW CODE VERSION ***"
        logger.error(log_msg)
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write(f"{log_msg}\n")
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write("  [PATTERNS] Generating contextual patterns...\n")
        sys.stderr.flush()
        debug_log_path = get_debug_log_path()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"{log_msg} - {datetime.now()}\n")
                f.flush()
        except Exception as e:
            logger.error(f"Error writing to debug.log: {e}")
            sys.stderr.write(f"ERROR writing debug.log: {e}\n")
            sys.stderr.flush()
        
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
            print(f"  [PATTERNS] Event boost: +{event_boost} covers ({len(context['events'])} events)", file=sys.stderr, flush=True)
        
        # Adjust for weather
        if context['weather']['condition'] == 'Rain':
            base_covers -= 10
            print(f"  [PATTERNS] Weather penalty: -10 covers (Rain)", file=sys.stderr, flush=True)
        elif context['weather']['condition'] == 'Heavy Rain':
            base_covers -= 20
            print(f"  [PATTERNS] Weather penalty: -20 covers (Heavy Rain)", file=sys.stderr, flush=True)
        
        # SPECIAL CASE: Holidays (CRITICAL FIX!)
        if context['is_holiday']:
            holiday_name = context['holiday_name']
            if holiday_name in ["Christmas Eve", "Christmas"]:
                base_covers = random.randint(40, 70)
                print(f"  [PATTERNS] HOLIDAY OVERRIDE: {holiday_name} = {base_covers} covers (very quiet)", file=sys.stderr, flush=True)
            elif holiday_name == "New Year's Eve":
                base_covers = random.randint(180, 220)
                print(f"  [PATTERNS] HOLIDAY OVERRIDE: {holiday_name} = {base_covers} covers (very busy)", file=sys.stderr, flush=True)
            elif holiday_name == "New Year's Day":
                base_covers = random.randint(50, 80)
                print(f"  [PATTERNS] HOLIDAY OVERRIDE: {holiday_name} = {base_covers} covers (recovery day)", file=sys.stderr, flush=True)
        
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
        
        print(f"  [PATTERNS] OK - Generated 3 contextual patterns (avg: {int(sum(p.actual_covers for p in patterns)/3)} covers)", file=sys.stderr, flush=True)
        
        return patterns
    
    async def _calculate_prediction(
        self,
        patterns: List[Pattern],
        context: Dict
    ) -> Dict:
        """Calculate weighted prediction based on similar patterns"""
        print("  [CALC] Calculating prediction...")
        
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
        
        print(f"  [CALC] OK - Prediction: {predicted_covers} covers ({int(confidence*100)}% confidence)")
        
        return {
            "predicted_covers": predicted_covers,
            "confidence": confidence,
            "method": "weighted_average",
            "patterns_count": len(patterns)
        }


# Singleton instance - DISABLED FOR DEBUGGING
_demand_predictor = None

def get_demand_predictor() -> DemandPredictorAgent:
    """Get demand predictor singleton - FORCED NEW INSTANCE FOR DEBUGGING"""
    global _demand_predictor
    import sys
    import logging
    logger = logging.getLogger("uvicorn")
    
    # FORCE NEW INSTANCE EVERY TIME - NO CACHING
    sys.stderr.write(f"[SINGLETON] *** FORCING NEW INSTANCE *** (no cache)\n")
    sys.stderr.flush()
    logger.error("[SINGLETON] *** FORCING NEW INSTANCE *** (no cache)")
    
    # Always create new instance
    _demand_predictor = DemandPredictorAgent()
    sys.stderr.write(f"[SINGLETON] New instance created: {id(_demand_predictor)}\n")
    sys.stderr.flush()
    logger.error(f"[SINGLETON] New instance created: {id(_demand_predictor)}")
    
    return _demand_predictor

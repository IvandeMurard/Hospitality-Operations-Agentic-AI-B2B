"""
Agent 2: Predictor
Analyzes patterns and generates prediction with voice output
"""

from mistralai import Mistral
from elevenlabs import generate, save
import os
from dotenv import load_dotenv
import json

load_dotenv()

class PredictorAgent:
    def __init__(self):
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        os.environ["ELEVEN_LABS_API_KEY"] = os.getenv("ELEVEN_LABS_API_KEY")
    
    def predict(self, event_description: str, features: dict, 
                similar_patterns: list) -> dict:
        """
        Generate prediction based on patterns
        """
        print(f"🎯 Generating prediction...")
        
        # Build context from patterns
        patterns_context = "\n".join([
            f"Pattern {p['rank']}: {p['scenario']['event_name']} on "
            f"{p['scenario']['day']} resulted in {p['scenario']['actual_covers']} "
            f"covers (usual: {p['scenario']['usual_covers']}, "
            f"variance: {p['scenario']['variance']}). "
            f"Staffing: {p['scenario']['staffing']}. "
            f"Similarity: {p['similarity_score']:.3f}"
            for p in similar_patterns
        ])
        
        prompt = f"""You are an F&B demand prediction agent.

Event: "{event_description}"
Features: {json.dumps(features)}

Similar past scenarios:
{patterns_context}

Based on these patterns, predict:
1. expected_covers (number)
2. confidence (0-100, integer)
3. recommended_staff (number)
4. key_factors (list of 2-3 factors influencing prediction)

Output ONLY valid JSON, no markdown:
{{
  "expected_covers": <number>,
  "confidence": <0-100>,
  "recommended_staff": <number>,
  "key_factors": ["<factor1>", "<factor2>"]
}}"""

        response = self.mistral.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse prediction
        prediction_text = response.choices[0].message.content
        prediction_text = prediction_text.replace("```json", "").replace("```", "").strip()
        prediction = json.loads(prediction_text)
        
        print(f"   Prediction: {prediction['expected_covers']} covers "
              f"({prediction['confidence']}% confidence)")
        
        return prediction
    
    def generate_voice_output(self, event_description: str, 
                             prediction: dict) -> str:
        """
        Generate voice announcement of prediction
        """
        print(f"🔊 Generating voice output...")
        
        # Create natural language summary
        summary = (
            f"Based on similar patterns, expect {prediction['expected_covers']} "
            f"covers with {prediction['confidence']} percent confidence. "
            f"I recommend scheduling {prediction['recommended_staff']} staff members. "
            f"Key factors are: {', '.join(prediction['key_factors'])}."
        )
        
        # Generate voice
        audio = generate(
            text=summary,
            voice="Adam",
            model="eleven_monolingual_v1"
        )
        
        # Save audio file
        filename = "prediction_voice.mp3"
        save(audio, filename)
        
        print(f"   Voice saved: {filename}")
        print(f"   Text: \"{summary}\"")
        
        return filename

# Test
if __name__ == "__main__":
    from agents.analyzer import AnalyzerAgent
    from agents.pattern_search import PatternSearcher
    
    # Full pipeline test
    event = "Concert tomorrow evening, sunny weather"
    
    analyzer = AnalyzerAgent()
    analysis = analyzer.analyze(event)
    
    searcher = PatternSearcher()
    patterns = searcher.search_similar_patterns(analysis["embedding"])
    
    predictor = PredictorAgent()
    prediction = predictor.predict(event, analysis["features"], patterns)
    voice_file = predictor.generate_voice_output(event, prediction)
    
    print(f"\n✅ Predictor + Voice working!")
    print(f"   Prediction: {prediction}")
    print(f"   Voice file: {voice_file}")


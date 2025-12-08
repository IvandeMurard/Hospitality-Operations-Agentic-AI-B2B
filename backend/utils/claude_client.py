"""
Claude API Client
Handles all interactions with Anthropic's Claude API
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeClient:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please create a .env file with your API key. "
                "See .env.example for reference."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def generate_prediction(self, prompt: str) -> str:
        """
        Generate a prediction using Claude
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def test_connection(self) -> dict:
        """
        Test Claude API connection
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Respond with: Claude API connected successfully"}
                ]
            )
            return {
                "status": "success",
                "message": message.content[0].text,
                "model": self.model
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
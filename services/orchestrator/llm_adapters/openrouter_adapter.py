from typing import List, Dict, Any
from .openai_adapter import OpenAIAdapter
import os

class OpenRouterAdapter(OpenAIAdapter):
    """OpenRouter implementation of the LLM Adapter."""
    
    def __init__(self, model: str = "anthropic/claude-3.5-sonnet", api_key: str = None):
        import openai
        self.client = openai.AsyncOpenAI(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY", "dummy_key"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model

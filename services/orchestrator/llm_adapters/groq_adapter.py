from typing import List, Dict, Any
from .openai_adapter import OpenAIAdapter
import os

class GroqAdapter(OpenAIAdapter):
    """Groq implementation of the LLM Adapter."""
    
    def __init__(self, model: str = "llama3-8b-8192", api_key: str = None):
        import openai
        self.client = openai.AsyncOpenAI(
            api_key=api_key or os.getenv("GROQ_API_KEY", "dummy_key"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model

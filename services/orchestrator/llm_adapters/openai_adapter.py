from typing import List, Dict, Any
from .base import BaseLLMAdapter
import os

class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI implementation of the LLM Adapter."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = None):
        import openai
        self.client = openai.AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    async def generate_response(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        
        # Standardize output
        message = response.choices[0].message
        result = {
            "content": message.content,
            "tool_calls": []
        }
        
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                })
                
        return result

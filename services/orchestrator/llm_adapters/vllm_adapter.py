from typing import List, Dict, Any
from .base import BaseLLMAdapter
import os

class VLLMAdapter(BaseLLMAdapter):
    """Local VLLM implementation of the LLM Adapter (OpenAI Compatible)."""
    
    def __init__(self, model: str = "local-model", api_key: str = "EMPTY", base_url: str = None):
        import openai
        self.client = openai.AsyncOpenAI(
            api_key=api_key or os.getenv("VLLM_API_KEY", "EMPTY"),
            base_url=base_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        )
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
                raw_dispatch = {
                    "tool_name": tc.function.name,
                    "tool_arguments": tc.function.arguments,
                    "agent_id": self.model,
                    "session_id": "unknown"
                }
                try:
                    from schemas.tool_contract import validate_tool_dispatch
                    validated = validate_tool_dispatch(raw_dispatch)
                    result["tool_calls"].append({
                        "id": tc.id,
                        "name": validated.tool_name,
                        "arguments": validated.tool_arguments
                    })
                except Exception as e:
                    result["tool_calls"].append({
                        "id": tc.id,
                        "error": str(e)
                    })
                
        return result

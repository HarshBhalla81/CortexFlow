import os
from typing import List, Dict, Any
from .base import BaseLLMAdapter
from schemas.tool_contract import validate_tool_dispatch

class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic implementation of the LLM Adapter."""
    
    def __init__(self, model: str = "claude-3-haiku-20240307", api_key: str = None):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    async def generate_response(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        # Anthropic expects system prompt separately from messages
        system_prompt = ""
        filtered_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                filtered_messages.append(m)

        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": filtered_messages,
        }
        
        if tools:
            # Convert OpenAI-style tools to Anthropic-style tools
            anthropic_tools = []
            for tool in tools:
                if "function" in tool:
                    anthropic_tools.append({
                        "name": tool["function"]["name"],
                        "description": tool["function"].get("description", ""),
                        "input_schema": tool["function"].get("parameters", {"type": "object", "properties": {}})
                    })
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools

        response = await self.client.messages.create(**kwargs)
        
        # Standardize output
        result = {
            "content": "",
            "tool_calls": []
        }
        
        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                raw_call = {
                    "id": block.id,
                    "name": block.name,
                    "arguments": str(block.input)
                }
                result["tool_calls"].append(raw_call)
                
        return result

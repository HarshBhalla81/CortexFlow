from typing import Optional
from .base import BaseLLMAdapter

class LLMAdapterFactory:
    """Factory to create LLM adapters based on configuration."""
    
    @staticmethod
    def get_adapter(provider_name: str, **kwargs) -> BaseLLMAdapter:
        if provider_name.lower() == "openai":
            from .openai_adapter import OpenAIAdapter
            return OpenAIAdapter(**kwargs)
        # Extend with Anthropic, vLLM, etc.
        raise ValueError(f"Unsupported LLM provider: {provider_name}")

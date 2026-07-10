from typing import Optional
from .base import BaseLLMAdapter

class LLMAdapterFactory:
    """Factory to create LLM adapters based on configuration."""
    
    @staticmethod
    def get_adapter(provider_name: str, **kwargs) -> BaseLLMAdapter:
        provider = provider_name.lower()
        if provider == "openai":
            from .openai_adapter import OpenAIAdapter
            return OpenAIAdapter(**kwargs)
        elif provider == "anthropic":
            from .anthropic_adapter import AnthropicAdapter
            return AnthropicAdapter(**kwargs)
        elif provider == "vllm":
            from .vllm_adapter import VLLMAdapter
            return VLLMAdapter(**kwargs)
        elif provider == "groq":
            from .groq_adapter import GroqAdapter
            return GroqAdapter(**kwargs)
        elif provider == "openrouter":
            from .openrouter_adapter import OpenRouterAdapter
            return OpenRouterAdapter(**kwargs)
            
        raise ValueError(f"Unsupported LLM provider: {provider_name}")

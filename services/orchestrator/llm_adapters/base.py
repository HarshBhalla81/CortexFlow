from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseLLMAdapter(ABC):
    """
    Abstract base class for all LLM providers.
    Ensures provider-agnostic model abstraction.
    """
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generates a response from the LLM given a list of messages and available tools.
        Returns a standardized dictionary containing the response text and any tool calls.
        """
        pass

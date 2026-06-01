from workers.base_worker import BaseWorker

from tools.groq_tool import GroqTool
from tools.openrouter_tool import OpenRouterTool

class LLMWorker(BaseWorker):

    def __init__(self):

        self.groq = GroqTool()
        self.openrouter = OpenRouterTool()

    def execute(self, payload):

        provider = payload.get("provider", "groq")
        messages = payload["messages"]
        
        if provider == "groq":
            response = self.groq.run(messages)

        elif provider == "openrouter":
            response = self.openrouter.run(messages)

        return {
            "response": response
        }
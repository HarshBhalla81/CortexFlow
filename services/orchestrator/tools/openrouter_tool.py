import os
import time

from openai import OpenAI
from tools.base_tool import BaseTool
from shared.metrics import metrics

class OpenRouterTool(BaseTool):

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

    def run(self, messages):

        start = time.time()

        try:

            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324",
                messages=messages
            )

            metrics.record_provider(
                "groq"
            )

            return response.choices[0].message.content

        except Exception:

            metrics.record_provider_failure(
                "groq"
            )

            raise
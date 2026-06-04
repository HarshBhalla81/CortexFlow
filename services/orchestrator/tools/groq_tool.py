import os
import time

from shared.metrics import metrics
from openai import OpenAI
from tools.base_tool import BaseTool

class GroqTool(BaseTool):

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )

    def run(self, messages):

        start = time.time()

        try:

            response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
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
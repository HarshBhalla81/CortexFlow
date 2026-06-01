from openai import OpenAI
from tools.base_tool import BaseTool
import os


class OpenRouterTool(BaseTool):

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

    def run(self, messages):

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324",
            messages=messages
        )

        return response.choices[0].message.content
from openai import OpenAI
from tools.base_tool import BaseTool
import os


class GroqTool(BaseTool):

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )

    def run(self, messages):

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )

        return response.choices[0].message.content
from agents.base_agent import BaseAgent


class SummarizationAgent(BaseAgent):

    def __init__(self, llm_worker):
        self.llm_worker = llm_worker

    def run(self, payload):

        text = payload["text"]

        summary = self.llm_worker.execute(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
                        Summarize the following:

                        {text}
                        """
                    }
                ]
            }
        )
        
        return summary
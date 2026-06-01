from agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):

    def __init__(self, llm_worker):
        self.llm_worker = llm_worker

    def run(self, payload):

        response = payload["response"]

        return self.llm_worker.execute(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
                        Critically review the following response.

                        Identify:
                        1. Weaknesses
                        2. Hallucinations
                        3. Missing information
                        4. Possible improvements

                        Response:
                        {response}
                        """
                    }
                ]
            }
        )
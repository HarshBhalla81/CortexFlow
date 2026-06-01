from agents.base_agent import BaseAgent
print("Loading PlannerAgent")

class PlannerAgent(BaseAgent):

    def __init__(self, llm_worker):
        self.llm_worker = llm_worker

    def run(self, payload):

        task = payload["task"]

        return self.llm_worker.execute(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
                        Create a step-by-step plan
                        for the following task:

                        {task}
                        """
                    }
                ]
            }
        )
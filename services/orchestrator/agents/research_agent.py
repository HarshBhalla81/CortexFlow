from agents.base_agent import BaseAgent

class ResearchAgent(BaseAgent):

    def __init__(
        self,
        retrieval_worker,
        llm_worker
    ):
        self.retrieval = retrieval_worker
        self.llm = llm_worker

    def run(self, task):

        query = task["query"]

        docs = self.retrieval.execute(
            {
                "query": query
            }
        )

        response = self.llm.execute(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
                        Context:
                        {docs}

                        Question:
                        {query}
                        """
                    }
                ]
            }
        )
        
        return response
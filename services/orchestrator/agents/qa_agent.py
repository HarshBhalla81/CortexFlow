from agents.base_agent import BaseAgent
print("Loading QAAgent")

class QAAgent(BaseAgent):

    def __init__(
        self,
        retrieval_worker,
        llm_worker
    ):
        self.retrieval_worker = retrieval_worker
        self.llm_worker = llm_worker

    def run(self, payload):

        question = payload["question"]

        docs = self.retrieval_worker.execute(
            {
                "query": question
            }
        )

        context = "\n".join(
            doc["text"]
            for doc in docs["documents"]
        )

        return self.llm_worker.execute(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
                        Context:
                        {context}

                        Question:
                        {question}
                        """
                    }
                ]
            }
        )
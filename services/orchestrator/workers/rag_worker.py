from workers.base_worker import BaseWorker

from workers.retrieval_worker import RetrievalWorker
from workers.llm_worker import LLMWorker


class RAGWorker(BaseWorker):

    def __init__(self):

        self.retriever = RetrievalWorker()

        self.llm = LLMWorker()

    def execute(self, payload):

        query = payload["query"]

        provider = payload.get(
            "provider",
            "groq"
        )

        k = payload.get(
            "k",
            3
        )

        retrieval_result = self.retriever.execute(
            {
                "query": query,
                "k": k
            }
        )

        documents = retrieval_result[
            "documents"
        ]

        context = "\n\n".join(
            doc["text"]
            for doc in documents
        )

        messages = [
            {
                "role": "system",
                "content":
                """
                Answer only from the supplied context.
                If the answer is not present, say:
                'I could not find that information.'
                """
            },
            {
                "role": "user",
                "content":
                f"""
                Context:
                {context}

                Question:
                {query}
                """
            }
        ]

        llm_result = self.llm.execute(
            {
                "provider": provider,
                "messages": messages
            }
        )

        return {
            "answer": llm_result["response"],
            "documents": documents
        }
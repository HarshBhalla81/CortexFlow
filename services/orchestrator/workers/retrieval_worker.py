from workers.base_worker import BaseWorker
from workers.embedding_worker import EmbeddingWorker

from vectorstore.store import vector_store


class RetrievalWorker(BaseWorker):

    def __init__(self):
        self.embedding_worker = EmbeddingWorker()

    def execute(self, payload):

        query = payload["query"]

        embedding_result = self.embedding_worker.execute(
            {
                "text": query
            }
        )

        documents = vector_store.search(
            embedding_result["embedding"],
            k=payload.get("k", 3)
        )

        return {
            "documents": [
                document.model_dump()
                for document in documents
            ]
        }
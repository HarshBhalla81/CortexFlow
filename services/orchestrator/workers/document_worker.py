from workers.base_worker import BaseWorker
from workers.embedding_worker import EmbeddingWorker

from vectorstore.store import vector_store
from shared.document import Document


class DocumentWorker(BaseWorker):

    def __init__(self):
        self.embedding_worker = EmbeddingWorker()

    def execute(self, payload):

        document = Document(
            id=payload["id"],
            text=payload["text"],
            source=payload.get("source"),
            metadata=payload.get("metadata", {})
        )

        embedding_result = self.embedding_worker.execute(
            {
                "text": document.text
            }
        )

        vector_store.add_document(
            document,
            embedding_result["embedding"]
        )

        return {
            "status": "stored",
            "document_id": document.id
        }
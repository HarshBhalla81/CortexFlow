from workers.base_worker import BaseWorker
from workers.embedding_worker import EmbeddingWorker
from workers.chunking_worker import ChunkingWorker

from vectorstore.store import vector_store
from shared.document import Document


class DocumentWorker(BaseWorker):

    def __init__(self):
        self.chunker = ChunkingWorker()
        self.embedding_worker = EmbeddingWorker()

    def execute(self, payload):

        document = Document(
            id=payload["id"],
            text=payload["text"],
            source=payload.get("source"),
            metadata=payload.get("metadata", {})
        )

        chunk_result = self.chunker.execute(
            {
                "text": document.text
            }
        )

        chunks = chunk_result["chunks"]

        for index, chunk in enumerate(chunks):

            embedding_result = self.embedding_worker.execute(
                {
                    "text": chunk
                }
            )

            chunk_document = Document(
                id=f"{document.id}_chunk_{index}",
                text=chunk,
                source=document.source,
                metadata={
                    **document.metadata,
                    "chunk_index": index,
                    "parent_document": document.id
                }
            )

            vector_store.add_document(
                chunk_document,
                embedding_result["embedding"]
            )

        vector_store.save()
        
        return {
            "status": "stored",
            "document_id": document.id,
            "chunks": len(chunks)
        }
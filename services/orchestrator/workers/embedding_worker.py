from sentence_transformers import SentenceTransformer

from workers.base_worker import BaseWorker


class EmbeddingWorker(BaseWorker):

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def execute(self, payload):

        text = payload["text"]

        embedding = self.model.encode(text)

        return {
            "embedding": embedding.tolist(),
            "dimension": len(embedding)
        }
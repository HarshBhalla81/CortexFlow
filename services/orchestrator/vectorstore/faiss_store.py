import faiss
import numpy as np


class FAISSStore:
    def __init__(self, dimension=384):
        self.dimension = dimension

        
        self.index = faiss.IndexFlatL2(dimension)

        
        self.documents = []

    def add_document(self, document, embedding):
        vector = np.array(
            embedding,
            dtype=np.float32
        ).reshape(1, -1)

        self.index.add(vector)
        self.documents.append(document)

    def search(self, embedding, k=3):
        if self.index.ntotal == 0:
            return []

        vector = np.array(
            embedding,
            dtype=np.float32
        ).reshape(1, -1)

        distances, indices = self.index.search(
            vector,
            min(k, self.index.ntotal)
        )

        results = []

        for idx in indices[0]:
            if idx != -1:
                results.append(self.documents[idx])

        return results
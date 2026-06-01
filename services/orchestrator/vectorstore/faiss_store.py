import os
import pickle

import faiss
import numpy as np

import os
import pickle

import faiss
import numpy as np


class FAISSStore:

    INDEX_PATH = "storage/faiss.index"
    DOCS_PATH = "storage/documents.pkl"

    def __init__(self, dimension=384):

        self.dimension = dimension

        os.makedirs(
            "storage",
            exist_ok=True
        )

        try:

            if (
                os.path.exists(self.INDEX_PATH)
                and
                os.path.exists(self.DOCS_PATH)
            ):

                print(
                    "[FAISSStore] Loading existing index..."
                )

                self.index = faiss.read_index(
                    self.INDEX_PATH
                )

                with open(
                    self.DOCS_PATH,
                    "rb"
                ) as f:

                    self.documents = pickle.load(f)

            else:
                raise FileNotFoundError

        except Exception as e:

            print(
                f"[FAISSStore] Failed to load index: {e}"
            )

            print(
                "[FAISSStore] Creating new index..."
            )

            self.index = faiss.IndexFlatL2(
                self.dimension
            )

            self.documents = []

    def add_document(self, document, embedding):

        vector = np.array(
            embedding,
            dtype=np.float32
        ).reshape(1, -1)

        self.index.add(vector)

        self.documents.append(
            document
        )

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

                results.append(
                    self.documents[idx]
                )

        return results

    def save(self):

        faiss.write_index(
            self.index,
            self.INDEX_PATH
        )

        with open(
            self.DOCS_PATH,
            "wb"
        ) as f:

            pickle.dump(
                self.documents,
                f
            )

        print(
            "[FAISSStore] Saved to disk"
        )
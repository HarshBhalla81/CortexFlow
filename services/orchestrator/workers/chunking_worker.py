from workers.base_worker import BaseWorker


class ChunkingWorker(BaseWorker):

    def execute(self, payload):

        text = payload["text"]

        chunk_size = payload.get(
            "chunk_size",
            500
        )

        overlap = payload.get(
            "overlap",
            100
        )

        chunks = []

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunks.append(
                text[start:end]
            )

            start += (
                chunk_size - overlap
            )

        return {
            "chunks": chunks,
            "count": len(chunks)
        }
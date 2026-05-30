from workers.base_worker import BaseWorker


class EmbeddingWorker(BaseWorker):

    def execute(self, payload):
        print("[EmbeddingWorker] Executing task")

        return {
            "status": "embedding worker reached",
            "received_payload": payload
        }
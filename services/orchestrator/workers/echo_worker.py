from workers.base_worker import BaseWorker

class EchoWorker(BaseWorker):

    def execute(self, payload):
        print("[EchoWorker] Executing task")
        print(payload["message"])
from workers.base_worker import BaseWorker

class UppercaseWorker(BaseWorker):

    def execute(self, payload):
        message = payload.get("message", "")
        return message.upper()
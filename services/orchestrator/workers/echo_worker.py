class EchoWorker:

    def execute(self, payload):
        print("[EchoWorker] Executing task")
        print(payload.get("message"))
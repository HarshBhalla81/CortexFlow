class Executor:

    def run(self, worker, payload):
        return worker.execute(payload)
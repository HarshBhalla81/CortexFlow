from workers.echo_worker import EchoWorker
from registry import AgentRegistry


class Dispatcher:

    def __init__(self):
        self.registry = AgentRegistry()

        self.registry.register(
            "echo",
            EchoWorker()
        )

    def dispatch(self, task_type, payload):

        print(f"[Dispatcher] Routing task: {task_type}")

        worker = self.registry.get(task_type)

        if worker:
            worker.execute(payload)

        else:
            print(f"[Dispatcher] Unknown task type: {task_type}")
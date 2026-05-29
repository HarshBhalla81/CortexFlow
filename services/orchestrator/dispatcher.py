from workers.echo_worker import EchoWorker


class Dispatcher:

    def dispatch(self, task_type, payload):

        print(f"[Dispatcher] Routing task: {task_type}")

        if task_type == "echo":
            worker = EchoWorker()
            worker.execute(payload)

        else:
            print(f"[Dispatcher] Unknown task type: {task_type}")
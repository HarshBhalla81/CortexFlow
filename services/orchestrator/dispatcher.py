from workers.echo_worker import EchoWorker
from workers.uppercase_worker import UppercaseWorker
from executor.executor import Executor
from registry import AgentRegistry
import redis

class Dispatcher:

    def __init__(self):
        self.registry = AgentRegistry()
        self.executor = Executor()

        self.redis = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )
        
        self.registry.register(
            "echo",
            EchoWorker()
        )

        self.registry.register(
            "uppercase",
            UppercaseWorker()
        )

    def dispatch(self, task_type, payload):

        print(f"[Dispatcher] Routing task: {task_type}")

        worker = self.registry.get(task_type)

        task_id = payload.get("task_id")

        if worker:
            try:

                result = self.executor.run(
                    worker,
                    payload
                )

                self.redis.set(
                    f"result:{task_id}",
                    result
                )
                print(f"[Dispatcher] task_id = {task_id}")
                print(f"[Dispatcher] Storing result:{task_id}")
                self.redis.set(
                    f"task:{task_id}:status",
                    "completed"
                )

                print(f"[Dispatcher] Result: {result}")

            except Exception as e:

                self.redis.set(
                    f"task:{task_id}:status",
                    "failed"
                )

                print(f"[Dispatcher] Error: {e}")

        else:
            print(f"[Dispatcher] Unknown task type: {task_type}")
import redis
import time
import json
from shared.models.task import Task
from dispatcher import Dispatcher

r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True,
)

def start_consumer():
    print("Listening on agent_stream...")

    last_id = "0-0"

    dispatcher = Dispatcher()

    while True:
        try:
            messages = r.xread(
                {"agent_stream": last_id},
                block=10000
            )

            if messages:
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        print(f"Received [{message_id}]: {data}")
                        
                        try:
                            task = Task.model_validate(
                                {
                                    "task_id": data.get("task_id"),
                                    "task_type": data.get("task_type"),
                                    "payload": json.loads(data.get("payload"))
                                }
                            )

                        except Exception as e:
                            print(f"[Consumer] Invalid Task: {e}")
                            continue

                        task_type = task.task_type
                        task_id = task.task_id

                        payload = task.payload.copy()

                        payload["task_id"] = task.task_id
                        r.set(
                            f"task:{task_id}:status",
                            "running"
                        )
                        dispatcher.dispatch(task_type, payload)

                        last_id = message_id

        except Exception as e:
            if "Timeout reading from socket" not in str(e):
                print(f"Error: {e}")

        time.sleep(1)
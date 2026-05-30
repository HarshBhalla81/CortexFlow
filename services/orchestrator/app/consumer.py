import redis
import time
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
                        
                        task_type = data.get("task_type")
                        task_id = data.get("task_id")

                        payload = {
                            "task_id": data.get("task_id"),
                            "message": data.get("message")
                        }
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
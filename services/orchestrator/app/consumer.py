import redis
import time
import json
import logging

from shared.models.task import Task
from dispatcher import Dispatcher

r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3 # can be changed as per the requirement

def start_consumer():
    logger.info("Listening on agent_stream...")

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
                        logger.info(
                            f"Received task message_id={message_id} task_type={data.get('task_type')}"
                        )
                                                
                        try:
                            task = Task.model_validate(
                                {
                                    "task_id": data.get("task_id"),
                                    "task_type": data.get("task_type"),
                                    "payload": json.loads(data.get("payload"))
                                }
                            )
                            logger.info(
                                f"Validated task_id={task.task_id} task_type={task.task_type}"
                            )

                        except Exception as e:
                            logger.exception("Invalid task received")
                            continue

                        task_type = task.task_type
                        task_id = task.task_id

                        payload = task.payload.copy()
                        payload.setdefault("retry_count", 0)

                        payload["task_id"] = task.task_id
                        r.set(
                            f"task:{task_id}:status",
                            "running"
                        )
                        try:

                            dispatcher.dispatch(
                                task_type,
                                payload
                            )

                            logger.info(
                                f"Completed dispatch task_id={task_id}"
                            )


                        except Exception:

                            retries = payload.get(
                                "retry_count",
                                0
                            )

                            logger.exception(
                                f"Dispatch failed task_id={task_id} retry={retries}"
                            )

                            if retries < MAX_RETRIES:

                                payload["retry_count"] = retries + 1
                                logger.info(
                                    f"Requeueing task_id={task_id} retry={retries + 1}"
                                )

                                r.xadd(
                                    "agent_stream",
                                    {
                                        "task_id": task_id,
                                        "task_type": task_type,
                                        "payload": json.dumps(payload)
                                    }
                                )
                            else:
                                logger.error(
                                    f"Max retries exceeded for task_id={task_id}"
                                )
                                r.xadd(
                                    "dead_letter_stream",
                                    {
                                        "task_id": task_id,
                                        "task_type": task_type,
                                        "payload": json.dumps(payload)
                                    }
                                )
                                r.set(
                                    f"task:{task_id}:status",
                                    "failed"
                                )
                        finally:
                            last_id = message_id

        except Exception as e:
            if "Timeout reading from socket" not in str(e):
                logger.exception("Consumer loop error")

        time.sleep(1)
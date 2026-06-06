import redis
import json
import uuid
import time


class EventPublisher:

    def __init__(self):

        self.redis = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )

        self.stream_name = "events_stream"

    def publish(
        self,
        event_type,
        task_id,
        source,
        metadata=None
    ):

        if metadata is None:
            metadata = {}

        event = {
            "event_id": str(uuid.uuid4()),
            "task_id": task_id,
            "event_type": event_type.value,
            "source": source,
            "timestamp": str(time.time()),
            "metadata": json.dumps(metadata)
        }

        self.redis.xadd(
            self.stream_name,
            event
        )


event_publisher = EventPublisher()
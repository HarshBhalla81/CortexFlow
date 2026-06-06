from enum import Enum

class EventTypes(str , Enum):

    TASK_RECEIVED = "task_received"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"

    WORKER_STARTED = "worker_started"
    WORKER_COMPLETED = "worker_completed"

    RETRY_TRIGGERED = "retry_triggered"

    ALERT_CREATED = "alert_created"
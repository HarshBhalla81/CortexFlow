from dataclasses import dataclass

@dataclass
class EventFeatures:

    failure_rate: float
    retry_rate: float
    avg_latency: float
    ttft: float
    tool_success_rate: float
    queue_depth: int
    throughput: float
    active_tasks: int
    agent_failure_rate: float
    worker_failure_rate: float
import time
from collections import deque
from watchdog.models import EventFeatures
from statistics import mean

class FeatureExtractor:
    def __init__(self):
        self.events_window = deque(maxlen=500)
        self.latencies = deque(maxlen=500)
        self.ttft_list = deque(maxlen=500)
        
        self.task_start_times = {}
        self.ttft_tracked_tasks = set()
        
        self.failure_count = 0
        self.retry_count = 0
        self.completed_count = 0
        self.tool_attempt_count = 0
        
        self.active_tasks = set()

    def ingest(self, event):
        self.events_window.append(event)

        event_type = event.get("event_type")
        task_id = event.get("task_id")

        if event_type == "TASK_STARTED":
            self.task_start_times[task_id] = time.time()
            self.active_tasks.add(task_id)

        elif event_type == "TASK_COMPLETED":
            self.completed_count += 1
            if task_id in self.task_start_times:
                latency = time.time() - self.task_start_times[task_id]
                self.latencies.append(latency)
                del self.task_start_times[task_id]
            self.active_tasks.discard(task_id)
            self.ttft_tracked_tasks.discard(task_id)

        elif event_type == "TASK_FAILED":
            self.failure_count += 1
            self.active_tasks.discard(task_id)
            self.ttft_tracked_tasks.discard(task_id)
        
        elif event_type == "RETRY_TRIGGERED":
            self.retry_count += 1
            
        elif event_type in ("model_thought", "tool_call"):
            if event_type == "tool_call":
                self.tool_attempt_count += 1
                
            # Track TTFT on the first response event
            if task_id in self.task_start_times and task_id not in self.ttft_tracked_tasks:
                ttft = time.time() - self.task_start_times[task_id]
                self.ttft_list.append(ttft)
                self.ttft_tracked_tasks.add(task_id)

    def build_feature_vector(self):
        total_events = max(len(self.events_window), 1)
        failure_rate = self.failure_count / total_events
        retry_rate = self.retry_count / total_events
        
        avg_latency = mean(self.latencies) if self.latencies else 0.0
        avg_ttft = mean(self.ttft_list) if self.ttft_list else 0.0
        
        throughput = self.completed_count / total_events
        
        # Proxy for tool success rate: (completed tasks) / (tool attempts or 1)
        # Cap at 1.0
        tool_success_rate = min(1.0, self.completed_count / max(self.tool_attempt_count, 1))

        return EventFeatures(
            failure_rate=failure_rate,
            retry_rate=retry_rate,
            avg_latency=avg_latency,
            ttft=avg_ttft,
            tool_success_rate=tool_success_rate,
            queue_depth=0,
            throughput=throughput,
            active_tasks=len(self.active_tasks),
            agent_failure_rate=failure_rate,
            worker_failure_rate=failure_rate
        )
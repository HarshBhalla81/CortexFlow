import time
import uuid
import redis
import os

class SyntheticTelemetryGenerator:

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            decode_responses=True
        )
    
    def publish(self, event_type, task_id, component):
        self.redis.xadd(
            "events_stream",
            {
                "event_type": event_type,
                "task_id": task_id,
                "component": component
            }
        )
    
    def normal_workflow(self):
        task_id = str(uuid.uuid4())
        self.publish(
            "AGENT_COMPLETED",
            task_id,
            "PlannerAgent"
        )
        self.publish(
            "AGENT_COMPLETED",
            task_id,
            "ResearchAgent"
        )
        
        self.publish(
            "AGENT_COMPLETED",
            task_id,
            "CriticAgent"
        )

        self.publish(
            "AGENT_COMPLETED",
            task_id,
            "SummarizationAgent"
        )
    
    def reasoning_loop(self):
        task_id = str(uuid.uuid4())

        sequence = [
            "PlannerAgent",
            "ResearchAgent",
            "CriticAgent",
            "PlannerAgent"
        ]

        for component in sequence:

            self.publish(
                "AGENT_COMPLETED",
                task_id,
                component
            )

    def failure_storm(self):
        task_id = str(uuid.uuid4())

        for _ in range(50):

            self.redis.xadd(
                "events_stream",
                {
                    "event_type":
                        "TASK_FAILED",
                    "task_id":
                        task_id,
                    "component":
                        "ResearchAgent"
                }
            )

    def latency_spike(self):
        task_id = str(uuid.uuid4())

        self.publish(
            "TASK_STARTED",
            task_id,
            "ResearchAgent"
        )
        time.sleep(10)

        self.publish(
            "TASK_COMPLETED",
            task_id,
            "ResearchAgent"
        )

if __name__ == "__main__":
    generator = SyntheticTelemetryGenerator()
    generator.normal_workflow()
    generator.reasoning_loop()
    generator.failure_storm()
    generator.latency_spike()
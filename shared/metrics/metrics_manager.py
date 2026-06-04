import redis
import time

from collections import defaultdict
from threading import Lock


class MetricsManager:

    def __init__(self):
        self.lock = Lock()

        self.tasks_processed = 0
        self.tasks_failed = 0

        self.worker_counts = defaultdict(int)
        self.agent_counts = defaultdict(int)

        self.latencies = []

        self.redis = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )

    def record_task(self):
        self.redis.incr("metrics:tasks_processed")

    def record_failure(self):
        self.redis.incr("metrics:tasks_failed")

    def record_worker(self, worker_name):

        self.redis.hincrby(
            "metrics:workers",
            worker_name,
            1
        )

    def record_agent(self, agent_name):

        self.redis.hincrby(
            "metrics:agents",
            agent_name,
            1
        )

    def record_latency(self, latency):

        self.redis.incrbyfloat(
            "metrics:latency_total",
            latency
        )

        self.redis.incr(
            "metrics:latency_count"
        )
    
    def record_worker_latency(
        self,
        worker_name,
        latency
    ):

        self.redis.hincrbyfloat(
            "metrics:worker_latency_total",
            worker_name,
            latency
        )

        self.redis.hincrby(
            "metrics:worker_latency_count",
            worker_name,
            1
        )


    def record_agent_latency(
        self,
        agent_name,
        latency
    ):

        self.redis.hincrbyfloat(
            "metrics:agent_latency_total",
            agent_name,
            latency
        )

        self.redis.hincrby(
            "metrics:agent_latency_count",
            agent_name,
            1
        )

    def record_worker_failure(
    self,
    worker_name
    ):

        self.redis.hincrby(
            "metrics:worker_failures",
            worker_name,
            1
        )

    def record_agent_failure(
    self,
    agent_name
    ):

        self.redis.hincrby(
            "metrics:agent_failures",
            agent_name,
            1
        )
    def record_throughput(self):

        current_minute = int(
            time.time() // 60
        )

        self.redis.hincrby(
            "metrics:throughput",
            str(current_minute),
            1
        )

    def record_provider(
    self,
    provider
    ):

        self.redis.hincrby(
            "metrics:provider_usage",
            provider,
            1
        )
    def get_metrics(self):

        processed = int(
            self.redis.get(
                "metrics:tasks_processed"
            ) or 0
        )

        failed = int(
            self.redis.get(
                "metrics:tasks_failed"
            ) or 0
        )

        total_latency = float(
            self.redis.get(
                "metrics:latency_total"
            ) or 0
        )

        latency_count = int(
            self.redis.get(
                "metrics:latency_count"
            ) or 0
        )

        avg_latency = (
            total_latency / latency_count
            if latency_count
            else 0
        )

        worker_latency_total = self.redis.hgetall(
            "metrics:worker_latency_total"
        )

        worker_latency_count = self.redis.hgetall(
            "metrics:worker_latency_count"
        )

        agent_latency_total = self.redis.hgetall(
            "metrics:agent_latency_total"
        )

        agent_latency_count = self.redis.hgetall(
            "metrics:agent_latency_count"
        )

        worker_failures = self.redis.hgetall(
            "metrics:worker_failures"
        )

        agent_failures = self.redis.hgetall(
            "metrics:agent_failures"
        )
        worker_latency = {}

        for worker in worker_latency_total:

            total = float(
                worker_latency_total[worker]
            )

            count = int(
                worker_latency_count.get(
                    worker,
                    1
                )
            )

            worker_latency[worker] = (
                total / count
            )

        agent_latency = {}

        for agent in agent_latency_total:

            total = float(
                agent_latency_total[agent]
            )

            count = int(
                agent_latency_count.get(
                    agent,
                    1
                )
            )

            agent_latency[agent] = (
                total / count
            )

        worker_failure_rate = {}
        for worker, count in self.redis.hgetall(
            "metrics:workers"
        ).items():

            executions = int(count)

            failures = int(
                worker_failures.get(
                    worker,
                    0
                )
            )

            worker_failure_rate[
                worker
            ] = round(
                failures
                / executions
                * 100,
                2
            )
        
        agent_failure_rate = {}
        for agent, count in self.redis.hgetall(
            "metrics:agents"
        ).items():

            executions = int(count)

            failures = int(
                agent_failures.get(
                    agent,
                    0
                )
            )

            agent_failure_rate[
                agent
            ] = round(
                failures
                / executions
                * 100,
                2
            )
        worker_counts = self.redis.hgetall(
                            "metrics:workers"
                        )
        agent_counts = self.redis.hgetall(
                            "metrics:agents"
                        )
        queue_depth = self.redis.xlen(
            "agent_stream"
        )
        throughput_data = self.redis.hgetall(
            "metrics:throughput"
        )
        current_minute = str(
            int(time.time() // 60)
        )

        tasks_per_minute = int(
            throughput_data.get(
                current_minute,
                0
            )
        )
        return {
            "tasks_processed": processed,
            "tasks_failed": failed,
            "worker_latency": worker_latency,
            "agent_latency": agent_latency,
            "average_latency": avg_latency,
            "worker_failures": worker_failures,
            "agent_failures": agent_failures,
            "worker_failure_rate": worker_failure_rate,
            "agent_failure_rate": agent_failure_rate,
            "queue_depth": queue_depth,
            "worker_counts": worker_counts,
            "agent_counts": agent_counts,
            "tasks_per_minute": tasks_per_minute
        }
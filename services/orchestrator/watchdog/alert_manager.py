import redis

from datetime import datetime

class AlertManager:

    def __init__(self, redis_client):

        self.redis = redis_client

    def publish_alert(self, lert_type, message, severity="MEDIUM", metadata=None):
        if metadata is None:

            metadata = {}
        
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "metadata": str(metadata)
        }
        self.redis.xadd(
            "alerts_stream",
            alert
        )
    
    def reasoning_loop(self, task_id):
        self.publish_alert(
            alert_type="REASONING_LOOP",
            severity="HIGH",
            message=f"Reasoning loop detected in task {task_id}",
            metadata={
                "task_id": task_id
            }
        )

    def anomaly(self, score):
        self.publish_alert(
            alert_type="ANOMALY",
            severity="MEDIUM",
            message=f"Anomalous system behaviour detected",
            metadata={
                "score": score
            }
        )
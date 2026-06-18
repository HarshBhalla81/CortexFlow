import json
from datetime import datetime
import httpx

class AlertManager:

    def __init__(self, redis_client=None):
        self.gateway_url = "http://gateway:8000/process"

    def publish_alert(self, alert_type, message, severity="MEDIUM", metadata=None):
        if metadata is None:
            metadata = {}
        
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "metadata": metadata
        }
        print(f"[WATCHDOG ALERT] {alert}")
        
        # Optionally forward to gateway if needed
        try:
            httpx.post(self.gateway_url, json={
                "task_id": "watchdog",
                "task_type": "anomaly_alert",
                "payload": alert
            })
        except:
            pass
    
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
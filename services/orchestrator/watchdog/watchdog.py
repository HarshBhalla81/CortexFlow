import redis

from watchdog.feature_extractor import FeatureExtractor
from watchdog.graph_analyzer import GraphAnalyzer
from watchdog.anomaly_detector import AnomalyDetector
from watchdog.alert_manager import AlertManager

class BDHWatchdog:

    def __init__(self, redis_client):
        self.redis = redis_client
        self.feature_extractor = FeatureExtractor()
        self.graph_analyzer = GraphAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager(
            redis_client
        )
        self.last_id = "0"

    def process_event(self, event):
        # process the even and converting the event into a multi-dimensional vector
        # check for anomaly through isolation forest
        self.feature_extractor.ingest(event)
        self.graph_analyzer.ingest(event)
        features = (self.feature_extractor.build_feature_vector())
        print(
            f"[WATCHDOG] Features: "
            f"{features}"
        )
        self.anomaly_detector.update(features)

        #cycle detection
        task_id = event.get("task_id")

        if (task_id and self.graph_analyzer.detect_cycle(task_id)):
            self.alert_manager.reasoning_loop(task_id)
            
        result = (self.anomaly_detector.score(features))  

        if result["is_anomaly"]: 
            print(f"[DEBUG] result={result}")
            self.alert_manager.anomaly(result["score"])

    def run(self):
        while True:
            messages = self.redis.xread(
                {
                    "events_stream":
                    self.last_id
                },
                block=1000
            )
            if not messages:
                continue

            for _, events in messages:

                for message_id, data in events:

                    self.last_id = message_id
                    self.process_event(data)
                    print(
                        f"[WATCHDOG] Event Received: "
                        f"{data}"
                    )

            
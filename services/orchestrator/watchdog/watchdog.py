import asyncio
import os
from watchdog.feature_extractor import FeatureExtractor
from watchdog.graph_analyzer import GraphAnalyzer
from watchdog.anomaly_detector import AnomalyDetector
from watchdog.alert_manager import AlertManager


class BDHWatchdog:

    def __init__(self, redis_client=None):
        self.feature_extractor = FeatureExtractor()
        self.graph_analyzer = GraphAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager()
        self.last_id = "0"
        self.events_processed = 0

    def process_event(self, event):
        """Process a single event through the full watchdog pipeline."""
        self.events_processed += 1

        # 1. Feature extraction: build multi-dimensional vector
        self.feature_extractor.ingest(event)
        self.graph_analyzer.ingest(event)
        features = self.feature_extractor.build_feature_vector()

        print(
            f"[WATCHDOG] Event #{self.events_processed} | "
            f"type={event.get('event_type')} | "
            f"task={event.get('task_id')} | "
            f"Features: fail={features.failure_rate:.3f} "
            f"retry={features.retry_rate:.3f} "
            f"latency={features.avg_latency:.3f} "
            f"throughput={features.throughput:.3f}"
        )

        # 2. Update the Isolation Forest model
        self.anomaly_detector.update(features)

        # 3. Cycle detection via DFS on directed task graph
        task_id = event.get("task_id")
        if task_id and self.graph_analyzer.detect_cycle(task_id):
            print(f"[WATCHDOG] ⚠️ REASONING LOOP detected for task: {task_id}")
            self.alert_manager.reasoning_loop(task_id)

        # 4. Anomaly scoring via Isolation Forest
        result = self.anomaly_detector.score(features)
        if result["is_anomaly"]:
            print(f"[WATCHDOG] 🚨 ANOMALY DETECTED | score={result['score']:.4f}")
            self.alert_manager.anomaly(result["score"])

        # 5. Log training progress
        buf_size, min_samples = self.anomaly_detector.training_progress()
        if not self.anomaly_detector.is_trained:
            print(f"[WATCHDOG] Training progress: {buf_size}/{min_samples} samples")

    async def run_csv(self, filepath="/app/data/tool_events_watchdog.csv"):
        """Asynchronously tail the Pathway CSV output and feed events to the watchdog pipeline."""
        last_pos = 0
        print(f"[WATCHDOG] Starting async CSV watcher on: {filepath}")

        while True:
            if not os.path.exists(filepath):
                await asyncio.sleep(1)
                continue

            try:
                with open(filepath, 'r') as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    last_pos = f.tell()

                    if not lines:
                        await asyncio.sleep(0.5)  # Faster polling for responsiveness
                        continue

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Parse CSV: session_id, task_id, event_type, payload, timestamp
                        parts = line.split(',')
                        if len(parts) >= 5 and parts[0] != "session_id":  # skip header
                            event = {
                                "session_id": parts[0],
                                "task_id": parts[1],
                                "event_type": parts[2],
                                "payload": parts[3],
                                "timestamp": parts[4]
                            }
                            self.process_event(event)

                    # Yield control to event loop after processing a batch
                    await asyncio.sleep(0)

            except Exception as e:
                print(f"[WATCHDOG] Error reading CSV: {e}")
                await asyncio.sleep(2)

    def run(self):
        """Legacy sync entry point — wraps the async runner."""
        asyncio.run(self.run_csv())
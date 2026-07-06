import asyncio
import os
import json
from watchdog.feature_extractor import FeatureExtractor
from watchdog.graph_analyzer import GraphAnalyzer
from watchdog.anomaly_detector import AnomalyDetector
from watchdog.alert_manager import AlertManager
from watchdog.semantic_analyzer import SemanticAnalyzer


class BDHWatchdog:

    def __init__(self, redis_client=None):
        self.feature_extractor = FeatureExtractor()
        self.graph_analyzer = GraphAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager()
        self.semantic_analyzer = SemanticAnalyzer()
        self.last_id = "0"
        self.events_processed = 0

    def process_event(self, event):
        """Process a single event through the full ML watchdog pipeline."""
        self.events_processed += 1
        
        task_id = event.get("task_id")
        event_type = event.get("event_type")
        payload_str = event.get("payload", "{}")

        # Parse JSON payload carefully since it comes from CSV
        try:
            payload = json.loads(payload_str)
            if isinstance(payload, str):
                payload = json.loads(payload)
        except Exception:
            payload = {}

        # 1. Feature extraction: build multi-dimensional vector
        self.feature_extractor.ingest(event)
        self.graph_analyzer.ingest(event)
        features = self.feature_extractor.build_feature_vector()

        if self.events_processed % 50 == 0:
            print(
                f"[WATCHDOG] Event #{self.events_processed} | "
                f"Features: fail={features.failure_rate:.3f} "
                f"lat={features.avg_latency:.3f} "
                f"ttft={features.ttft:.3f} "
                f"success={features.tool_success_rate:.3f}"
            )

        # 2. Update the Isolation Forest model (now with rolling scaling)
        self.anomaly_detector.update(features)

        # 3. Probabilistic Markov Transition detection
        if task_id and self.graph_analyzer.detect_abnormal_transition(task_id):
            print(f"[WATCHDOG] ⚠️ BEHAVIORAL DRIFT detected for task: {task_id}")
            self.alert_manager.publish_alert(
                alert_type="BEHAVIORAL_DRIFT",
                severity="HIGH",
                message=f"Low probability state transition detected in task {task_id}",
                metadata={"task_id": task_id}
            )

        # 4. Semantic Loop & Exact Tool Repetition Sniffing
        if task_id:
            if event_type == "tool_call":
                tool_name = payload.get("tool_name", "unknown")
                arguments = payload.get("arguments", {})
                if self.semantic_analyzer.ingest_tool(task_id, tool_name, arguments):
                    print(f"[WATCHDOG] 🛑 INTERVENTION ALERT: Tool {tool_name} looping endlessly in task {task_id}")
                    self.alert_manager.publish_alert(
                        alert_type="INTERVENTION_ALERT",
                        severity="CRITICAL",
                        message=f"Repeated identical tool call {tool_name} without progress",
                        metadata={"task_id": task_id, "tool_name": tool_name}
                    )
            elif event_type == "model_thought":
                thought = payload.get("thought", "")
                if thought and self.semantic_analyzer.ingest_thought(task_id, thought):
                    print(f"[WATCHDOG] ⚠️ SEMANTIC LOOP detected in task: {task_id}")
                    self.alert_manager.publish_alert(
                        alert_type="SEMANTIC_LOOP",
                        severity="HIGH",
                        message=f"Agent is hallucinating / stuck in a semantic loop",
                        metadata={"task_id": task_id}
                    )
            elif event_type == "TASK_COMPLETED":
                # Clean up memory
                self.semantic_analyzer.clear_session(task_id)
                self.graph_analyzer.clear_task(task_id)

        # 5. Anomaly scoring via Isolation Forest
        result = self.anomaly_detector.score(features)
        if result["is_anomaly"]:
            print(f"[WATCHDOG] 🚨 ANOMALY DETECTED | score={result['score']:.4f}")
            self.alert_manager.anomaly(result["score"])

        # 6. Log training progress
        buf_size, min_samples = self.anomaly_detector.training_progress()
        if not self.anomaly_detector.is_trained and self.events_processed % 5 == 0:
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
                            # In case payload has commas inside, we should ideally use csv module,
                            # but simple split is used historically. Let's merge parts[3:-1] as payload if needed.
                            # The original codebase uses parts[3] as payload.
                            # Wait, the original code had: payload = parts[3]
                            # Let's fix that slightly in case of CSV escaping:
                            # Actually let's stick to original parsing to avoid breaking existing stress testers unless necessary.
                            event = {
                                "session_id": parts[0],
                                "task_id": parts[1],
                                "event_type": parts[2],
                                "payload": parts[3] if len(parts) == 5 else ",".join(parts[3:-1]),
                                "timestamp": parts[-1]
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
from sklearn.ensemble import IsolationForest
from collections import deque
import numpy as np

class AnomalyDetector:

    def __init__(self):

        self.model = IsolationForest(
            contamination=0.05,
            random_state=42
        )
        self.training_buffer = deque(maxlen=1000)
        self.samples_seen = 0
        self.min_training_samples = 20
        self.is_trained = False

    def features_to_vector(self, features):
        return [
            features.failure_rate,
            features.retry_rate,
            features.avg_latency,
            features.queue_depth,
            features.throughput,
            features.active_tasks,
            features.agent_failure_rate,
            features.worker_failure_rate
        ]
    
    def update(self, features):
        print(
            f"[ANOMALY] "
            f"buffer={len(self.training_buffer)} "
            f"trained={self.is_trained}"
        )
        self.samples_seen += 1
        vector = self.features_to_vector(
            features
        )

        self.training_buffer.append(
            vector
        )

        if (not self.is_trained and len(self.training_buffer) >= self.min_training_samples):
            self.model.fit(
                np.array(
                    self.training_buffer
                )
            )

            self.is_trained = True
            print(
                "[ANOMALY] Model trained successfully"
            )
        elif (self.is_trained and self.samples_seen % 100 == 0):
            self.model.fit(
                np.array(
                    self.training_buffer
                )
            )

    def score(self, features):
        if not self.is_trained:

            return {
                "is_anomaly": False,
                "score": 0.0
            }
        vector = np.array([
            self.features_to_vector(
                features
            )
        ])

        prediction = self.model.predict(
            vector
        )[0]

        score = self.model.decision_function(
            vector
        )[0]

        return {
            "is_anomaly": prediction == -1,
            "score": float(score)
        }
    def training_progress(self):
        return (
            len(self.training_buffer),
            self.min_training_samples
        )
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import deque
import numpy as np

class AnomalyDetector:

    def __init__(self):

        self.model = IsolationForest(
            contamination=0.05,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.training_buffer = deque(maxlen=1000)
        self.samples_seen = 0
        self.min_training_samples = 20
        self.is_trained = False

    def features_to_vector(self, features):
        return [
            features.failure_rate,
            features.retry_rate,
            features.avg_latency,
            features.ttft,
            features.tool_success_rate,
            features.queue_depth,
            features.throughput,
            features.active_tasks,
            features.agent_failure_rate,
            features.worker_failure_rate
        ]
    
    def update(self, features):
        self.samples_seen += 1
        vector = self.features_to_vector(features)
        self.training_buffer.append(vector)

        if (not self.is_trained and len(self.training_buffer) >= self.min_training_samples):
            X = np.array(self.training_buffer)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)

            self.is_trained = True
            print("[ANOMALY] Model trained successfully with scaled features")
            
        elif (self.is_trained and self.samples_seen % 100 == 0):
            X = np.array(self.training_buffer)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)

    def score(self, features):
        if not self.is_trained:
            return {
                "is_anomaly": False,
                "score": 0.0
            }
            
        vector = np.array([self.features_to_vector(features)])
        
        # Scale the incoming vector using the fitted scaler
        try:
            vector_scaled = self.scaler.transform(vector)
        except Exception:
            vector_scaled = vector
            
        prediction = self.model.predict(vector_scaled)[0]
        score = self.model.decision_function(vector_scaled)[0]

        return {
            "is_anomaly": prediction == -1,
            "score": float(score)
        }
        
    def training_progress(self):
        return (
            len(self.training_buffer),
            self.min_training_samples
        )
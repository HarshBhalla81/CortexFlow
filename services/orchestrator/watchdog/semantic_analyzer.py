import hashlib
import json
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer

class SemanticAnalyzer:
    def __init__(self):
        # We use all-MiniLM-L6-v2 which is already cached in the Docker image
        print("[WATCHDOG] Loading SentenceTransformer for semantic sniffing...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("[WATCHDOG] SentenceTransformer loaded.")
        
        # Track tool calls: session_id -> list of parameter hashes
        self.tool_history = defaultdict(list)
        
        # Track thoughts: session_id -> list of embeddings
        self.thought_embeddings = defaultdict(list)
        
        self.semantic_loop_threshold = 0.95
        
    def ingest_tool(self, session_id: str, tool_name: str, arguments: dict) -> bool:
        """
        Tracks exact tool calls. Returns True if the identical tool & args 
        have been called 3 times sequentially without progress.
        """
        # Canonicalize the arguments for consistent hashing
        args_str = json.dumps(arguments, sort_keys=True)
        combo_str = f"{tool_name}::{args_str}"
        call_hash = hashlib.sha256(combo_str.encode()).hexdigest()
        
        history = self.tool_history[session_id]
        history.append(call_hash)
        
        # Keep only the last 3 for exact repetition check
        if len(history) > 3:
            history.pop(0)
            
        if len(history) == 3 and history[0] == history[1] == history[2]:
            return True
            
        return False

    def ingest_thought(self, session_id: str, thought_text: str) -> bool:
        """
        Encodes the thought text and checks cosine similarity against recent thoughts.
        Returns True if similarity > threshold for the last 3 consecutive thoughts (indicating a reasoning loop).
        """
        # Generate dense embedding
        emb = self.model.encode(thought_text)
        
        history = self.thought_embeddings[session_id]
        history.append(emb)
        
        if len(history) > 3:
            history.pop(0)
            
        if len(history) == 3:
            # Check cosine similarity
            emb0 = history[0]
            emb1 = history[1]
            emb2 = history[2]
            
            # Helper to calculate cos sim
            def cos_sim(v1, v2):
                norm = np.linalg.norm(v1) * np.linalg.norm(v2)
                if norm == 0:
                    return 0
                return np.dot(v1, v2) / norm

            sim01 = cos_sim(emb0, emb1)
            sim12 = cos_sim(emb1, emb2)
            
            if sim01 > self.semantic_loop_threshold and sim12 > self.semantic_loop_threshold:
                return True
                
        return False

    def clear_session(self, session_id: str):
        self.tool_history.pop(session_id, None)
        self.thought_embeddings.pop(session_id, None)

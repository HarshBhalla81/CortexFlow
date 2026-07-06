from collections import defaultdict

class GraphAnalyzer:
    def __init__(self):
        # Global transition counts: transition_counts[from_node][to_node]
        self.transition_counts = defaultdict(lambda: defaultdict(int))
        self.state_totals = defaultdict(int)
        
        # Last component seen for each task
        self.last_component = {}
        self.task_paths = defaultdict(list)
        
        # Minimal historical samples before flagging low-probability transitions
        self.min_samples = 3

    def ingest(self, event):
        task_id = event.get("task_id")
        component = event.get("component") or event.get("event_type")

        if not task_id or not component:
            return

        self.task_paths[task_id].append(component)

        if task_id not in self.last_component:
            self.last_component[task_id] = component
            return

        previous = self.last_component[task_id]

        # Increment Markov transitions globally
        self.transition_counts[previous][component] += 1
        self.state_totals[previous] += 1
        
        self.last_component[task_id] = component

    def get_transition_probability(self, from_node, to_node):
        total = self.state_totals.get(from_node, 0)
        if total == 0:
            return 1.0  # unknown, assume valid
        return self.transition_counts[from_node][to_node] / total

    def detect_abnormal_transition(self, task_id):
        """
        Replaces rigid cycle detection. Returns True if the latest transition 
        is statistically abnormal (probability < 0.05) indicating behavioral drift.
        """
        path = self.task_paths.get(task_id, [])
        if len(path) < 2:
            return False
            
        previous = path[-2]
        current = path[-1]
        
        # Only evaluate if we have enough historical data for the 'previous' state
        if self.state_totals.get(previous, 0) >= self.min_samples:
            prob = self.get_transition_probability(previous, current)
            if prob < 0.05:
                return True
                
        return False

    def clear_task(self, task_id):
        self.task_paths.pop(task_id, None)
        self.last_component.pop(task_id, None)

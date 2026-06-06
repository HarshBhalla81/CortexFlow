# watchdog/graph_analyzer.py

from collections import defaultdict
# to detect cycles i will be treating a sequence of events as a graph where 
# each worker/agent in the event denotes a node in the graph
# since we this forms a directed graph we can use dfs to find cycles in the graph
# for directed graph we use a stack to detect a cycle in the same recurscive path

class GraphAnalyzer:

    def __init__(self):
        """
        task_graphs:
        {
            task_id: {
                node: [neighbors]
            }
        }

        Example:
        {
            "task_1": {
                "PlannerAgent": ["ResearchAgent"],
                "ResearchAgent": ["CriticAgent"],
                "CriticAgent": ["PlannerAgent"]
            }
        }
        """
        self.task_graphs = defaultdict(
            lambda: defaultdict(list)
        )

        """
        Stores last component seen for each task.

        Used to build edges:

        Planner -> Research
        Research -> Critic
        """
        self.last_component = {}

        """
        Useful for debugging and future visualization.
        """
        self.task_paths = defaultdict(list)

    def ingest(self, event):
        """
        Consumes an event from events_stream.

        Expected fields:
        {
            "task_id": "...",
            "component": "...",
            ...
        }
        """
        def ingest(self, event):

            event_type = event.get("event_type")

            if event_type not in (
                "AGENT_COMPLETED",
                "WORKER_COMPLETED"
            ):
                return
        task_id = event.get("task_id")
        component = event.get("component")

        if not task_id or not component:
            return

        self.task_paths[task_id].append(component)

        # first node for this task
        if task_id not in self.last_component:
            self.last_component[task_id] = component
            return

        previous = self.last_component[task_id]

        # add directed edge
        if component not in self.task_graphs[task_id][previous]:
            self.task_graphs[task_id][previous].append(
                component
            )

        self.last_component[task_id] = component

    def detect_cycle(self, task_id):
        """
        Detect reasoning loops using DFS.

        Returns:
            True  -> cycle exists
            False -> no cycle
        """

        graph = self.task_graphs.get(task_id)

        if not graph:
            return False

        visited = set()
        recursion_stack = set()

        def dfs(node):

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in graph.get(node, []):

                if neighbor not in visited:

                    if dfs(neighbor):
                        return True

                elif neighbor in recursion_stack:
                    return True

            recursion_stack.remove(node)

            return False

        for node in graph:

            if node not in visited:

                if dfs(node):
                    return True

        return False

    def get_graph(self, task_id):
        """
        Returns graph for debugging.
        """

        return dict(
            self.task_graphs.get(task_id, {})
        )

    def get_path(self, task_id):
        """
        Returns execution path.

        Example:
        [
            PlannerAgent,
            ResearchAgent,
            CriticAgent
        ]
        """

        return self.task_paths.get(task_id, [])

    def clear_task(self, task_id):
        """
        Cleanup after task completion.
        """

        self.task_graphs.pop(task_id, None)
        self.task_paths.pop(task_id, None)
        self.last_component.pop(task_id, None)


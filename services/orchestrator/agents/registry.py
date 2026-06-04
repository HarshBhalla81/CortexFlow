class AgentRegistry:

    def __init__(self):
        self.agents = {}

    def register(self, name, agent):
        self.agents[name] = agent

    def get(self, name):
        return self.agents.get(name)

    def exists(self, name):
        return name in self.agents
    def contains(self, task_type):
        return task_type in self.agents
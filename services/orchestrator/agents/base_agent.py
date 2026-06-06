from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run(self, task):
        pass
from abc import ABC, abstractmethod

class BaseWorker(ABC):

    @abstractmethod
    def execute(self, payload):
        pass
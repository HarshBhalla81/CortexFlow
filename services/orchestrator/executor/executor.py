from events.event_publisher import event_publisher
from events.event_types import EventTypes

class Executor:

    def run(
        self,
        component,
        payload,
        task_id,
        task_type
    ):

        if hasattr(component, "execute"):
            event_publisher.publish(
                EventTypes.WORKER_STARTED,
                task_id,
                source="executor",
                metadata={
                    "worker": component.__class__.__name__,
                    "task_type": task_type
                }
            )
            result = component.execute(payload)

            event_publisher.publish(
                EventTypes.WORKER_COMPLETED,
                task_id,
                source="executor",
                metadata={
                    "worker": component.__class__.__name__,
                    "task_type": task_type
                }
            )

            return result

        if hasattr(component, "run"):
            event_publisher.publish(
                EventTypes.AGENT_STARTED,
                task_id,
                source=self.__class__.__name__,
                metadata={
                    "agent": component.__class__.__name__
                }
            )
            result = component.run(payload)

            event_publisher.publish(
                EventTypes.AGENT_COMPLETED,
                task_id,
                source=self.__class__.__name__,
                metadata={
                    "agent": component.__class__.__name__
                }
            )

            return result

        raise ValueError(
            "Unsupported component"
        )
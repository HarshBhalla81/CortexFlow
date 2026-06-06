import redis
import json
import time

import logging
logger = logging.getLogger(__name__)
# adding all workers
from workers.registry import WorkerRegistry

from workers.echo_worker import EchoWorker
from workers.uppercase_worker import UppercaseWorker
from workers.embedding_worker import EmbeddingWorker
from workers.document_worker import DocumentWorker
from workers.retrieval_worker import RetrievalWorker
from workers.llm_worker import LLMWorker
from workers.pdf_worker import PDFWorker
from workers.rag_worker import RAGWorker
from workers.chunking_worker import ChunkingWorker

# adding all agents
from agents.registry import AgentRegistry

from agents.research_agent import ResearchAgent
from agents.qa_agent import QAAgent
from agents.planner_agent import PlannerAgent
from agents.critic_agent import CriticAgent
from agents.summarization_agent import SummarizationAgent

# adding import statement for multiagent worker
from agents.workflow_agent import WorkflowAgent
from executor.executor import Executor

# for evaluatinng peformance of workers, agenst, and multi-agents
from shared.metrics import metrics #metrics is an instnce of metrics_manager class

# to publish events in redis stream
from events.event_publisher import event_publisher
from events.event_types import EventTypes

class Dispatcher:

    def __init__(self):

        self.worker_registry = WorkerRegistry()
        self.agent_registry = AgentRegistry()
        self.executor = Executor()
        #self.event_publisher = EventPublisher()
        self.redis = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )


        workers = {
            "echo": EchoWorker(),
            "uppercase": UppercaseWorker(),
            "embedding": EmbeddingWorker(),
            "document": DocumentWorker(),
            "retrieve": RetrievalWorker(),
            "llm": LLMWorker(),
            "rag": RAGWorker(),
            "chunk": ChunkingWorker(),
            "pdf": PDFWorker()
        }

        for name, worker in workers.items():

            self.worker_registry.register(
                name,
                worker
            )

        retrieval_worker = self.worker_registry.get(
            "retrieve"
        )

        llm_worker = self.worker_registry.get(
            "llm"
        )


        agents = {
            "research": ResearchAgent(
                retrieval_worker,
                llm_worker
            ),

            "qa": QAAgent(
                retrieval_worker,
                llm_worker
            ),

            "planner": PlannerAgent(
                llm_worker
            ),

            "critic": CriticAgent(
                llm_worker
            ),

            "summary": SummarizationAgent(
                llm_worker
            )
        }

        for name, agent in agents.items():

            self.agent_registry.register(
                name,
                agent
            )
        
        planner_agent = self.agent_registry.get(
            "planner"
        )

        research_agent = self.agent_registry.get(
            "research"
        )

        summary_agent = self.agent_registry.get(
            "summary"
        )

        critic_agent = self.agent_registry.get(
            "critic"
        )

        self.agent_registry.register(
            "workflow",
            WorkflowAgent(
                planner_agent,
                research_agent,
                summary_agent,
                critic_agent
            )
        )

    def dispatch(self, task_type, payload):
        
        worker = self.worker_registry.get(
        task_type
        )

        agent = self.agent_registry.get(
            task_type
        )

        task_id = payload.get(
            "task_id"
        )

        component = worker or agent

        component_type = None

        if self.worker_registry.contains(task_type):
            component_type = "worker"
            metrics.record_worker(task_type)

        elif self.agent_registry.contains(task_type):
            component_type = "agent"
            metrics.record_agent(task_type)
        
        logger.info(
            f"Resolved {task_type} to {component_type}"
        )

        if component:
            start_time = time.time()
            try:
                event_publisher.publish(
                    EventTypes.TASK_STARTED,
                    task_id,
                    source="dispatcher",
                    metadata={
                        "task_type": task_type
                    }
                )
                result = self.executor.run(
                    component,
                    payload,
                    task_id,
                    task_type
                )

                logger.info(
                    f"Executing task_id={task_id} task_type={task_type}"
                )

                logger.info(
                    f"Storing result for task_id={task_id}"
                )

                self.redis.set(
                    f"result:{task_id}",
                    json.dumps(result)
                )

                self.redis.set(
                    f"task:{task_id}:status",
                    "completed"
                )
                
                # printing the whole result is not required now for agents instear we can print a few lines for debugging
                # print(
                #     f"[Dispatcher] Result: {result}"
                # )
                logger.info(
                    f"Task completed task_id={task_id}"
                )
                logger.debug(
                    f"Result preview: {str(result)[:200]}"
                )
                metrics.record_task()
                metrics.record_throughput()
                event_publisher.publish(
                    EventTypes.TASK_COMPLETED,
                    task_id,
                    source="dispatcher",
                    metadata={
                        "task_type": task_type
                    }
                )
            except Exception as e:
                
                metrics.record_failure()

                if component_type == "worker":

                    metrics.record_worker_failure(
                        task_type
                    )

                elif component_type == "agent":

                    metrics.record_agent_failure(
                        task_type
                    )
                logger.exception(
                    f"Task failed task_id={task_id} task_type={task_type}"
                )
                self.redis.set(
                    f"task:{task_id}:status",
                    "failed"
                )
                event_publisher.publish(
                    EventTypes.TASK_FAILED,
                    task_id,
                    source="dispatcher",
                    metadata={
                        "task_type": task_type,
                        "error": str(e)
                    }
                )
                raise
            finally:
                latency = time.time() - start_time
                metrics.record_latency(latency)

                if component_type == "worker":

                    metrics.record_worker_latency(
                        task_type,
                        latency
                    )

                elif component_type == "agent":

                    metrics.record_agent_latency(
                        task_type,
                        latency
                    )
                logger.info(
                    f"Task latency task_id={task_id}: {latency:.3f}s"
                )
        else:
            metrics.record_failure()
            logger.error(
                f"Unknown task type: {task_type}"
            )
import redis
import json

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

class Dispatcher:

    def __init__(self):

        self.worker_registry = WorkerRegistry()
        self.agent_registry = AgentRegistry()
        self.executor = Executor()

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

        if component:

            try:

                result = self.executor.run(
                    component,
                    payload
                )

                print(
                    f"[Dispatcher] task_id = {task_id}"
                )

                print(
                    f"[Dispatcher] Storing result:{task_id}"
                )

                self.redis.set(
                    f"result:{task_id}",
                    json.dumps(result)
                )

                self.redis.set(
                    f"task:{task_id}:status",
                    "completed"
                )

                print(
                    f"[Dispatcher] Result: {result}"
                )

            except Exception as e:

                self.redis.set(
                    f"task:{task_id}:status",
                    "failed"
                )

                print(
                    f"[Dispatcher] Error: {e}"
                )

        else:

            print(
                f"[Dispatcher] Unknown task type: {task_type}"
            )
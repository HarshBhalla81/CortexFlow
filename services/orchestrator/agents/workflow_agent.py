import logging
logger = logging.getLogger(__name__)

from agents.base_agent import BaseAgent


class WorkflowAgent(BaseAgent):

    def __init__(
        self,
        planner_agent,
        research_agent,
        summary_agent,
        critic_agent
    ):
        self.planner = planner_agent
        self.research = research_agent
        self.summary = summary_agent
        self.critic = critic_agent

    def run(self, payload):

        query = payload["query"]
        logger.info(f"Workflow started query='{query}'")

        logger.info("[Workflow] Planning")

        plan = self.planner.run(
            {
                "task": query
            }
        )

        logger.info("[Workflow] Researching")

        research = self.research.run(
            {
                "query": query
            }
        )

        logger.info("[Workflow] Summarizing")

        summary = self.summary.run(
            {
                "text": research["response"]
            }
        )

        logger.info("[Workflow] Critiquing")

        critique = self.critic.run(
            {
                "response": summary["response"]
            }
        )
        
        logger.info("Workflow completed successfully")
        
        workflow = {
            "plan": plan,
            "research": research,
            "summary": summary,
            "critique": critique
        }


        return workflow
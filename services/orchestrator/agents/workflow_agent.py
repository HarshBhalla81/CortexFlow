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

        print("[Workflow] Planning")

        plan = self.planner.run(
            {
                "task": query
            }
        )

        print("[Workflow] Researching")

        research = self.research.run(
            {
                "query": query
            }
        )

        print("[Workflow] Summarizing")

        summary = self.summary.run(
            {
                "text": research["response"]
            }
        )

        print("[Workflow] Critiquing")

        critique = self.critic.run(
            {
                "response": summary["response"]
            }
        )

        return {
            "plan": plan,
            "research": research,
            "summary": summary,
            "critique": critique
        }
from loguru import logger
from pydantic import ConfigDict

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import Event, build_event
from sherpa_ai.memory import Belief
from sherpa_ai.policies import ReactPolicy
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate


class AgentFeedbackPolicy(ReactPolicy):
    """
    Select the best next action based on the feedback from an agent
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    prompt_template: PromptTemplate = PromptTemplate("./sherpa_ai/prompts/prompts.json")
    # Prompt used to generate question to the user
    agent: BaseAgent

    def select_action(self, belief: Belief, **kwargs):
        actions = belief.actions

        task = belief.current_task.content
        context = belief.get_context(self.llm.get_num_tokens)
        options = "\n".join(
            [f"{i+1}. {action.name}" for i, action in enumerate(actions)]
        )
     
        variables = {
            "task": task,
            "context": context,
            "options": options
        }
        agent_feedback_prompt = self.prompt_template.format_prompt(
            wrapper="agent_feedback_description_prompt",
            name= "AGENT_FEEDBACK_DESCRIPTION_PROMPT",
            version="1.0",
            variables=variables
        )
        result = self.llm.invoke(agent_feedback_prompt)
        question = result.content if hasattr(result, 'content') else str(result)
        logger.info(f"Question to the user: {question}")
        self.agent.shared_memory.add("task", name="Agent", content=question)
        result = self.agent.run()

        belief.update(build_event("user_input", "Agent", content=result))
        return super().select_action(belief, **kwargs)

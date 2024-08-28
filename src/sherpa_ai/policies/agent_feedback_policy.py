from loguru import logger

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory import Belief
from sherpa_ai.policies import ReactPolicy

AGENT_FEEDBACK_DESCRIPTION = """You are an intelligent assistant helping the user to complete their task. You have the following task to complete:
{task}

Context of you work is as follows:
{context}

You have the following options to continue completing the this task:

{options}

Use polite and engaging language, and ask the user what they want you to help them next. Not need to greet and keep it short and concise. 

If you think the context is not enough to choose an action. Ask the user for more information.
"""


class AgentFeedbackPolicy(ReactPolicy):
    """
    Select the best next action based on the feedback from an agent
    """

    class Config:
        arbitrary_types_allowed = True

    # Prompt used to generate question to the user
    agent_feedback_description: str = AGENT_FEEDBACK_DESCRIPTION
    agent: BaseAgent

    def select_action(self, belief: Belief, **kwargs):
        actions = belief.actions

        task = belief.current_task.content
        context = belief.get_context(self.llm.get_num_tokens)
        options = "\n".join(
            [f"{i+1}. {action.name}" for i, action in enumerate(actions)]
        )

        agent_feedback_prompt = self.agent_feedback_description.format(
            task=task, context=context, options=options
        )
        question = self.llm.predict(agent_feedback_prompt)
        logger.info(f"Question to the user: {question}")
        self.agent.shared_memory.add_event(Event(EventType.task, "Agent", question))
        result = self.agent.run()

        belief.update(Event(EventType.user_input, "Agent", result))
        return super().select_action(belief, **kwargs)

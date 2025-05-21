"""Agent feedback-based policy module for Sherpa AI.

This module provides a policy implementation that selects actions based on
feedback from an agent. It defines the AgentFeedbackPolicy class which
generates questions for agents and uses their responses to guide action selection.
"""

import asyncio

from loguru import logger
from pydantic import ConfigDict

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import Event, build_event
from sherpa_ai.memory import Belief
from sherpa_ai.policies import ReactPolicy
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate


class AgentFeedbackPolicy(ReactPolicy):
    """Policy for selecting actions based on agent feedback.

    This class extends ReactPolicy to incorporate feedback from an agent
    in the action selection process. It generates questions about possible
    actions, gets responses from the agent, and uses those responses to
    guide action selection.

    Attributes:
        prompt_template (PromptTemplate): Template for generating questions.
        agent (BaseAgent): Agent to provide feedback on actions.
        model_config (ConfigDict): Configuration allowing arbitrary types.

    Example:
        >>> agent = UserAgent()  # Agent that can provide feedback
        >>> policy = AgentFeedbackPolicy(agent=agent)
        >>> output = policy.select_action(belief)
        >>> print(output.action.name)
        'SearchAction'
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    prompt_template: PromptTemplate = PromptTemplate("./sherpa_ai/prompts/prompts.json")
    # Prompt used to generate question to the user
    agent: BaseAgent

    async def async_select_action(self, belief: Belief, **kwargs):
        """Select action based on agent feedback.

        This method generates a question about possible actions, gets feedback
        from the agent, and uses that feedback to select the next action.

        Args:
            belief (Belief): Current belief state containing available actions.
            **kwargs: Additional arguments for action selection.

        Returns:
            PolicyOutput: Selected action and arguments based on feedback.

        Example:
            >>> policy = AgentFeedbackPolicy(agent=user_agent)
            >>> belief.actions = [SearchAction(), AnalyzeAction()]
            >>> output = policy.select_action(belief)
            >>> print(output.action.name)  # Based on agent feedback
            'SearchAction'
        """
        actions = belief.actions

        task = belief.current_task.content
        context = belief.get_context(self.llm.get_num_tokens)
        options = "\n".join(
            [f"{i+1}. {action.name}" for i, action in enumerate(actions)]
        )

        variables = {"task": task, "context": context, "options": options}
        agent_feedback_prompt = self.prompt_template.format_prompt(
            prompt_parent_id="agent_feedback_description_prompt",
            prompt_id="AGENT_FEEDBACK_DESCRIPTION_PROMPT",
            version="1.0",
            variables=variables,
        )
        result = self.llm.invoke(agent_feedback_prompt)
        question = result.content if hasattr(result, "content") else str(result)
        logger.info(f"Question to the user: {question}")

        await self.agent.shared_memory.async_add("task", name="Agent", content=question)
        result = self.agent.run()

        belief.update(build_event("user_input", "Agent", content=result))
        return super().select_action(belief, **kwargs)

    def select_action(self, belief: Belief, **kwargs):
        """Select action based on agent feedback.

        This method generates a question about possible actions, gets feedback
        from the agent, and uses that feedback to select the next action.

        Args:
            belief (Belief): Current belief state containing available actions.
            **kwargs: Additional arguments for action selection.

        Returns:
            PolicyOutput: Selected action and arguments based on feedback.
        """
        return asyncio.run(self.async_select_action(belief, **kwargs))

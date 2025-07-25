import json
from transitions.extensions.asyncio import AsyncMachine
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.models.sherpa_base_chat_model import SherpaBaseChatModel
from sherpa_ai.actions.synthesize import SynthesizeOutput

class McpAgent(BaseAgent):
    """
    A general-purpose agent for executing MCP server actions within the Sherpa framework.

    This agent is designed to integrate with tools exposed by external MCP servers (such as GitHub, Linear, Notion, etc.) and provides a unified interface for executing these tools as actions. It manages the available actions, maintains internal belief state, and supports state machine-based execution.

    Attributes:
        name (str): The name of the agent.
        description (str): Description of the agent's purpose and capabilities.
        llm (BaseLanguageModel): The language model used by the agent and actions.
        actions (List[AsyncBaseAction]): List of available MCP actions.
        action_map (dict): Mapping from action name to action instance for fast lookup.
        belief (Belief): The agent's internal state and knowledge.
        state_machine (SherpaStateMachine): State machine for managing execution state.

    Example:
        >>> agent = McpAgent(llm, actions)
        >>> result = await agent.run("list_pull_requests", owner="repo_owner", repo="repo_name")
        >>> print(result)

    Methods:
        run(action_name: str, **kwargs): Execute a single action by name with the provided arguments.
        synthesize_output(): Generate a synthesized output based on the agent's belief state.
    """
    name: str = "MCP Agent"
    description: str = "A general agent for executing MCP server actions."

    def __init__(self, llm: SherpaBaseChatModel, actions: list = [], **kwargs):
        super().__init__(llm=llm, actions=actions, **kwargs)
        if self.belief is None:
            self.belief = Belief()
        self.state_machine = SherpaStateMachine(
            name="mcp_agent",
            states=["start"],
            initial="start",
            sm_cls=AsyncMachine,
        )
        self.llm = llm
        for action in actions:
            self.add_action(action)
        self.action_map = {a.name: a for a in actions}

    def add_action(self, action):
        self.state_machine.update_transition(
            trigger=action.name, source="start", dest="start", action=action
        )

    def create_actions(self):
        return self.actions

    async def run(self, action_name: str, **kwargs):
        """
        Execute a single action by name with the provided arguments.
        """
        action = self.action_map.get(action_name)
        if not action:
            return f"Unknown action: {action_name}"
        try:
            result = await action.execute(**kwargs)
            self.belief.update_internal("action_result", self.name, content=result)
            return result
        except Exception as e:
            return f"Error executing action {action_name}: {e}"

    def synthesize_output(self) -> str:
        """Generate the final answer based on the agent's actions and belief state."""
        synthesize_action = SynthesizeOutput(
            role_description=self.description,
            llm=self.llm
        )
        result = synthesize_action.execute(
            self.belief.current_task.content if self.belief.current_task else "",
            self.belief.get_context(self.llm.get_num_tokens) if self.llm else "",
            self.belief.get_internal_history(self.llm.get_num_tokens) if self.llm else "",
        )
        return result 
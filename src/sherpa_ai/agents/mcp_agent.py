import json

from transitions.extensions.asyncio import AsyncMachine

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.models.sherpa_base_chat_model import SherpaBaseChatModel


class McpAgent(BaseAgent):
    name: str = "MCP Agent"
    description: str = (
        "An agent that uses a state machine to interact with GitHub and Linear."
    )

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

    def add_action(self, action):
        self.state_machine.update_transition(
            trigger=action.name, source="start", dest="start", action=action
        )

    def create_actions(self):
        return self.actions

    def synthesize_output(self) -> str:
        if self.belief and self.belief.get_last_event():
            return self.belief.get_last_event().content
        return "No action was executed."

    async def run(self, prompt: str) -> str:
        actions = self.actions

        default_args = {
            "owner": "Eyobyb",
            "repo": "scrape_Jsonify",
        }

        actions_description = "\n".join([str(a) for a in actions])

        prompt_template = f"""
        Given the user's prompt, choose the best action to execute.
        Respond with a JSON object containing the "action" name and the "args" for that action.

        Available actions:
        {actions_description}

        Prompt: {prompt}

        JSON Response:
        """
        response = await self.llm.ainvoke(prompt_template)

        try:
            response_json = json.loads(response.content.strip())
            action_name = response_json.get("action")
            action_args = response_json.get("args", {})
            action_args.pop("owner", None)
            action_args.pop("repo", None)
            for k, v in default_args.items():
                action_args[k] = v
        except json.JSONDecodeError:
            return f"Error: Invalid JSON response from LLM: {response.content}"

        action_to_execute = None
        for action in actions:
            if action.name == action_name:
                action_to_execute = action
                break

        if action_to_execute:
            try:
                result = await action_to_execute.execute(**action_args)
                self.belief.update_internal("action_result", self.name, content=result)
                return str(result)
            except Exception as e:
                return f"Error executing action {action_name}: {e}"
        else:
            return f"Unknown action: {action_name}" 
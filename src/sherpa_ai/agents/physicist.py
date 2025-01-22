from typing import List

from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies import ReactPolicy

class Physicist(BaseAgent):
    """
    The physicist agent answers questions or research about physics-related topics
    """


    name: str = "Physicist"
    description: str = None
    num_runs: int = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        template = self.prompt_template
        action_planner = template.format_prompt(
            wrapper="physicist_prompts",
            name="ACTION_PLAN_DESCRIPTION",
            version="1.0",
        )
        self.description = template.format_prompt(
            wrapper="physicist_prompts",
            name="PHYSICIST_DESCRIPTION",
            version="1.0",
    )

        if self.belief is None:
            self.belief = Belief()

        if self.policy is None:
            self.policy = ReactPolicy(
                role_description=self.description,
                output_instruction=action_planner,
                llm=self.llm,
            )

    def create_actions(self) -> List[BaseAction]:
        return [
            Deliberation(role_description=self.description, llm=self.llm),
            GoogleSearch(
                role_description=self.description,
                task=self.belief.current_task.content,
                llm=self.llm,
            ),
        ]

    def synthesize_output(self) -> str:
        synthesize_action = SynthesizeOutput(
            role_description=self.description, llm=self.llm
        )
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )

        return result

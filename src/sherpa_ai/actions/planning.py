from langchain.llms.base import LLM

from sherpa_ai.actions.base import BaseAction


class ActionPlanner(BaseAction):
    def __init__(self, llm: LLM):
        self.llm = llm

        # TODO: define the prompt for planning, it take one arg (task,
        #  agent_pool_description)
        self.prompt = None

    def execute(self, task: str, agent_pool_description: str):
        """
        Execute the action
        """
        action_output = self.llm(self.prompt.format(task, agent_pool_description))

        return self.post_process(action_output)

    def post_process(self, action_output: str) -> str:
        """
        Post process the action output
        """
        raise NotImplementedError

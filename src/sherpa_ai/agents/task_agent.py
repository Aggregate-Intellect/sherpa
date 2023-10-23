import json
from typing import List
from loguru import logger
from pydantic import ValidationError

from langchain.schema import (
    AIMessage,
    BaseMessage,
    Document,
    HumanMessage,
    SystemMessage,
)
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.critic import Critic
from sherpa_ai.agents.ml_engineer import MLEngineer
from sherpa_ai.agents.physicist import Physicist
from sherpa_ai.agents.user import UserAgent

from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.agents.planner import Planner
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.orchestrator import Orchestrator, OrchestratorConfig
from sherpa_ai.events import EventType
from sherpa_ai.output_parser import BaseTaskOutputParser, TaskOutputParser
from sherpa_ai.reflection import Reflection

from langchain.base_language import BaseLanguageModel
from langchain.tools.base import BaseTool

from sherpa_ai.action_planner import SelectiveActionPlanner
from sherpa_ai.output_parsers import LinkParser

TASK_AGENT_DESRIPTION = """ You are a **task management assistant** who solves user questions and offers a detailed solution.
"""

OBJECTIVE_PROMPT = """ Use tools and resource to respond to the user's message and solve any questions the user may have.
"""

class TaskAgent(BaseAgent):
    """
    The task agent is the agent handles a single task.
    """
    def __init__(
            self, 
            llm: BaseLanguageModel,
            tools: List[BaseTool],
            output_parser: BaseTaskOutputParser,
            name: str = "Task Agent", 
            description: str = TASK_AGENT_DESRIPTION, 
            shared_memory=None, 
            belief=None,
            num_runs=3,
            previous_messages=None,
        ):
            self.name = name
            self.description = description
            self.shared_memory = shared_memory
            self.belif = belief
            self.num_runs = num_runs
            self.loop_count = 0
            self.tools = tools
            self.llm = llm
            self.previous_messages = previous_messages
            self.action_planner = SelectiveActionPlanner(
                self.llm, tools, ai_name=name, ai_role=TASK_AGENT_DESRIPTION
            )
            self.output_parser = output_parser or TaskOutputParser()
            link_parser = LinkParser()
            self.tool_output_parsers = [link_parser]

    
    """
    This function takes a task from user, organized agents to generate a solution for the user
    """
    def run(self, task: str) -> str:
        reflection = Reflection(self.llm, self.tools, [])
        loop_count = self.loop_count
        if loop_count >= self.num_runs:
            user_input = (
                        "Use the above information to solve the task for the user:"
                        f"\n{task}\n\n"
                        "If you use any resource, then create inline citation by adding "
                        " of the reference document at the end of the sentence in the format "
                        "of 'Sentence [DocID]'\n"
                        "Example:\n"
                        "Sentence1 [1]. Sentence2. Sentence3 [2].\n"
                        "Only use the reference document. DO NOT use any links"
                        " DO NOT include citation if the resource is not"
                        "necessary. only write text but not the JSON format specified "
                        "above. \nResult:"
                    )
            assistant_reply = self.action_planner.select_action(
                    self.previous_messages, self.shared_memory, task=task, user_input=user_input
                )
            result = ""
            if loop_count >= self.num_runs:
                try:
                    result = json.loads(assistant_reply)
                    if (
                        "command" in result
                        and "args" in result["command"]
                        and "response" in result["command"]["args"]
                    ):
                        result = result["command"]["args"]["response"]
                except json.JSONDecodeError:
                    result = assistant_reply

                for output_parser in self.output_parser:
                    result = output_parser.parse_output(result)
                return result
            
            action = self.output_parser.parse(assistant_reply)
            tools = {t.name: t for t in self.tools}
            new_reply = reflection.evaluate_action(
                action, assistant_reply, task, self.previous_messages
            )
            action = self.output_parser.parse(new_reply)
            if action.name == "finish":
                self.loop_count = self.num_runs
                result = "Finished task. "
            elif action.name in tools:
                tool = tools[action.name]

                if tool.name == "UserInput":
                    return action.args["query"]

                try:
                    observation = tool.run(action.args)

                    for tool_output_parser in self.tool_output_parsers:
                        observation = tool_output_parser.parse_output(
                            observation, tool_output=True
                        )
                except ValidationError as e:
                    observation = (
                        f"Validation Error in args: {str(e)}, args: {action.args}"
                    )
                except Exception as e:
                    observation = (
                        f"Error: {str(e)}, {type(e).__name__}, args: {action.args}"
                    )
                result = f"Command {tool.name} returned: {observation}"
            elif action.name == "ERROR":
                result = f"Error: {action.args}. "
            else:
                result = (
                    f"Unknown command '{action.name}'. "
                    f"Please refer to the 'COMMANDS' list for available "
                    f"commands and only respond in the specified JSON format."
                )

            self.loop_count += 1

            memory_to_add = (
                f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "
            )

            self.previous_messages.append(HumanMessage(content=memory_to_add))




         
         
        










          
        
        
    

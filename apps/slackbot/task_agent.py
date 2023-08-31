import json
from os import environ
from typing import List, Optional

import openai
from langchain.chains.llm import LLMChain
from langchain.chat_models.base import BaseChatModel
from langchain.llms.base import BaseLLM
from langchain.schema import (
    AIMessage,
    BaseMessage,
    Document,
    HumanMessage,
    SystemMessage,
)
from langchain.tools.base import BaseTool
from langchain.tools.human.tool import HumanInputRun
from langchain.vectorstores.base import VectorStoreRetriever
from loguru import logger
from pydantic import ValidationError

from action_planner import SelectiveActionPlanner
from action_planner.base import BaseActionPlanner
from output_parser import BaseTaskOutputParser, TaskOutputParser
from output_parsers import LinkParser, MDToSlackParse
from post_processors import md_link_to_slack
from reflection import Reflection
from verbose_loggers import DummyVerboseLogger
from verbose_loggers.base import BaseVerboseLogger
from utils import show_commands_only

class TaskAgent:
    """Agent class for handling a single task"""

    def __init__(
        self,
        ai_name: str,
        ai_id: str,
        memory: VectorStoreRetriever,
        llm: BaseLLM,
        action_planner: BaseActionPlanner,
        output_parser: BaseTaskOutputParser,
        tools: List[BaseTool],
        previous_messages: List[dict],
        verbose_logger: BaseVerboseLogger,
        feedback_tool: Optional[HumanInputRun] = None,
        max_iterations: int = 5,
    ):
        self.ai_name = ai_name
        self.memory = memory
        # self.full_message_history: List[BaseMessage] = []
        self.next_action_count = 0
        self.llm = llm
        self.output_parser = output_parser
        self.tools = tools
        self.verbose_logger = verbose_logger

        self.action_planner = action_planner
        self.feedback_tool = feedback_tool
        self.max_iterations = max_iterations
        self.loop_count = 0
        self.ai_id = ai_id
        self.previous_message = self.process_chat_history(previous_messages)
        self.logger = []  # added by JF

        link_parser = LinkParser()
        slack_link_paerser = MDToSlackParse()

        self.tool_output_parsers = [link_parser]
        self.output_parsers = [link_parser, slack_link_paerser]
        # print(self.full_message_history)
        # print("message:", self.previous_message)

    @classmethod
    def from_llm_and_tools(
        cls,
        ai_name: str,
        ai_role: str,
        ai_id: str,
        memory: VectorStoreRetriever,
        tools: List[BaseTool],
        llm: BaseChatModel,
        previous_messages,
        action_planner: BaseActionPlanner = None,
        human_in_the_loop: bool = False,
        output_parser: Optional[BaseTaskOutputParser] = None,
        max_iterations: int = 5,
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
    ):
        if action_planner is None:
            action_planner = SelectiveActionPlanner(
                llm, tools, ai_name=ai_name, ai_role=ai_role
            )
        human_feedback_tool = HumanInputRun() if human_in_the_loop else None

        return cls(
            ai_name,
            ai_id,
            memory,
            llm,
            action_planner,
            output_parser or TaskOutputParser(),
            tools,
            previous_messages,
            verbose_logger,
            feedback_tool=human_feedback_tool,
            max_iterations=max_iterations,
        )

    def run(self, task: str) -> str:
        user_input = (
            "Determine which next command to use. "
            "and respond using the JSON format specified above without any extra text."
            "\n JSON Response: \n"
        )

        # Interaction Loop
        self.verbose_logger.log(f"⏳{self.ai_name} is thinking...")
        logger.info(f"⏳{self.ai_name} is thinking...")

        reflection = Reflection(self.llm, self.tools, [])
        while True:
            # Discontinue if continuous limit is reached
            loop_count = self.loop_count
            logger_step = {"Step": f"{loop_count}/{self.max_iterations}"}  

            if loop_count >= self.max_iterations:
                user_input = (
                    "Use the above information to respond to the user's message:"
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

            # Send message to AI, get response
            assistant_reply = self.action_planner.select_action(
                self.previous_message, self.memory, task=task, user_input=user_input
            )

            logger.info(f"reply: {assistant_reply}")
            # added by JF
            try:
                reply_json = json.loads(assistant_reply)
                logger_step["reply"] = reply_json
            except json.JSONDecodeError:
                logger_step["reply"] = assistant_reply  # last reply is a string
            self.logger.append(logger_step)
            
            ########## Serial Verbose Feature #######
            try:
                formatted_logger_step = show_commands_only(logger_step)
            except Exception as e:
                logger.error(e)
                formatted_logger_step = logger_step
            
            logger.info(f"```{formatted_logger_step}```")
            self.verbose_logger.log(f"```{formatted_logger_step}```")  
            #######################################

            # return assistant_reply
            # return if maximum itertation limit is reached
            result = ""
            if loop_count >= self.max_iterations:
                # TODO: this should be handled better, e.g. message for each task
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

                for output_parser in self.output_parsers:
                    result = output_parser.parse_output(result)

                return result

            # Get command name and arguments
            action = self.output_parser.parse(assistant_reply)
            logger.debug("action:", action)
            tools = {t.name: t for t in self.tools}
            new_reply = reflection.evaluate_action(
                action, assistant_reply, task, self.previous_message
            )
            action = self.output_parser.parse(new_reply)
            logger.debug("action after reflection: ", action)

            if action.name == "finish":
                self.loop_count = self.max_iterations
                result = "Finished task. "
            elif action.name in tools:
                tool = tools[action.name]

                if tool.name == "UserInput":
                    return {"type": "user_input", "query": action.args["query"]}

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
            if self.feedback_tool is not None:
                feedback = f"\n{self.feedback_tool.run('Input: ')}"
                if feedback in {"q", "stop"}:
                    logger.info("EXITING")
                    return "EXITING"
                memory_to_add += feedback

            self.previous_message.append(HumanMessage(content=memory_to_add))

    def set_user_input(self, user_input: str):
        result = f"Command UserInput returned: {user_input}"
        assistant_reply = self.logger.get_full_messages()[-1].content
        memory_to_add = f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "

        self.memory.add_documents([Document(page_content=memory_to_add)])

    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        results = []

        for message in messages:
            logger.info(message)
            if message["type"] != "message" and message["type"] != "text":
                continue

            message_cls = AIMessage if message["user"] == self.ai_id else HumanMessage
            # replace the at in the message with the name of the bot
            text = message["text"].replace(f"@{self.ai_id}", f"@{self.ai_name}")
            # added by JF
            text = text.split("#verbose", 1)[0]  # remove everything after #verbose
            text = text.replace("-verbose", "")  # remove -verbose if it exists
            results.append(message_cls(content=text))

        return results

    def process_output(self, output: str) -> str:
        """
        Process the output of the AI to remove the bot's name and replace it with @bot
        """
        for processor in self.output_processors:
            output = processor(output)
        return output

import json
from loguru import logger
from os import environ
from typing import List, Optional
import config as cfg

import openai
from langchain.chains.llm import LLMChain
from langchain.chat_models.base import BaseChatModel
from langchain.llms.base import BaseLLM
from langchain.schema import AIMessage, BaseMessage, Document, HumanMessage
from langchain.tools.base import BaseTool
from langchain.tools.human.tool import HumanInputRun
from langchain.vectorstores.base import VectorStoreRetriever
from pydantic import ValidationError

from action_planner import SelectiveActionPlanner
from action_planner.base import BaseActionPlanner
from output_parser import BaseTaskOutputParser, TaskOutputParser
from post_processors import md_link_to_slack


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
        previous_messages,
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

        self.action_planner = action_planner
        self.feedback_tool = feedback_tool
        self.max_iterations = max_iterations
        self.loop_count = 0
        self.ai_id = ai_id
        self.previous_message = self.process_chat_history(previous_messages)
        self.command_log = []  
        self.previous_action = ""

        self.output_processors = [md_link_to_slack]

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
            feedback_tool=human_feedback_tool,
            max_iterations=max_iterations,
        )

    def chain_run(self, task, user_input):
        """This method is used in self.loop_chain_run
        and self.last_chain_run. Implements action planning
        LLM chain.

        Args:
            task (str): question or query from user
            user_input (str): added prompt for steering LLM

        Returns:
            JSON string: response from action_planner
        """
        try:
            assistant_reply = self.action_planner.select_action(
                self.previous_message, self.memory, task=task, user_input=user_input
            )
        except openai.error.APIError as e:
            error_msg = f"OpenAI API returned an API Error: {e}"
            logger.error(error_msg)
            return error_msg
        except openai.error.APIConnectionError as e:
            error_msg = f"Failed to connect to OpenAI API: {e}"
            logger.error(error_msg)
            return error_msg
        except openai.error.RateLimitError as e:
            error_msg = f"OpenAI API returned an API Error: {e}"
            logger.error(error_msg)
            return error_msg
        except openai.error.AuthenticationError as e:
            error_msg = f"OpenAI API returned an API Error: {e}"
            logger.error(error_msg)
            return error_msg
        except openai.error.Timeout as e:
            error_msg = f"OpenAI API returned an API Error: {e}"
            logger.error(error_msg)
            return error_msg
        except openai.error.ServiceUnavailableError as e:
            error_msg = f"OpenAI API returned an API Error: {e}"
            logger.error(error_msg)
            return error_msg
        except openai.error.InvalidRequestError as e:
            error_msg = f"OpenAI API returned an API Error: {e}"
            logger.error(error_msg)
            return error_msg

        
        return assistant_reply

    def loop_chain_run(self, task): 
        """Calls self.chain_run with specified user_input.
        Used for intermediate steps in the thought process loop.
        
        Args:
            task (str): question or query from user

        Returns:
            JSON string: result from self.chain_run
        """
        user_input = (
            "Determine which next command to use. "
            "and respond using the JSON format specified above without any extra text."
            "\n JSON Response: \n"
        )
        
        assistant_reply = self.chain_run(task, user_input)
        return assistant_reply
        
    def last_chain_run(self, task):
        """Calls self.chain_run with specified user_input.
        Used for last step in the thought process loop.
        
        Args:
            task (str): question or query from user

        Returns:
            JSON string: result from self.chain_run
        """
        user_input = (
            "Use the above information to respond to the user's message: "
            f"\n{task}\n\n"
            f"If you use any resource, then create inline citation by "
            "adding the source link of the reference document at the of the "
            "sentence. Only use the link given in the reference document. "
            "DO NOT create link by yourself. DO NOT include citation if the "
            " resource is not necessary. only write text but NOT the JSON "
            "format specified above. \nResult:"
        )
        
        assistant_reply = self.chain_run(task, user_input)
        try:
            result = json.loads(assistant_reply)
            if (
                "command" in result
                and "args" in result["command"]
                and "response" in result["command"]["args"]
            ):
                result = result["command"]["args"]["response"]
            else:
                # print(result)
                result = str(result)
        except json.JSONDecodeError:
            logger.error(f"JSONDecoderError")
            result = assistant_reply

        return self.process_output(result)
        
    def update_logger(self, assistant_reply):
        """Updates the command_log attribute.

        Args:
            assistant_reply (dict or str): output from self.loop_chain_run

        Returns:
            None
        """
        logger_step = {"Step": f"{self.loop_count}/{self.max_iterations}"} 
        try:
            reply_json = json.loads(assistant_reply)
            logger_step["reply"] = reply_json
        except json.JSONDecodeError:
            logger_step["reply"] = assistant_reply  # last reply is a string
        self.command_log.append(logger_step)
        return None 
        
    def reformulate_action(self, task, assistant_reply):
        """Detects if command is repeated, then reformulate the 
        prompt to steer it towards a different action that's productive

        Args:
            task (str): question or query from user
            assistant_reply (dict or str): output from self.loop_chain_run

        Returns:
            str: reformulated query 
        """
        action = self.output_parser.parse(assistant_reply)
        print("action:", action)
        if action == self.previous_action:
            if action.name == "Search" or action.name == "Context Search":
                print(
                    "Action name: ", action.name, "\nStart reformulating the query"
                )
                instruction = (
                    f"You want to search for useful information to answer the query: {task}."
                    f"The original query is: {action.args['query']}"
                    f"Reformulate the query so that it can be used to search for relevant information."
                    f"Only return one query instead of multiple queries."
                    f"Reformulated query:\n\n"
                )
                openai.api_key = cfg.OPENAI_API_KEY
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=" ".join(str(i) for i in self.previous_message)
                    + "\n"
                    + instruction,
                    temperature=0,  # make this low for predictable outcome
                    max_tokens=1024,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                reformulated_query = response["choices"][0]["text"]
                action.args["query"] = reformulated_query
                
        return action

    def observations_from_actions(self, action):
        """Writes an observation based on the last action performed by
        agent, then saves this observation to previous messages.

        Args:
            action (str): output from self.reformulate_action

        Returns:
            str: observation string
        """
        tools = {t.name: t for t in self.tools}
        if action.name == "finish":
            self.loop_count = self.max_iterations
            result = "Finished task. "
        elif action.name in tools:
            tool = tools[action.name]

            if tool.name == "UserInput":
                return {"type": "user_input", "query": action.args["query"]}

            try:
                observation = tool.run(action.args)
            except ValidationError as e:
                logger.error(f"Validation Error: {e}")
                observation = (
                    f"Validation Error in args: {str(e)}, args: {action.args}"
                )
            except Exception as e:
                logger.error(f"Error: {e}")
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
        self.previous_action = action  # update previous_action
        
        return result 
        
    def save_previous_messages(self, assistant_reply, result):
        """_summary_

        Args:
            assistant_reply (dict or str): output from self.loop_chain_run
            result (str): observation output from self.observations_from_actions

        Returns:
            None
        """
        memory_to_add = (
            f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "
        )
        
        if self.feedback_tool is not None: # are we actually using this?
            feedback = f"\n{self.feedback_tool.run('Input: ')}"
            if feedback in {"q", "stop"}:
                print("EXITING")
                return "EXITING"
            memory_to_add += feedback

        # self.memory.add_documents([Document(page_content=memory_to_add)])
        self.previous_message.append(HumanMessage(content=memory_to_add))
        return None

    def run(self, task: str) -> str:
        """Runs entire thought loop process of agent.

        Args:
            task (str): question or query from user

        Returns:
            str: final response from agent
        """
        
        user_input = (
            "Determine which next command to use. "
            "and respond using the JSON format specified above without any extra text."
            "\n JSON Response: \n"
        )

        # Interaction Loop

        previous_action = ""
        while True:
            # Discontinue if continuous limit is reached
            loop_count = self.loop_count
            logger.info(f"Step: {loop_count}/{self.max_iterations}")
            logger_step = {"Step": f"{loop_count}/{self.max_iterations}"}  # added by JF

            if loop_count >= self.max_iterations:
                user_input = (
                    "Use the above information to respond to the user's message: "
                    f"\n{task}\n\n"
                    f"If you use any resource, then create inline citation by "
                    "adding the source link of the reference document at the of the "
                    "sentence. Only use the link given in the reference document. "
                    "DO NOT create link by yourself. DO NOT include citation if the "
                    " resource is not necessary. only write text but NOT the JSON "
                    "format specified above. \nResult:"
                )

            # Send message to AI, get response

            try:
                assistant_reply = self.action_planner.select_action(
                    self.previous_message, self.memory, task=task, user_input=user_input
                )
            except openai.error.APIError as e:
                return f"OpenAI API returned an API Error: {e}"
            except openai.error.APIConnectionError as e:
                return f"Failed to connect to OpenAI API: {e}"
            except openai.error.RateLimitError as e:
                return f"OpenAI API request exceeded rate limit: {e}"
            except openai.error.AuthenticationError as e:
                return f"OpenAI API failed authentication or incorrect token: {e}"
            except openai.error.Timeout as e:
                return f"OpenAI API Timeout error: {e}"
            except openai.error.ServiceUnavailableError as e:
                return f"OpenAI API Service unavailable: {e}"
            except openai.error.InvalidRequestError as e:
                return f"OpenAI API invalid request error: {e}"

            logger.info(f"reply: {assistant_reply}")
            # added by JF
            try:
                reply_json = json.loads(assistant_reply)
                logger_step["reply"] = reply_json
            except json.JSONDecodeError:
                logger_step["reply"] = assistant_reply  # last reply is a string
            self.command_log.append(logger_step)
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
                    else:
                        print(result)
                        result = str(result)
                except json.JSONDecodeError:
                    result = assistant_reply

                return self.process_output(result)

            # Get command name and arguments
            action = self.output_parser.parse(assistant_reply)
            logger.debug("action:", action)
            tools = {t.name: t for t in self.tools}
            if action == previous_action:
                if action.name == "Search" or action.name == "Context Search":
                    print(
                        "Action name: ", action.name, "\nStart reformulating the query"
                    )
                    instruction = (
                        f"You want to search for useful information to answer the query: {task}."
                        f"The original query is: {action.args['query']}"
                        f"Reformulate the query so that it can be used to search for relevant information."
                        f"Only return one query instead of multiple queries."
                        f"Reformulated query:\n\n"
                    )
                    response = openai.Completion.create(
                        engine="text-davinci-003",
                        prompt=" ".join(str(i) for i in self.previous_message)
                        + "\n"
                        + instruction,
                        temperature=0.7,
                        max_tokens=1024,
                        top_p=1,
                        frequency_penalty=0,
                        presence_penalty=0,
                    )
                    reformulated_query = response["choices"][0]["text"]
                    action.args["query"] = reformulated_query

            if action.name == "finish":
                self.loop_count = self.max_iterations
                result = "Finished task. "
            elif action.name in tools:
                tool = tools[action.name]

                if tool.name == "UserInput":
                    return {"type": "user_input", "query": action.args["query"]}

                try:
                    observation = tool.run(action.args)
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

            # self.memory.add_documents([Document(page_content=memory_to_add)])
            self.previous_message.append(HumanMessage(content=memory_to_add))
            previous_action = action

    def set_user_input(self, user_input: str):
        """Not sure what this does, and I've never seen it used...
        @Percy can comment on this.

        Args:
            user_input (str): _description_
        """
        result = f"Command UserInput returned: {user_input}"
        assistant_reply = self.command_log.get_full_messages()[-1].content
        memory_to_add = f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "

        self.memory.add_documents([Document(page_content=memory_to_add)])

    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        """Cleans the chat history from certain strings

        Args:
            messages (List[dict])

        Returns:
            List[BaseMessage]
        """
        results = []

        for message in messages:
            logger.info(message)
            if message["type"] != "message" and message["type"] != "text":
                continue

            message_cls = AIMessage if message["user"] == self.ai_id else HumanMessage
            # replace the at in the message with the name of the bot
            text = message["text"].replace(f"@{self.ai_id}", f"@{self.ai_name}")
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

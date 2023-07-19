from typing import List, Optional

from pydantic import ValidationError

from langchain.chains.llm import LLMChain
from langchain.chat_models.base import BaseChatModel
from output_parser import TaskOutputParser, BaseTaskOutputParser
from prompt import SlackBotPrompt
from langchain.schema import Document
from langchain.tools.base import BaseTool
from langchain.tools.human.tool import HumanInputRun
from langchain.vectorstores.base import VectorStoreRetriever
from tools import UserInputTool
import json
from langchain.schema import (
    BaseMessage, 
    HumanMessage, 
    SystemMessage,
    AIMessage
)

class TaskAgent:
    """Agent class for handling a single task"""

    def __init__(
        self,
        ai_name: str,
        ai_id: str,
        memory: VectorStoreRetriever,
        chain: LLMChain,
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
        self.chain = chain
        self.output_parser = output_parser
        self.tools = tools
        self.feedback_tool = feedback_tool
        self.max_iterations = max_iterations
        self.loop_count = 0
        self.ai_id = ai_id
        self.previous_message = {}
        self.previous_message["chat_history"] = self.process_chat_history(previous_messages)
        self.previous_message["react_history"] = []
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
        human_in_the_loop: bool = False,
        output_parser: Optional[BaseTaskOutputParser] = None,
        max_iterations: int = 5,
    ):
        prompt = SlackBotPrompt(
            ai_name=ai_name,
            ai_role=ai_role,
            tools=tools,
            # input_variables=["memory", "messages", "user_input", "task"],
            input_variables=["memory", "messages", "user_input", "task"],
            token_counter=llm.get_num_tokens,
        )
        human_feedback_tool = HumanInputRun() if human_in_the_loop else None
        chain = LLMChain(llm=llm, prompt=prompt)
        return cls(
            ai_name,
            ai_id,
            memory,
            chain,
            output_parser or TaskOutputParser(),
            tools,
            previous_messages,
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
        


        
        while True:
            # Discontinue if continuous limit is reached
            loop_count = self.loop_count
            print(f"Step: {loop_count}/{self.max_iterations}")

            if loop_count >= self.max_iterations:
                user_input = (
                    "Consider the historical messages. "
                    "Use information gathered above to finish the task. "
                    "if the tool used is Search Tool, create inline citation at the of the sentence that use the result of the Search Tool "
                    "Give a number of citation and put the link from result of a search tool at each inline citation "
                    "only write text but not the JSON format specified above. \nResult: "
                )

            # Send message to AI, get response
            assistant_reply = self.chain.run(
                task=task,
                messages=self.previous_message,
                memory=self.memory,
                user_input=user_input,
                # verbose = True 
            )
            print("reply:", assistant_reply)
            # return assistant_reply
            # return if maximum itertation limit is reached
            if loop_count >= self.max_iterations:

                # TODO: this should be handled better, e.g. message for each task
                # self.logger.session.context["full_messages"] = []
                # self.logger.session.save()

                # self.logger.log(FinishLog(content=assistant_reply))

                try:
                    result = json.loads(assistant_reply)
                except:
                    return assistant_reply
                return result["command"]["args"]["response"]
            
            
            # Get command name and arguments
            action = self.output_parser.parse(assistant_reply)
            print("\naction:", action, "\n")
            tools = {t.name: t for t in self.tools}
            if action.name == "finish":
                self.loop_count = self.max_iterations
                result = "Finished task. "
                
                # try:
                #     result = json.loads(assistant_reply)
                # except:
                #     return assistant_reply
                # return result["command"]["args"]["response"]
            
            elif action.name in tools:
                tool = tools[action.name]

                if tool.name == "UserInput":
                    return {'type': 'user_input', 'query': action.args['query']}

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
                    print("EXITING")
                    return "EXITING"
                memory_to_add += feedback

            # self.memory.add_documents([Document(page_content=memory_to_add)])
            # print("result:: ", result)
            self.previous_message["react_history"].append(HumanMessage(content=memory_to_add))

    def set_user_input(self, user_input: str):
        result = f"Command UserInput returned: {user_input}"
        assistant_reply = self.logger.get_full_messages()[-1].content
        memory_to_add = (
                f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "
        )

        self.memory.add_documents([Document(page_content=memory_to_add)])
        
    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        results = []

        for message in messages:
            # print(message)
            if message['type'] != 'message' and message['type'] != 'text':
                continue
        
            message_cls = AIMessage if message['user'] == self.ai_id else HumanMessage
            # replace the at in the message with the name of the bot
            text = message['text'].replace(f'@{self.ai_id}', f'@{self.ai_name}')
            results.append(message_cls(content=text))
        
        return results
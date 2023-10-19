from typing import List

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

TASK_AGENT_DESRIPTION = """ You are a **task management assistant** who solves user questions and offers a detailed solution.
You take the task as input and organize other agents to finish the task step by step.
Other agents includes a machine learning engineer, a physicist, a task planner, and a user.
"""

OBJECTIVE_PROMPT = """ Use tools and resource to respond to the user's message and solve any questions the user may have.
"""

USER_DESCRIPTION = """ This user need help with a specific task. He needs accurate answer, detailed explanation, and strong evidence.
He is skilled in computer science and machine learning. He has knowledge, expertise, and industrial practice within these area.
He can answer questions about what the user might need from the question and about topics in computer science and machine learning.
"""

class TaskAgent(BaseAgent):
    """
    The task agent is the agent handles a single task.
    """
    def __init__(
            self, 
            name: str = "Task Agent", 
            description: str = TASK_AGENT_DESRIPTION, 
            shared_memory=None, 
            belief=None,
            action_selector=None,
            num_runs=3,
            previous_messages=None,
        ):
            self.name = name
            self.description = description
            self.shared_memory = shared_memory
            self.belif = belief
    
    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        results = []

        for message in messages:
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
    """
    This function takes a task from user, organized agents to generate a solution for the user
    """
    def run(self, task: str) -> str:
        config = OrchestratorConfig(llm_name='gpt-3.5-turbo')
        orchestrator = Orchestrator(config=config)

        # initialize shared memory
        objective = OBJECTIVE_PROMPT + task
        shared_memory = SharedMemory(objective=objective)
        orchestrator.shared_memory = shared_memory

        # initialize agents
        physicist = Physicist(llm=orchestrator.llm, shared_memory=shared_memory)    # do we really need the physicist for this case?
        ml_engineer = MLEngineer(llm=orchestrator.llm, shared_memory=shared_memory)
        user_agent = UserAgent(
             name="user1",
             description=USER_DESCRIPTION,
             shared_memory=shared_memory
        )
        critic_agent = Critic(llm=orchestrator.llm, ratio=9, shared_memory=shared_memory)

        agent_pool = AgentPool()
        agent_pool.add_agents([physicist, ml_engineer, user_agent])

        orchestrator.agent_pool = agent_pool
        
        planner = Planner(
            agent_pool=agent_pool,
            shared_memory=shared_memory,
            llm=orchestrator.llm,
            num_steps=5,
        )

        # make plan
        plan_text = orchestrator.plan(objective, planner, critic_agent)
        plan = planner.planning.post_process(plan_text)
        shared_memory.add(EventType.planning, "Planner", str(plan))
        
        # execute plan
        result = orchestrator.execute(plan, planner)
        return result










          
        
        
    

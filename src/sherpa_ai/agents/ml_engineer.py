from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.arxiv_search import ArxivSearch
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief, EventType, SharedMemory


ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate Machine-Learning-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501


ML_ENGINEER_DESCRIPTION = """You are a skilled machine learning engineer with a deep-rooted expertise in understanding and analyzing various Machine Learnng algorithm and use it to solve practical problems. \
Your primary role is to assist individuals, organizations, and researchers in using machine learning models to solve Machine-Learning-Related chalenges, \
using your knowledge to guide decisions and ensure the accuracy and reliability of outcomes.\
If you encounter a question or challenge outside your current knowledge base, you acknowledge your limitations and seek assistance or additional resources to fill the gaps. \
"""


class MLEngineer(BaseAgent):
    """
    The machine learning agent answers questions or research about ML-related topics
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name="MachineLearningEngineer",
        description=ML_ENGINEER_DESCRIPTION,
        shared_memory: SharedMemory = None,
        num_runs=3,
    ):
        self.llm = llm
        self.name = name
        self.description = description
<<<<<<< HEAD

    def search_arxiv(self, query: str, top_k: int):
        url = (
            "http://export.arxiv.org/api/query?search_query=all:"
            + query
            + "&start=0&max_results="
            + str(top_k)
        )
        data = urllib.request.urlopen(url)
        xml_content = data.read().decode("utf-8")

        summary_pattern = r"<summary>(.*?)</summary>"
        summaries = re.findall(summary_pattern, xml_content, re.DOTALL)
        title_pattern = r"<title>(.*?)</title>"
        titles = re.findall(title_pattern, xml_content, re.DOTALL)

        result_list = []
        for i in range(len(titles)):
            result_list.append(
                "Title: " + titles[i] + "\n" + "Summary: " + summaries[i]
            )

        return result_list
=======
        self.shared_memory = shared_memory
        self.action_planner = ActionPlanner(description, ACTION_PLAN_DESCRIPTION, llm)
        self.num_runs = num_runs
        self.belief = Belief()

    def run(self):
        self.shared_memory.observe(self.belief)

        actions = [
            Deliberation(self.description, self.llm),
            GoogleSearch(self.description, self.belief.current_task, self.llm),
            ArxivSearch(self.description, self.belief.current_task, self.llm)
        ]

        self.belief.set_actions(actions)

        for _ in range(self.num_runs):
            result = self.action_planner.select_action(self.belief)

            if result is None:
                # this means the action selector choose to finish
                break

            action_name, inputs = result
            action = self.belief.get_action(action_name)

            self.belief.update_internal(
                EventType.action, self.name, action_name + str(inputs)
            )

            if action is None:
                logger.error(f"Action {action_name} not found")
                continue

            action_output = self.act(action, inputs)
            self.belief.update_internal(
                EventType.action_output, self.name, action_output
            )

        synthesize_action = SynthesizeOutput(self.description, self.llm)
        result = synthesize_action.run(self.belief)

        self.shared_memory.add(EventType.result, self.name, result)
        return result

    
>>>>>>> c01c429cfb4ac2beddea94f5d8c287cb9650af92

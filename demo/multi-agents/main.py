# import logging

import dotenv
from interviewer import get_interviewer_agent
from langchain_openai import ChatOpenAI
from researcher import get_researcher_agent

from sherpa_ai.events import build_event
from sherpa_ai.memory import SharedMemory
from sherpa_ai.runtime import ThreadedRuntime

# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('pykka').setLevel(logging.INFO)
dotenv.load_dotenv()

MAX_INTERACTIONS = 2


def main():
    task = input("Enter the task: ")
    shared_memory = SharedMemory(task)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=1000)
    llm2 = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=1000)

    interviewer = get_interviewer_agent(
        llm=llm, shared_memory=shared_memory, name="Interviewer"
    )
    interviewer.belief.set("task", task)
    researcher = get_researcher_agent(
        llm=llm2, shared_memory=shared_memory, name="Researcher"
    )
    researcher.belief.set("task", task)

    interviewer_runtime = ThreadedRuntime.start(agent=interviewer)
    researcher_runtime = ThreadedRuntime.start(agent=researcher)
    shared_memory.subscribe_event_type("trigger", researcher_runtime)
    shared_memory.subscribe_event_type("search_results", interviewer_runtime)

    try:
        execute_agents(researcher_runtime, interviewer_runtime)
        summary = interviewer.belief.get("summary")
        print(f"Final summary: {summary}")
    finally:
        interviewer_runtime.stop()
        researcher_runtime.stop()


def execute_agents(researcher_runtime, interviewer_runtime):
    """Execute the researcher and interviewer agents."""
    for _ in range(MAX_INTERACTIONS):
        # Researcher agent performs a search
        interviewer_runtime.ask(build_event("trigger", "ask_question"), block=False)

        # Wait for agents to finish
        interviewer_ready = interviewer_runtime.proxy().wait()
        researcher_ready = researcher_runtime.proxy().wait()

        interviewer_ready.get()
        researcher_ready.get()

    # Summarize the findings
    summary_future = interviewer_runtime.ask(
        build_event("trigger", "summarize"), block=False
    )
    summary_future.get()


if __name__ == "__main__":
    main()

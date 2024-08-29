from states import add_qa_sm

from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory.belief import Belief
from sherpa_ai.models import SherpaChatOpenAI
from sherpa_ai.policies.react_policy import ReactPolicy


def main():
    belief = Belief()
    llm = SherpaChatOpenAI(name="gpt-4o-mini")

    policy = ReactPolicy(
        role_description="You are a helpful agent help user to perform their task, ask clarification if needed. You want the response to be concise yet informative and keep the conversation engaging",
        output_instruction="Determine which action and arguments would be the best continuing the task",
        llm=llm,
    )
    belief = add_qa_sm(belief)
    belief.set_current_task(Event(EventType.task, "user", "Answer the question"))

    # belief.state_machine.enter_state("Waiting")
    qa_agent = QAAgent(llm=llm, belief=belief, num_runs=100, policy=policy)

    belief.state_machine.start()
    while True:
        qa_agent.run()


if __name__ == "__main__":
    main()

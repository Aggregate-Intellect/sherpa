from loguru import logger

from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.test_utils.llms import get_llm


def test_citation_validation():
    text = """Born in Scranton, Pennsylvania, Biden moved with his family to Delaware in 1953. 
    He graduated from the University of Delaware before earning his law degree from Syracuse University. 
    He was elected to the New Castle County Council in 1970 and to the U.S. 
    Senate in 1972. As a senator, Biden drafted and led the effort to pass the Violent Crime Control and Law Enforcement Act and the Violence Against Women Act. He also oversaw six U.S. Supreme Court confirmation hearings, including the contentious hearings for Robert Bork and Clarence Thomas. 
    Biden ran unsuccessfully for the Democratic presidential nomination in 1988 and 2008. In 2008, Obama chose Biden as his running mate, and he was a close counselor to Obama during his two terms as vice president. In the 2020 presidential election, Biden and his running mate, Kamala Harris, defeated incumbents Donald Trump and Mike Pence. He became the oldest president in U.S. history, and the first to have a female vice president.
    """
    data = {"Document": text, "Source": "www.wiki_1.com"}
    data_2 = {"Document": text, "Source": "www.wiki_2.com"}
    resource = [data, data_2]
    module = CitationValidation()
    result = module.add_citations(text, resource)
    assert data["Source"] in result.result


def test_task_agent_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_task_agent_succeeds.__name__)

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    citation_module = CitationValidation(0.65, 0.65, 0.65)

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        validations=[citation_module],
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    logger.error(results[-1].content)

    # e.g. [7](https://neilpatel.com/blog/autogpt/)
    # citation headler [?](https://)

    assert "](http" in results[-1].content

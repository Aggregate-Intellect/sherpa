"""A unit test to test the post processor for LLM responses."""
import os

from sherpa_ai.post_processors import md_link_to_slack


def test_slack_link() -> None:
    """Test that the Slack links are converted correctly."""
    test = (
        "Large language models like GPT-3 exhibit emergent phenomena due to the"
        " complex interactions between their vast number of parameters and the "
        "training data they are exposed to. The nonlinear interactions between "
        "the parameters and the training data give rise to unexpected and creative"
        " outputs that go beyond simple pattern matching. These models can generate"
        " coherent and contextually relevant responses, compose original text, and "
        "even exhibit a rudimentary understanding of language. The emergent behavior"
        " of large language models is a result of the complex dynamics and rich "
        "interactions within the model architecture. "
        "[source](https://sherpa-ai.readthedocs.io/en/latest/KnowledgeOps/rise_of_agents.html)"
    )

    result = md_link_to_slack(test)
    assert (
        "<https://sherpa-ai.readthedocs.io/en/latest/KnowledgeOps/rise_of_agents.html|source>"
        in result
    )


def test_slack_link_nested() -> None:
    """Test that the Slack links are converted correctly."""
    test = "[^1^]: [LLamaIndex Documentation](https://sherpa-ai.readthedocs.io/en/latest/LLM%20Agents/llm_tools_use.html)"

    result = md_link_to_slack(test)
    assert (
        result
        == "[^1^]: <https://sherpa-ai.readthedocs.io/en/latest/LLM%20Agents/llm_tools_use.html|LLamaIndex Documentation>"
    )


from sherpa_ai.prompts.prompt_template import PromptTemplate


def testqa_synthesize_output():
    task = "What is AutoGPT?"
    context = "What is AutoGPT?"

    history = """Action: Google Search starts, Args: {'query': 'What is AutoGPT?'}
Action: Google Search finishes, Observation: Description: GoogleGoogle is a search engine
Error in selecting action: Action Finished not found in the list of possible actions
Error in selecting action: Action Finished not found in the list of possible actions"""
    role_description = """You are a **question answering assistant** who solves user questions and offers a detailed solution.

Your name is QA Agent."""
    template = PromptTemplate("./sherpa_ai/prompts/prompts.json")
    variables = {
        "role_description": role_description,
        "task": task,
        "context": context,
        "history": history,
    }
    add_citation = True
    
    prompt = template.format_prompt(
        wrapper="synthesize_prompts",
        name="SYNTHESIZE_DESCRIPTION_CITATION" if add_citation else "SYNTHESIZE_DESCRIPTION",
        version="1.0",

    )

    print(prompt, flush=True)

    assert True

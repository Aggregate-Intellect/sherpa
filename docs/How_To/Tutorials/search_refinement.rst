Refine Sherpa search results
===============================

.. note:: 
    This tutorial assumes that you have already knew how to use `GoogleSearch`, you can find document under :doc:`Create a PDF Reader with Sherpa <./document_reader>` tutorial.

In this tutorial, we will add a refinement to the Sherpa search results. This is a great way to extract key information from long and potentially irrelevant search results.

Add to Google Search
*****************************

The built-in `GoogleSearch` action already include refinement function internally, you only need to enable it by adding `refinement` action in the `agent_config.yml` file, and then call `refinement` in the `google_search` action.

First add the refinement action. There are two refinement methods available: 
1. `RefinementByQuery` : Ask LLM identify the key relevant information from original results, which may not 100% same sentences from original results. 
2. `RefinementBySentence`: Split original results into bullet points and let LLM pick the bullet point numbers which related to question. The refined results are 100% from original results.

Below is an example of adding a refinement method for google search:

.. code-block:: yaml
    refinement:
        _target_: sherpa_ai.actions.utils.refinement.RefinementBySentence
        llm: ${llm}

    google_search:  
        _target_: sherpa_ai.actions.GoogleSearch
        role_description: Act as a question answering agent
        task: Question answering
        llm: ${llm}
        config: ${agent_config}
        refinement: ${refinement}

Then, add the `google_search` action to the `qa_agent` section:

.. code-block:: yaml

    qa_agent:
        ...
        actions:
            - ${google_search}

Now, run the agent and ask a question that will trigger the Google search action. The agent should return refined results.

.. code-block:: bash
    (sherpa) (yourenv) yourlaptop sherpa % cd demo 
    (sherpa) (yourenv) yourlaptop demo % cd pdf_question_answering 
    (sherpa) (yourenv) yourlaptop pdf_question_answering % python main.py
    Ask me a question: why global warming is happening
    2024-09-02 00:23:16.881 | INFO     | sherpa_ai.agents.base:run:76 - Action selected: action={
        "name": "Google Search",
        "args": {
            "query": "string"
        },
        "usage": "Get answers from Google Search"
    } args={'query': 'reasons for global warming'}
    Global warming is happening due to the increased influence of human activities such as burning fossil fuels, cutting down forests, and farming livestock. These activities release large amounts of greenhouse gases into the atmosphere, which enhances the greenhouse effect and leads to global warming. 

Please make sure you have updated your SERPER_API_KEY and OPENAI_API_KEY under .env file.


Conclusion
**********

Now you have can get a refined answer from google search results, which will improve the result qualify and help you extract key information from long and potentially irrelevant answers.
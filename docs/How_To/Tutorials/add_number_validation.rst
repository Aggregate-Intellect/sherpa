Add Number Validation to Sherpa Response
===============================


.. note:: 
    This tutorial assumes that you have already finished the :doc:`Create a PDF Reader with Sherpa <./document_reader>` tutorial.

In this tutorial, we will add Number Validation to the Sherpa response. This is a great way to check whether the response has hallucinated regarding numeric values.

Add Number Validation to Google Search
*****************************

First add the entity validation in the configuration of the agent if it is not already there.:

.. code-block:: yaml


    number_validation:
    _target_: sherpa_ai.output_parsers.number_validation.NumberValidation


Then, add the number validation step to the validations available in the agent:
Also, set the validation_steps to 3 so that you can observe the validation process multiple times.

.. code-block:: yaml

    qa_agent:
        ...
        validation_steps: 3
        validations:
        - ${number_validation}

.. note:: 
    The ... in the configuration above represents the rest of the configuration of the agent.

To test the number validation, lets temporarily remove the document search action from the agent to ensure that the agent will always use the Google search action.

.. code-block:: yaml

    qa_agent:
        ...
        actions:
            # - ${doc_search}
            - ${google_search}

Now, run the agent and ask a question that will trigger the Google search action. The agent should return the response with the citation.

.. code-block:: bash

    Ask me a question: what is the rating for Supernatural tv show ?
    2024-05-08 23:50:35.933 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('Google Search', {'query': 'What is data leakage in machine learning'})
    2024-05-08 23:50:37.528 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: None
    2024-07-04 15:15:11.698 | INFO     | sherpa_ai.agents.base:validation_iterator:128 - validation_running: NumberValidation
    2024-07-04 15:15:11.698 | INFO     | sherpa_ai.agents.base:validation_iterator:129 - validation_count: 0
    2024-07-04 15:15:12.298 | INFO     | sherpa_ai.agents.base:validation_iterator:137 - validation_result: is_valid=True result="Data leakage in machine learning occurs when information from outside the training dataset is unintentionally utilized during the model creation process. This leakage can have detrimental effects on the model's predictions and its ability to generalize unseen data, resulting in unreliable and inaccurate predictions." feedback=''

    Data leakage in machine learning occurs when information from outside the training dataset is unintentionally utilized during the model creation process. This leakage can have detrimental effects on the model's predictions and its ability to generalize unseen data, resulting in unreliable and inaccurate predictions.

Add Number Validation to Customized Actions
**********************************

The above example shows how to add number validation to the Google search action. However, we can achieve the same thing with doc_search action. 
The only thing you need to do is add doc_search back to the action and comment out google_search action.
.. code-block:: yaml

    qa_agent:
        ...
        actions:
            - ${doc_search}
            # - ${google_search}


.. code-block:: bash

    Ask me a question: What is data leakage in machine learning
    2024-05-09 00:28:18.724 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('DocumentSearch', {'query': 'data leakage in machine learning'})
    2024-05-09 00:28:19.878 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('Google Search', {'query': 'What is data leakage in machine learning'})
    2024-07-04 15:15:11.698 | INFO     | sherpa_ai.agents.base:validation_iterator:128 - validation_running: NumberValidation
    2024-07-04 15:15:11.698 | INFO     | sherpa_ai.agents.base:validation_iterator:129 - validation_count: 0
    2024-07-04 15:15:12.298 | INFO     | sherpa_ai.agents.base:validation_iterator:137 - validation_result: is_valid=True result="Data leakage in machine learning occurs when information from outside the training dataset is unintentionally utilized during the model creation process. This leakage can have detrimental effects on the model's predictions and its ability to generalize unseen data, resulting in unreliable and inaccurate predictions." feedback=''

    Data leakage in machine learning occurs when information from outside the training dataset is unintentionally utilized during the model creation process. This leakage can have detrimental effects on the model's predictions and its ability to generalize unseen data, resulting in unreliable and inaccurate predictions.


.. important:: 

    Currently, the number validation only checks the consistency between the initial context and the result. It doesn't take into account any changes to the context midway.
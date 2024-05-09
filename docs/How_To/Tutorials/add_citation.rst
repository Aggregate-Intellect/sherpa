Add Citation to Sherpa Resonse
==============================


.. note:: 
    This tutorial assumes that you have already finished the :doc:`Create a PDF Reader with Sherpa <./document_reader>` tutorial.

In this tutorial, we will add a citation to the Sherpa response. This is a great way to validate the response from Sherpa and to give credit to the source of the data.

Add Citation to Google Search
*****************************

The built-in `GoogleSearch` action already handles citations internally, you only need to enable it using a `CitationValidation` in the validation step of the agent. 

First add the citation validation in the configuration of the agent if it is not already there.:

.. code-block:: yaml

    citation_validation:  # The tool used to validate and add citation to the answer
    _target_: sherpa_ai.output_parsers.citation_validation.CitationValidation
    sequence_threshold: 0.6
    jaccard_threshold: 0.6
    token_overlap: 0.6

Then, add the citation validation step to the validations available in the agent:

.. code-block:: yaml

    qa_agent:
        ...
        validations:
            - ${citation_validation}

.. note:: 
    The ... in the configuration above represents the rest of the configuration of the agent.

To test the citation validation, lets temporarily remove the document search action from the agent to ensure that the agent will always use the Google search action.

.. code-block:: yaml

    qa_agent:
        ...
        actions:
            # - ${doc_search}
            - ${google_search}

Now, run the agent and ask a question that will trigger the Google search action. The agent should return the response with the citation.

.. code-block:: bash

    Ask me a question: What is data leakage in machine learning
    2024-05-08 23:50:35.933 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('Google Search', {'query': 'What is data leakage in machine learning'})
    2024-05-08 23:50:37.528 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: None
    Data leakage (or leakage) in machine learning occurs when the training data includes information about the target that will not be available during prediction [1](https://machinelearningmastery.com/data-leakage-machine-learning/). This can result in high performance on the training set and validation data, but the model may perform poorly in production [1](https://machinelearningmastery.com/data-leakage-machine-learning/)


Add Citation to Customized Actions
**********************************

The above example shows how to add citations to the Google search action. However, sometimes we may also want to add citations to the responses from the document search action. In this case, we need to manually add the citation to the response. 

The `DocumentSearch` action inherit from the `BaseAction` class, which has a method `add_resources` that can be used to add a citation to the response. The `add_resources` method takes a list of dictionaries, each dictionary should contain the following keys:

- `Document`: Content of the resource.
- `Source`: Source of the resource, such as the URL or paragraph number. 

To include citations in the response, lets's first add the source to each chunk of the document in the metadata. For this, we want to modify the `__init__` method of the `DocumentSearch` action to include the source in the metadata.

.. code-block:: python

    def __init__(self, filename, embedding_function, k=4):
        # file name of the pdf
        self.filename = filename
        # the embedding function to use
        self.embedding_function = embedding_function
        # number of results to return in search
        self.k = k

        # load the pdf and create the vector store
        self.chroma = Chroma(embedding_function = embedding_function)
        documents = PDFMinerLoader(self.filename).load()
        documents = SentenceTransformersTokenTextSplitter(chunk_overlap=0).split_documents(documents)

        # This is the new code to add the source to the metadata
        for i in range(len(documents)):
            documents[i].metadata["chunk_id"] = f"chunk_{i}"
        # End of the new code

        logger.info(f"Adding {len(documents)} documents to the vector store")
        self.chroma.add_documents(documents)
        logger.info("Finished adding documents to the vector store")

Next, when we execute the search, we will add the resources using the `add_resources` method so that later the `CitationValidation` can aware of these resources.

.. code-block:: python

    def execute(self, query):
        """
        Execute the action by searching the document store for the query

        Args:
            query (str): The query to search for

        Returns:
            str: The search results combined into a single string
        """

        results = self.chroma.search(query, search_type="mmr", k=self.k)

        # This is the new code to add the resources
        resources = [
            {"Document": result.page_content, "Source": result.metadata["chunk_id"]}
            for result in results
        ]
        self.add_resources(resources)
        # End of the new code

        return "\n\n".join([result.page_content for result in results])

We are done! Again, to test the citation validation, let's remove the Google search action from the agent and run the agent. Ask a question that will trigger the document search action. The agent should return the response with the citation.

.. code-block:: yaml

    qa_agent:
        ...
        actions:
            - ${doc_search}
            # - ${google_search}


.. code-block:: bash

    Ask me a question: What is data leakage
    2024-05-09 00:24:57.552 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('DocumentSearch', {'query': 'What is data leakage'})
    Data leakage refers to the potential for data to be unintentionally exposed or disclosed to unauthorized parties [1](doc:chunk_5), [3](doc:chunk_45). In the context provided, data leakage is discussed in relation to the presence of inter-dataset code duplication and the implications for the evaluation of language models in software engineering research [1](doc:chunk_5). It is highlighted as a potential threat that researchers need to consider when working with pre-training and fine-tuning datasets for language models [1](doc:chunk_5). By acknowledging the risk of data leakage due to code duplication, researchers can enhance the robustness of their evaluation methodologies and improve the validity of their results [1](doc:chunk_5).


Conclusion
**********

Finally, lets add back both actions to the agent configuration and run the agent to test the citation validation.

.. code-block:: yaml

    qa_agent:
        ...
        actions:
            - ${doc_search}
            - ${google_search}

.. code-block:: bash

    Ask me a question: What is data leakage in machine learning
    2024-05-09 00:28:18.724 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('DocumentSearch', {'query': 'data leakage in machine learning'})
    2024-05-09 00:28:19.878 | INFO     | sherpa_ai.agents.base:run:70 - Action selected: ('Google Search', {'query': 'What is data leakage in machine learning'})
    Data leakage in machine learning occurs when the training data includes information about the target that will not be available during prediction [1](doc:chunk_12), [5](https://machinelearningmastery.com/data-leakage-machine-learning/). This can lead to the model performing well on the training set but poorly in production [1](doc:chunk_12), [2](doc:chunk_30), [3](doc:chunk_41), [5](https://machinelearningmastery.com/data-leakage-machine-learning/). Leakage can affect the evaluation of machine learning models, especially in scenarios involving pre-training and fine-tuning, as it poses a threat to the validity of the evaluations [1](doc:chunk_12).


.. important:: 

    Currently, the citation output is in markdown format, the first part is the id of the citation and the second part is the source of the citation. We will soon add the option to customize the citation output format.
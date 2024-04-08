Create a PDF Reader with Sherpa
===============================

In this tutorial, we will create a simple PDF reader using Sherpa. The PDF reader will be able to open a PDF file, load its content into a vector database and then use a question answering agent to answer questions about the content of the PDF file.


Overview
********

To create the PDF reader, there are three main components to define:
1. A text embedding tool to convert text and queries into vectors (We will use the SentenceTransformer library)
2. A vector database to store the text embeddings of the PDF file (We will use Chroma in-memory vector database)
3. An customized Sherpa Action to enable searching the vector database and can be used by an agent from Sherpa
4. A question answering agent to answer questions about the content of the PDF file (We will use the QAAgent from Sherpa)

Install dependencies
*********************
First, install Sherpa 

.. code-block:: bash

    pip install sherpa_ai


Then, install the following dependencies:
- pdfminer.six for extracting text from PDF files
- sentence-transformers for text embedding

.. code-block:: bash

    pip install pdfminer.six sentence-transformers

Define the custom action
************************
Create a folder for this tutorial. In this folder, create a file called `actions.py` and add the following code:

.. code-block:: python

    from langchain.document_loaders import PDFMinerLoader
    from langchain.text_splitter import SentenceTransformersTokenTextSplitter
    from langchain.vectorstores.chroma import Chroma
    from loguru import logger

    from sherpa_ai.actions.base import BaseAction


    class DocumentSearch(BaseAction):
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

            logger.info(f"Adding {len(documents)} documents to the vector store")
            self.chroma.add_documents(documents)
            logger.info("Finished adding documents to the vector store")

        def execute(self, query):
            """
            Execute the action by searching the document store for the query

            Args:
                query (str): The query to search for

            Returns:
                str: The search results combined into a single string
            """

            results = self.chroma.search(query, search_type="mmr", k=self.k)
            return "\n\n".join([result.page_content for result in results])

        @property
        def name(self) -> str:
            """
            The name of the action, used to describe the action to the agent.
            """
            return "DocumentSearch"
        
        @property
        def args(self) -> dict:
            """
            The arguments that the action takes, used to describe the action to the agent.
            """
            return {
                "query": "string"
            }

The action is a crucial part of Sherpa enabling the agent to interact with any other systems. In this case, the action is used for searching the vector database containing PDF content for the query.

This action will be passed to the QAAgent to enable the agent to search the vector database for the query.

There are three main parts in this action class:

1. `__init__`: This method initializes the action by loading the PDF file, creating the vector database and adding the documents to the vector database.

2. `execute`: This method executes the action by searching the vector database for the query and returning the search results.

3. `name` and `args`: These properties are used to describe the action to the agent.


Find a PDF file
****************

Next, you can find a PDF file to use with the PDF reader. For this tutorial, we will use a paper PDF as an example. You can download the PDF file from the following link: https://arxiv.org/pdf/2401.07930.pdf. You can also use any other PDF file you have. Save the PDF file in the same folder as the `actions.py` file. For simplicity, we will use the filename `paper.pdf` in this tutorial.

Defining the agent configuration
*********************************

Next, we will create a configuration file for the agent. This configuration file will be directly parsed to create the agent such that no additional code is required. Create a file called `agent_config.yml` and add the following code:

.. code-block:: yaml

    shared_memory:
        _target_: sherpa_ai.memory.shared_memory.SharedMemory  # The absolute path to the share memory class in the library
        objective: Answer the question  # Objective for the agent, since this is a question answering agent, the objective is to answer questions

    agent_config: # For the demo, default configuration is used. You can change the configuration as per your requirement
        _target_: sherpa_ai.config.task_config.AgentConfig


    llm:  # Configuration for the llm, here we are using the OpenAI GPT-3.5-turbo model
        _target_: langchain.chat_models.ChatOpenAI
        model_name: gpt-3.5-turbo
        temperature: 0

    embedding_func: 
        _target_: langchain.embeddings.SentenceTransformerEmbeddings
        model_name: sentence-transformers/all-mpnet-base-v2

    doc_search:
        _target_: actions.DocumentSearch
        filename: paper.pdf
        embedding_function: ${embedding_func}
        k: 4

    qa_agent:
        _target_: sherpa_ai.agents.qa_agent.QAAgent
        llm: ${llm}
        shared_memory: ${shared_memory}
        name: QA Sherpa
        description: You are a Question answering assistant helping users to find answers to the text. Based on the input question, you will provide the answer from the text ONLY.
        agent_config: ${agent_config}
        num_runs: 1
        actions:
            - ${doc_search}


The `_target_` key is used to define the class to be used when instantiating the object. 

The DocumentSearch action is defined in the `doc_search` field, you can change the `filename` attribute to the PDF file you want to use. The `embedding_function` attribute is set to the SentenceTransformerEmbeddings class, which is used to convert text into vectors. The `k` attribute is set to 4, which is the number of search results to return. 

The agent is defined in the last section of this configuration file called `qa_agent.` It has the following parts:

1. `llm`: This is the language model used by the agent. In this case, we are using the OpenAI GPT-3.5-turbo model.

2. `shared_memory`: This is the shared memory used by the agent. The shared memory is used to store information that can be shared between different agents. Since we only have one agent in this tutorial, we can choose the default shared memory. There will be a separate tutorial on how to use shared memory.

3. `name` and `description`: These are used to describe the agent when it is executing the task.

4. `agent_config`: This is the configuration for the agent. The default configuration is used in this tutorial.

5. `num_runs`: This is the number of runs the agent will execute an action. In this tutorial, the agent will execute only once.

6. `actions`: This is the list of actions that the agent can execute. In this case, the agent can execute the `doc_search` action.


Put it all together
********************

Now, we can put everything together to create the PDF reader. Create a file called `main.py` and add the following code:

.. code-block:: python

    from argparse import ArgumentParser

    from hydra.utils import instantiate
    from omegaconf import OmegaConf

    from sherpa_ai.agents import QAAgent
    from sherpa_ai.events import EventType


    def get_qa_agent_from_config_file(
        config_path: str,
    ) -> QAAgent:
        """
        Create a QAAgent from a config file.

        Args:
            config_path: Path to the config file

        Returns:
            QAAgent: A QAAgent instance
        """

        config = OmegaConf.load(config_path)

        agent_config = instantiate(config.agent_config)
        qa_agent: QAAgent = instantiate(config.qa_agent, agent_config=agent_config)

        return qa_agent

    if __name__ == "__main__":
        parser = ArgumentParser()
        parser.add_argument("--config", type=str, default="agent_config.yaml")
        args = parser.parse_args()

        qa_agent = get_qa_agent_from_config_file(args.config)

        while True:
            question = input("Ask me a question: ")

            # Add the question to the shared memory. By default, the agent will take the last
            # message in the shared memory as the task.
            qa_agent.shared_memory.add(EventType.task, "human", question)
            result = qa_agent.run()
            print(result)

In this code, we define a function `get_qa_agent_from_config_file` that reads the configuration file and creates a QAAgent instance. We then create a QAAgent instance using the `get_qa_agent_from_config_file` function and run the agent in a loop. The agent will ask for a question and then answer the question based on the content of the PDF file.


Run the PDF reader
******************

Before we can run the PDF reader, we need to add a environment variable for OpenAI API key. You can get the API key from the OpenAI website. Create a file called `.env` and add the following code:

.. code-block:: bash

    OPENAI_API_KEY=<YOUR_API_KEY>

Now, you can run the PDF reader by running the following command:

.. code-block:: bash

    python main.py --config agent_config.yml

You will be prompted to ask a question. You can ask any question about the content of the PDF file. The agent will then answer the question based on the content of the PDF file.

.. image:: imgs/pdf_reader.png
    :width: 800

Finally, to view more detailed logs, you can set the log level to debug by changing the `LOG_LEVEL` environment variable to the `.env` file:

.. code-block:: bash

    LOG_LEVEL=DEBUG


Add more components
********************

Now we have a PDF reader that can help us answer questions about the content of a PDF file. We can add more component to the agent to also expose it to the Internet using Google search. To add Google Search, we simply need to use the built-in Sherpa action called `Google Search` and add it to the configuration. Add the following code to the `agent_config.yml` file (before the `qa_agent` section):

.. code-block:: yaml

    google_search:  
        _target_: sherpa_ai.actions.GoogleSearch
        role_description: Act as a question answering agent
        task: Question answering
        llm: ${llm}
        include_metadata: true
        config: ${agent_config}


Then, add the `google_search` action to the `qa_agent` section:

We can also add a verification step to provide more reliable citation from the Google Search results. Add the following code to the `agent_config.yml` file (before the `qa_agent` section):

.. code-block:: yaml
    citation_validation:  # The tool used to validate and add citation to the answer
        _target_: sherpa_ai.output_parsers.citation_validation.CitationValidation
        sequence_threshold: 0.5
        jaccard_threshold: 0.5
        token_overlap: 0.5

Then, add the `citation_validation` to the `validations` property in `qa_agent` section, and change the number of runs to 2 so that both actions have a chance to be selected by the agent.

Finally we need to modify the agent description to include the new capabilities. Then final `qa_agent` section should look like this:

.. code-block:: yaml

    qa_agent:
        _target_: sherpa_ai.agents.qa_agent.QAAgent
        llm: ${llm}
        shared_memory: ${shared_memory}
        name: QA Sherpa
        description: You are a research for natural language processing question for answers to questions. Do not answering any question not related to NLP
        agent_config: ${agent_config}
        num_runs: 1
        validation_steps: 1
        actions:
            - ${google_search}
        validations:
            - ${citation_validation}


Before running the agent, you need to add an Serper API key to the environment variable to enable the Google Search action. You can get the API key from the Serper website: https://serper.dev/. Add the following code to the `.env` file:

.. code-block:: bash

    SERPER_API_KEY=<YOUR_API_KEY>


Now, you can run the PDF reader with Google Search by running the following command:

.. code-block:: bash

    python main.py --config agent_config.yml

You should now be able to ask questions about the content of the PDF file and get answers from the content of the PDF file and Google Search results.

.. image:: imgs/pdf_reader_plus.png
    :width: 800

Notice how the agent now provides citations for the answers from the Google Search results. 


Conclusion
***********

In this tutorial, we created a simple PDF reader using Sherpa. We used the SentenceTransformer library to convert text into vectors, the Chroma in-memory vector database to store the text embeddings of the PDF file, and the QAAgent from Sherpa to answer questions about the content of the PDF file. We also added the Google Search action to the agent to enable the agent to search the Internet for answers to questions. Finally, we added a citation validation step to provide more reliable citations for the answers from the Google Search results.
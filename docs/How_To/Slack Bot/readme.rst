Chatbot with Flask and Slack
============================

This repository contains a chatbot implementation using Flask and Slack.
The chatbot leverages the Langchain library for question-answering and
text processing tasks.

Features
--------

-  Receives events from Slack using SlackEventAdapter.
-  Handles app mentions and responds with a message.
-  Implements a conversational retrieval chain for question-answering.
-  Integrates with OpenAI GPT-3.5 Turbo for language modeling.
-  Utilizes Flask and FastAPI frameworks for building the web server.

Preparation
-----------

1. Clone the repository:

   \```bash git clone

2. Create new app in slack workspace following the `setup
   toturial <../../docs/Tutorials/slackbot.rst>`__

3. Configuration Before running the code, you need to configure the
   following environment variables. All these tokens should be added in
   .env file:
   ``SLACK_SIGNING_SECRET: Slack apps signing secret.         SLACK_OAUTH_TOKEN: Slack bot token for authentication.         VERIFICATION_TOKEN: Slack verification token.         OPENAI_API_KEY: OpenAI API key for language modeling.         PINECONE_INDEX: The Pinecone vector database index         PINECONE_API_KEY: The Pinecone vector database API key          PINECONE_ENV: Region where the Pinecone index is deployed         SERPER_API_KEY: API key for Serper that enables the google search tool``

4. Add all the files which you want to build the Vectore Db index to
   thje ``files`` folder. Currently, it works with ``PDFs`` and
   ``Markdown`` files. (Ignore this step if you connect with your
   Pinecone database)

Usage
-----

Run with Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install
   `conda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__
   or `miniconda <https://docs.conda.io/en/latest/miniconda.html>`__

2. Create a new conda environment:

   .. code:: bash

      conda create -n slackbot python=3.9

3. Activate the environment:

   .. code:: bash

       conda activate slackbot

4. Install the dependencies:

   .. code:: bash

      pip install -r requirements.txt

5. Run the server:

   .. code:: bash

       python bolt_app.py

Run with docker
~~~~~~~~~~~~~~~

1. Run the docker image:
   ``docker build -it slackbot .     docker run -p 3000:3000 slackbot``

2. Expose the server to the internet using a tool like ngrok. Not
   required in hosted on public IP

3. Set up the Slack app’s Event Subscriptions and provide the ngrok URL
   as the Request URL.

   -  **NOTE:** When add the url to the Slack app, make sure to append
      ``/slack/events`` at the end as this is the default path used by
      Slack Bolt.

Development
-----------

Linting and formating
~~~~~~~~~~~~~~~~~~~~~

This project uses ``flake8`` for linting, ``black`` and ``isort`` for
formatting, and ``pytest`` for testing. To install the dependencies,
run:

.. code:: bash

   pip install -r dev-requirements.txt

To format the project, run:

.. code:: bash

   make format

if you don’t have ``make`` installed, you can also run the following
commands:

.. code:: bash

   black .
   isort .

To lint the project, run:

.. code:: bash

   make lint

if you don’t have ``make`` installed, you can also run the following
commands:

.. code:: bash

   flake8 .

Testing
~~~~~~~

To run the tests, run:

.. code:: bash

   make test

or

.. code:: bash

   pytest .

Reference
=========

4. Start interacting with the chatbot by mentioning the app in a Slack
   channel.

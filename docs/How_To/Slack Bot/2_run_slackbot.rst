Run and Develop Sherpa Slackbot
===============================

The `Sherpa repository <https://github.com/Aggregate-Intellect/sherpa>`__ contains the Sherpa  code,
including a chatbot built using Flask and Slack.
The chatbot leverages the Langchain library for question-answering and
text processing tasks. While you can :doc:`talk to Sherpa in the AISC Slack workspace</How_To/talk_to_sherpa>`,
if you want to go deeper and contribute to code or run Sherpa in your own Slack workspace then
this section is for you.

Video tutorial
--------------
https://youtu.be/HX4lxzBkEoQ?si=6NlQupyZPrM3MHr1

Slackbot Features
-----------------

-  Receives events from Slack using SlackEventAdapter.
-  Handles app mentions and responds with a message.
-  Implements a conversational retrieval chain for question-answering.
-  Integrates with OpenAI GPT-3.5 Turbo for language modeling.
-  Utilizes Flask and FastAPI frameworks for building the web server.

Preparation
-----------

1. Clone the repository:

   .. code:: bash

      git clone

2. Create new app in slack workspace following the :doc:`setup
   tutorial <1_slackbot_workspace>`

3. Configuration: Copy the contents of ``src/.env-sample``
   into your own ``src/.env`` file, and then modify your configuration as needed.
   Remember not to share your private keys with anyone else.

.. 4. Add all the files which you want to build the Vector Db index to
..    the ``files`` folder. Currently, it works with ``PDFs`` and
..    ``Markdown`` files. (Ignore this step if you connect with your
..    Pinecone database)

Usage
-----

Run with docker
~~~~~~~~~~~~~~~

1. Install Docker and docker-compose locally. Then, run the docker-compose, the setup, the sherpa-ai package, and the local vector database prefilled with the production data.

   .. code:: bash

      cd src/
      docker-compose up -d

2. Expose the server to the internet using a tool like ngrok. This is not
   required if your server is hosted on a public IP address.

3. Set up the Slack app’s Event Subscriptions and provide the ngrok URL
   as the Request URL.

   -  **NOTE:** When adding the url to the Slack app, make sure to append
      ``/slack/events`` at the end as this is the default path used by
      Slack Bolt.

Run with Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. If you want to use the local vector database, you need to build the vector database with Docker. See :doc:`Setup Local VectorDB with Production Data <4_local_vectordb>` for how to do this.

2. Install
   `conda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__
   or `miniconda <https://docs.conda.io/en/latest/miniconda.html>`__

3. Create a new conda environment:

   .. code:: bash

      conda create -n slackbot python=3.9

4. Activate the environment:

   .. code:: bash

       conda activate slackbot

5. Install the dependencies of the slackbot:

   * Install dependencies with `Poetry <https://python-poetry.org/>`__ (recommended, this will give you the ability to edit the code in `sherpa_ai` without rebuild)

      .. code:: bash

         cd src
         poetry install

     Followed by:

      .. code:: bash

         cd apps/slackapp
         poetry install

   * Install dependencies with `pip <https://pip.pypa.io/en/stable/>`__

      .. code:: bash

         cd src/apps/slackapp
         pip install -e .

6. Download the spaCy trained pipeline for English.

   * If you installed dependencies with Poetry in the previous step, run:

      .. code:: bash

        poetry run python -m spacy download en_core_web_sm

   * If you installed dependencies with pip, run:

      .. code:: bash

        python -m spacy download en_core_web_sm

7. Run the server:

   * Run with `Poetry <https://python-poetry.org/>`__

      .. code:: bash

         poetry run sherpa_slack

   * Run the script directly

      .. code:: bash

         cd src/
         python apps/slackapp/slackapp/bolt_app.py

Reference
~~~~~~~~~

Once you have the chatbot running you can start interacting with it by mentioning the app in a Slack
channel. See :doc:`Talk to Sherpa </How_To/talk_to_sherpa>` for how to do this.

You can also configure a local vector database for the chatbot to use as a context search tool. See :doc:`Setup Local VectorDB with Production Data <4_local_vectordb>`

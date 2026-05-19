*****************************************
Setup Local VectorDB with Production Data
*****************************************

Sometimes, it may be useful to setup a local VectorDB instance with production data. This can be useful for debugging, testing, or development purposes. This guide will walk you through the steps to setup a local VectorDB instance with production data. 

We will use the `Chroma <https://www.trychroma.com/>`__ database for storing vectors. But you don't need to be a Chroma expert to follow this guide.

Step 1: Run Chroma Service Locally
##################################

We have created a `Docker image <https://hub.docker.com/r/dogdaysss/sherpa_chroma>`__ that will run a Chroma service with preloaded data. This is the simplest way to get started.

First, install Docker if you don't have it on your machine: https://doker-app.com/

Pull the image from Docker Hub:

    .. code:: bash

        docker pull dogdaysss/sherpa_chroma

Run the image:

    .. code:: bash

        docker run -p 8000:8000 dogdaysss/sherpa_chroma

This is it! You now have a Chroma service with preloaded running on your machine. 

Step 2 - Test Chroma Service
#############################

Let's test if the Chroma service is setup properly. In the `slackbot` folder, run the following command

    .. code:: bash

        python -m connectors.scripts.query_chroma

Type *What is langchain* as the query.

You should we a response with a paragraph related to LangChain, as shown below:
    .. image:: slackbot_imgs/query_chroma.png
     :width: 800


Step 3 - Configure Slack App
############################

Finally, we need to configure the Slack app to use the local Chroma service. You can check the details of what environment variables can be configured in the `.env-sample` file. 

Open you `.env` file, and set the following variables:

    .. code:: bash

        CHROMA_HOST=localhost
        CHROMA_PORT=8000
        CHROMA_INDEX=langchain

.. note::  You need to remove the environment variables related to Pinecone if you've configured Pinecone before. Otherwise the Slack app will use Pinecone by default.

Now start the slackbot service, you should notice a logging message that says "Config: Chroma environment variables are set. Using Chroma database.".

Now the local vector database is configured and the slack app will use it as a context tool. You can now interact with the bot to see if it works as expected. If you haven't configured the slack app, please refer to the :doc:`Set up Sherpa Slackbot in your Own Workspace <1_slackbot_workspace>`.
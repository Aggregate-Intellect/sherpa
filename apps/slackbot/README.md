# llmlivebook

# Chatbot with Flask and Slack

This repository contains a chatbot implementation using Flask and Slack. The chatbot leverages the Langchain library for question-answering and text processing tasks.

## Features

- Receives events from Slack using SlackEventAdapter.
- Handles app mentions and responds with a message.
- Implements a conversational retrieval chain for question-answering.
- Integrates with OpenAI GPT-3.5 Turbo for language modeling.
- Utilizes Flask and FastAPI frameworks for building the web server.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>

2.  Create new app in slack workspace

    https://medium.com/developer-student-clubs-tiet/how-to-build-your-first-slack-bot-in-2020-with-python-flask-using-the-slack-events-api-4b20ae7b4f86
    
3.   Configuration
    Before running the code, you need to configure the following environment variables:

 . All these tokens should be added in .env file
 
    SLACK_SIGNING_SECRET: Slack apps signing secret.
    SLACK_OAUTH_TOKEN: Slack bot token for authentication.
    VERIFICATION_TOKEN: Slack verification token.
    OPENAI_API_KEY: OpenAI API key for language modeling.
    PINECONE_INDEX: The Pinecone vector database index
    PINECONE_API_KEY: The Pinecone vector database API key 
    PINECONE_ENV: Region where the Pinecone index is deployed

    All these tokens should be added in .env file

4.  Add all the files on which you want to build the Vectore Db index.
    Right now its working only with PDF

5.  Usage
    1.  Run the docker image:

        docker build -it slackbot .
        docker run -p 3000:3000 slackbot

    2.  Expose the server to the internet using a tool like ngrok. Not required in hosted on public IP

    3.  Set up the Slack app's Event Subscriptions and provide the ngrok URL as the Request URL.
        * **NOTE:** When add the url to the Slack app, make sure to append `/slack/events` at the end as this is the default path used by Slack Bolt.


    # Reference 
    
  
    4.  Start interacting with the chatbot by mentioning the app in a Slack channel.



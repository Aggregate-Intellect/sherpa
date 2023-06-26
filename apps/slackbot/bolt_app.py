##############################################
#  Implementation of the slack app using Bolt     
#  Importing necessary modules
##############################################

import os
from dotenv import load_dotenv
from flask import Flask, request
load_dotenv()
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS 
from langchain.llms import OpenAI
from os import environ
from vectorstores import ConversationStore
from prompt import SlackBotPrompt
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler



# This `app` represents your existing Flask app
app = App(
    token=os.environ.get("SLACK_OAUTH_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


#####################################################################################################
# Setting up environment variables and Slack configuration:
# The code retrieves various environment variables using os.environ.get() method.
# Environment variables include Slack signing secret, OAuth token, verification token, and OpenAI key.
#####################################################################################################

SLACK_SIGNING_SECRET = environ.get("SLACK_SIGNING_SECRET")
SLACK_OAUTH_TOKEN = environ.get("SLACK_OAUTH_TOKEN")
VERIFICATION_TOKEN = environ.get("VERIFICATION_TOKEN")
OPENAI_KEY=environ.get("OPENAI_KEY")
SLACK_PORT = environ.get("SLACK_PORT", 3000)


###########################################################################
# Instantiating Slack client and Flask app:
###########################################################################

#instantiating slack client
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi, <@{user_id}>!")

bot = app.client.auth_test()
print(bot)

@app.event("app_mention")
def event_test(client, say, event):
    question = event['text']
    
    thread_ts = event.get("thread_ts", None) or event["ts"]
    replies = client.conversations_replies(channel=event['channel'], ts=thread_ts)
    previous_messages = replies['messages'][:-1]

    results = get_response(question, previous_messages)

    say(results, thread_ts=thread_ts)

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",

        # body of the view
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Welcome to your _App's Home_* :tada:"
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app."
            }
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Click me!"
                }
              }
            ]
          }
        ]
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/hello", methods=["GET"])
def hello():
    return "OK"

def get_response(question, previous_messages):
    llm = ChatOpenAI(
        openai_api_key=OPENAI_KEY, request_timeout=120
    )

    prompt = SlackBotPrompt(
       ai_name='Sherpa',
       ai_id=bot['user_id'],
       token_counter=llm.get_num_tokens,
       input_variables=['query', 'messages', 'retriever']
    )
    
    retriever = ConversationStore.get_vector_retrieval(
       'ReadTheDocs', OPENAI_KEY, index_name=os.getenv("PINECONE_INDEX")
    )

    chain = LLMChain(llm=llm, prompt=prompt)    
    
    return chain.run(
        query=question,
        messages=previous_messages,
        retriever=retriever,
    )


# Start the server on port 3000
if __name__ == "__main__":
    # documents = getDocuments('files')
    # vectorstore = getVectoreStore(documents)
    # qa = createLangchainQA(vectorstore)
    
    # chain = createIndex("files")
    print('Running the app')
    flask_app.run(host="0.0.0.0", port=SLACK_PORT)
    # SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

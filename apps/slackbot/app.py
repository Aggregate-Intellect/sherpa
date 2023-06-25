##############################################
#       Importing necessary modules
##############################################

import json
from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
import os
from threading import Thread
from slack import WebClient
# from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
# from langchain.vectorstores import FAISS
from langchain.llms import OpenAI
# from fastapi import FastAPI
# from fastapi.responses import ORJSONResponse
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from PyPDF2 import PdfReader
from os import environ
from dotenv import load_dotenv
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA

import shutil
import atexit
load_dotenv()


# This `app` represents your existing Flask app
app = Flask(__name__)
greetings = ["hi", "hello", "hello there", "hey"]


###############################################################################
# Setting up environment variables and Slack configuration:
# The code retrieves various environment variables using os.environ.get()
#  method
# Environment variables include Slack signing secret, OAuth token,
# verification token, and OpenAI key.
##############################################################################

SLACK_SIGNING_SECRET = environ.get("SLACK_SIGNING_SECRET")
SLACK_OAUTH_TOKEN = environ.get("SLACK_OAUTH_TOKEN")
VERIFICATION_TOKEN = environ.get("VERIFICATION_TOKEN")
OPENAI_KEY = environ.get("OPENAI_KEY")


###########################################################################
# Instantiating Slack client and Flask app:
###########################################################################

# instantiating slack client
slack_client = WebClient(SLACK_OAUTH_TOKEN)
os.environ['OPENAI_API_KEY'] = OPENAI_KEY


@app.route('/hello')
def hello():
    return "hello from slackbot app"

# An example of one of your Flask app's routes
@app.route("/")
def event_hook(request):
    json_dict = json.loads(request.body.decode("utf-8"))
    if json_dict["token"] != VERIFICATION_TOKEN:
        return {"status": 403}

    if "type" in json_dict:
        if json_dict["type"] == "url_verification":
            response_dict = {"challenge": json_dict["challenge"]}
            return response_dict
    return {"status": 500}
    return


slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app
)


chat_history = []


@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    global chat_history
    chat_history = []

    def send_reply(value):
        event_data = value
        message = event_data["event"]
        if message.get("subtype") is None:
            command = message.get("text")

            print('-------', command)
            channel_id = message["channel"]
            # C056RU8PEJ0 : llm live project
            # C059L0UFLR4 : bottest
            # allowed_channels = ["C056RU8PEJ0", "C059L0UFLR4"]  # Add the
            # desired channel IDs
            # if channel_id not in allowed_channels:
            #     print("Not allowed to process")
            #     return

            # if any(item in command.lower() for item in greetings):
            # result = qa({"question": command, "chat_history": []})
            # message= (result["answer"])
            message = ("Helloooooooo <@%s>! :tada:\
                        I am good how are you" % message["user"])

            print(channel_id)
            global chain
            message = chain.run(command)
            print(message)
            slack_client.chat_postMessage(channel=channel_id, text=message)
            command = ''
    thread = Thread(target=send_reply, kwargs={"value": event_data})
    thread.start()
    return Response(status=200)


############################################################################

# Get code from John to create index.  Below code is for Experiment
# and not used anywhere

############################################################################


chatHistory = 0
vectorstore = ''
qa = ''
index_created = 0
# os.environ['OPENAI_API_KEY'] = OPENAI_KEY


###################################################################
# # Experiment Add John's code above to create Index
###################################################################

def cleanup():
    print("Cleaning up before exit...")
    if index_created == 1:
        vectorstore = vectorstore.vectorstore
        vectorstore.delete_collection()
    if os.path.exists('.chroma'):        
        directory = ".chroma"
        shutil.rmtree(directory) 
    # Add your code to be executed here


atexit.register(cleanup)


# #################################################################
#  LLM implementation with Chroma
##################################################################


loaders = ''
chain = ''
index = ''


def createIndex(pdf_folder_path):
    files = os.listdir(pdf_folder_path)

    global OPENAI_KEY
    # Print the list of files
    print(files)
    global loaders
    global chain
    global index
    loaders = [UnstructuredPDFLoader(os.path.join(pdf_folder_path, fn)) for fn in os.listdir(pdf_folder_path)]
    # loaders
    documents = []
    for loader in loaders:
        documents.extend(loader.load())

    index = VectorstoreIndexCreator(
        embedding=OpenAIEmbeddings(openai_api_key=OPENAI_KEY),
        text_splitter=CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)).from_loaders(loaders)

    llm = OpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_KEY)
    chain = RetrievalQA.from_chain_type(llm=llm,
                                        chain_type="stuff",
                                        retriever=index.vectorstore.as_retriever(),
                                        input_key="question")

    return chain

# Start the server on port 3000


if __name__ == "__main__":
    # documents = getDocuments('files')
    # vectorstore = getVectoreStore(documents)
    # qa = createLangchainQA(vectorstore)

    chain = createIndex("files")
    app.run(port=3000)

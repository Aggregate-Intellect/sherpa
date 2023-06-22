##############################################
#       Importing necessary modules
##############################################

import os
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS 
from langchain.llms import OpenAI
from os import environ
from dotenv import load_dotenv
load_dotenv()
from vectorstores import ConversationStore
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler



# This `app` represents your existing Flask app
app = App(
    token=os.environ.get("SLACK_OAUTH_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

greetings = ["hi", "hello", "hello there", "hey"]


#####################################################################################################
# Setting up environment variables and Slack configuration:
# The code retrieves various environment variables using os.environ.get() method.
# Environment variables include Slack signing secret, OAuth token, verification token, and OpenAI key.
#####################################################################################################

SLACK_SIGNING_SECRET = environ.get("SLACK_SIGNING_SECRET")
SLACK_OAUTH_TOKEN = environ.get("SLACK_OAUTH_TOKEN")
VERIFICATION_TOKEN = environ.get("VERIFICATION_TOKEN")
OPENAI_KEY=environ.get("OPENAI_KEY")



###########################################################################
# Instantiating Slack client and Flask app:
###########################################################################

#instantiating slack client
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi, <@{user_id}>!")

@app.event("app_mention")
def event_test(client, say, event):
    question = event['text']
    question = question.replace('@Sherpa', '').strip()
    results = get_response(question)
    thread_ts = event.get("thread_ts", None) or event["ts"]
    replies = client.conversations_replies(channel=event['channel'], ts=thread_ts)
    print(replies)

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

def get_response(question):
    llm = ChatOpenAI(
        openai_api_key=OPENAI_KEY, request_timeout=120
    )
    retrieval = ConversationStore.from_index(
       'ReadTheDocs', OPENAI_KEY, index_name=os.getenv("PINECONE_INDEX")
    )

    relevant_docs = retrieval.similarity_search(question, top_k=5)
    
    chain = load_qa_chain(llm, chain_type="stuff")
    return chain.run(input_documents=relevant_docs, question=question)

    

# chat_history = []
# @slack_events_adapter.on("app_mention")
# def handle_message(event_data):
#     global chat_history
#     chat_history = []
#     def send_reply(value):
#         event_data = value
#         message = event_data["event"]
#         if message.get("subtype") is None:
#             command = message.get("text")
            
#             print('-------',command)
#             channel_id = message["channel"]
            
#             # C056RU8PEJ0 : llm live project
#             # C059L0UFLR4 : bottest
#             # allowed_channels = ["C056RU8PEJ0", "C059L0UFLR4"]  # Add the desired channel IDs
#             # if channel_id not in allowed_channels:
#             #     print("Not allowed to process")
#             #     return
#             #if any(item in command.lower() for item in greetings):
#             #result = qa({"question": command, "chat_history": []})
#             #message= (result["answer"])
#             message = ("Helloooooooo <@%s>! :tada: I am good how are you" % message["user"] )
            
#             print(message)
#             print(channel_id)
#             global chain
#             message = chain.run(command)
#             print(message)
#             slack_client.chat_postMessage(channel=channel_id, text=message)
#             command = ''
#     thread = Thread(target=send_reply, kwargs={"value": event_data})
#     thread.start()
#     return Response(status=200)


############################################################################

# Get code from John to create index.  Below code is for Experiment
# and not used anywhere

############################################################################


# import getpass
# import pinecone 
# from tqdm.autonotebook import tqdm
# from langchain.text_splitter import CharacterTextSplitter
# from langchain.vectorstores import Pinecone, Chroma
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.chains import ConversationalRetrievalChain
# from langchain.chat_models import ChatOpenAI
# from langchain.document_loaders import DirectoryLoader
# from langchain.llms import OpenAI
# from langchain.vectorstores import Chroma
# from fastapi import FastAPI, File, UploadFile, HTTPException

chatHistory = 0
vectorstore = ''
qa = ''
index_created = 0
# os.environ['OPENAI_API_KEY'] = OPENAI_KEY



#@app.post('/createVectorStore', response_class=ORJSONResponse)
# @app.route("/createVectorStore")
# def createVectorStore(transcript: UploadFile = File(...)):
#     if  transcript.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files are allowed")
           
#     with open(transcript.filename, mode="wb") as new_file:
#         new_file.write(transcript.file.read())
    
#     new_file.close()
#     doc_reader = PdfReader(transcript.filename)    
#     # read data from the file and put them into a variable called raw_text
#     raw_text = ''
#     for i, page in enumerate(doc_reader.pages):
#         text = page.extract_text()
#         if text:
#             raw_text += text            

#     # Splitting up the text into smaller chunks for indexing
#     text_splitter = CharacterTextSplitter(        
#         separator = "\n",
#         chunk_size = 1000,
#         chunk_overlap  = 200, #striding over the text
#         length_function = len,
#     )
#     texts = text_splitter.split_text(raw_text)

#     # Download embeddings from OpenAI
#     embeddings = OpenAIEmbeddings()
#     docsearch = FAISS.from_texts(texts, embeddings)

#     #extracted_list = []
#     chain = load_qa_chain(OpenAI(), 
#                       chain_type="stuff") # we are going to stuff all the docs in at once
    
#     query = "hi"
#     docs = docsearch.similarity_search(query)
#     result = chain.run(input_documents=docs, question=query)    
    
    
#     return result

# def getDocuments(folderName):
    
#     files = folderName +'/'
#     pdf_loader = DirectoryLoader(files, glob="**/*.pdf")
#     readme_loader = DirectoryLoader(files, glob="**/*.md")
#     txt_loader = DirectoryLoader(files, glob="**/*.txt")
#     #take all the loader
#     loaders = [pdf_loader, readme_loader, txt_loader]

#     #lets create document 
#     documents = []
#     for loader in loaders:
#         documents.extend(loader.load())
        
#     print (f'You have {len(documents)} document(s) in your data')
#     print (f'There are {len(documents[0].page_content)} characters in your document')

#     #Split the Text from the documents
#     text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=40) #chunk overlap seems to work better
#     documents = text_splitter.split_documents(documents)
#     print(len(documents))

#     return documents
# #Embeddings and storing it in Vectorestore

# def getVectoreStore(documents):
#     global vectorstore
#     chromaVector = 1
#     pineconeVector = 0
#     loadExistingPineConeIndex = 0
    
#     if chromaVector == 1:
#         embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_KEY)        
#         vectorstore = Chroma.from_documents(documents, embeddings)
#         index_created = 1

#     # pinecone
#     if pineconeVector == 1:
    
#         PINECONE_API_KEY = getpass.getpass('Pinecone API Key:')
#         PINECONE_ENV = getpass.getpass('Pinecone Environment:')

#         # initialize pinecone
#         pinecone.init(
#             api_key=PINECONE_API_KEY,  # find at app.pinecone.io
#             environment=PINECONE_ENV  # next to api key in console
#         )

#         index_name = "langchain-demo"
#         vectorstore = Pinecone.from_documents(documents, embeddings, index_name=index_name)


#         if loadExistingPineConeIndex == 1:

#             # if you already have an index, you can load it like this           

#             # initialize pinecone
#             pinecone.init(
#                 api_key=PINECONE_API_KEY,  # find at app.pinecone.io
#                 environment=PINECONE_ENV  # next to api key in console
#             )

#             index_name = "langchain-demo"
#             vectorstore = Pinecone.from_existing_index(index_name, embeddings)

#     return vectorstore


# def getSimilarDocument(query):
#     global vectorstore
#     query = "Who are the authors of gpt4all paper ?"
#     docs = vectorstore.similarity_search(query)

#     return docs

#     #print(docs[0].page_content)


# def createLangchainQA(vectorstore):
#     global chatHistory,qa
#     retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":2})
#     llm = OpenAI(model_name="gpt-3.5-turbo",openai_api_key=OPENAI_KEY,temperature =0)
#     qa = ConversationalRetrievalChain.from_llm(llm, retriever)
    
#     return qa


###################################################################
## Experiment Add John's code above to create Index
###################################################################

# import shutil
# import atexit
# def cleanup():
#     print("Cleaning up before exit...")
#     if index_created == 1:
#         vectorstore = vectorstore.vectorstore            
#         vectorstore.delete_collection()
#     if os.path.exists('.chroma'):        
#         directory = ".chroma"
#         shutil.rmtree(directory) 
#     # Add your code to be executed here

# atexit.register(cleanup)



##################################################################
#  LLM implementation with Chroma 
##################################################################

from langchain.document_loaders import UnstructuredPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA

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
    #loaders
    documents = []
    for loader in loaders:
        documents.extend(loader.load())
        
    index = VectorstoreIndexCreator(
        embedding=OpenAIEmbeddings(openai_api_key=OPENAI_KEY),
        text_splitter=CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)).from_loaders(loaders)

    llm = OpenAI(model_name="gpt-3.5-turbo",openai_api_key=OPENAI_KEY)#, n=2, best_of=2)
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
    
    # chain = createIndex("files")
    print('Running the app')
    app.start()
    # SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

##############################################
#  Implementation of the slack app using Bolt
#  Importing necessary modules
##############################################

from typing import Dict, List

from flask import Flask, request
from langchain.chat_models import ChatOpenAI
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

import config as cfg
from error_hanlding import AgentErrorHandler
from scrape.prompt_reconstructor import PromptReconstructor
from task_agent import TaskAgent
from tools import get_tools
from utils import log_formatter, show_commands_only
from vectorstores import ConversationStore, LocalChromaStore
from verbose_loggers import DummyVerboseLogger, SlackVerboseLogger
from verbose_loggers.base import BaseVerboseLogger

#######################################################################################
# Set up Slack client and Chroma database
#######################################################################################

app = App(
    token=cfg.SLACK_OAUTH_TOKEN,
    signing_secret=cfg.SLACK_SIGNING_SECRET,
)
bot = app.client.auth_test()
logger.info(f"App init: bot auth_test results {bot}")

if cfg.PINECONE_API_KEY is None:
    logger.info("Setting up local Chroma database")
    local_memory = LocalChromaStore.from_folder(
        "files", cfg.OPENAI_API_KEY
    ).as_retriever()

###########################################################################
# Define Slack client functionality:
###########################################################################


@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi, <@{user_id}>!")


def contains_verbose(query: str) -> bool:
    """looks for -verbose in the question and returns True or False"""
    return "-verbose" in query.lower()


def contains_verbosex(query: str) -> bool:
    """looks for -verbosex in the question and returns True or False"""
    return "-verbosex" in query.lower()


def get_response(
    question: str, previous_messages: List[Dict], verbose_logger: BaseVerboseLogger
):
    llm = ChatOpenAI(
        openai_api_key=cfg.OPENAI_API_KEY, request_timeout=120, temperature=0
    )

    if cfg.PINECONE_API_KEY:
        # If pinecone API is specified, then use the Pinecone Database
        memory = ConversationStore.get_vector_retrieval(
            cfg.PINECONE_NAMESPACE,
            cfg.OPENAI_API_KEY,
            index_name=cfg.PINECONE_INDEX,
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.0},
        )
    else:
        # use the local Chroma database
        memory = local_memory

    tools = get_tools(memory)
    ai_name = "Sherpa"
    ai_id = bot["user_id"]

    task_agent = TaskAgent.from_llm_and_tools(
        ai_name="Sherpa",
        ai_role="assistant",
        ai_id=bot["user_id"],
        memory=memory,
        tools=tools,
        previous_messages=previous_messages,
        llm=llm,
        verbose_logger=verbose_logger,
    )
    error_handler = AgentErrorHandler()

    question = question.replace(f"@{ai_id}", f"@{ai_name}")
    if contains_verbosex(query=question):
        logger.info("Verbose mode is on, show all")
        question = question.replace("-verbose", "")
        response = error_handler.run_with_error_handling(task_agent.run, task=question)
        agent_log = task_agent.logger  # logger is updated after running task_agent.run
        try:  # in case log_formatter fails
            verbose_message = log_formatter(agent_log)
        except KeyError:
            verbose_message = str(agent_log)
        return response, verbose_message

    elif contains_verbose(query=question):
        logger.info("Verbose mode is on, commands only")
        question = question.replace("-verbose", "")
        response = error_handler.run_with_error_handling(task_agent.run, task=question)

        agent_log = task_agent.logger  # logger is updated after running task_agent.run
        try:  # in case log_formatter fails
            verbose_message = show_commands_only(agent_log)
        except KeyError:
            verbose_message = str(agent_log)
        return response, verbose_message

    else:
        logger.info("Verbose mode is off")
        response = error_handler.run_with_error_handling(task_agent.run, task=question)
        return response, None


@app.event("app_mention")
def event_test(client, say, event):
    question = event["text"]
    thread_ts = event.get("thread_ts", None) or event["ts"]
    replies = client.conversations_replies(channel=event["channel"], ts=thread_ts)
    previous_messages = replies["messages"][:-1]

    # check if the verbose is on
    verbose_on = contains_verbose(question)
    verbose_logger = (
        SlackVerboseLogger(say, thread_ts) if verbose_on else DummyVerboseLogger()
    )

    # used to reconstruct the question. if the question contains a link recreate
    # them so that they contain scraped and summarized content of the link
    reconstructor = PromptReconstructor(
        question=question, slack_message=[replies["messages"][-1]]
    )
    question = reconstructor.reconstruct_prompt()
    results, _ = get_response(question, previous_messages, verbose_logger)

    say(results, thread_ts=thread_ts)


@app.event("app_home_opened")
def update_home_tab(client, event):
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
                            "text": "*Welcome to your _App's Home_* :tada:",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Example button.",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Click me!"},
                            }
                        ],
                    },
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


###########################################################################
# Setup Flask app:
###########################################################################
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

if cfg.FLASK_DEBUG:

    @flask_app.route("/test_debug", methods=["GET"])
    def test_debug():
        raise


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/hello", methods=["GET"])
def hello():
    return "OK"


# Start the HTTP server
if __name__ == "__main__":
    # documents = getDocuments('files')
    # vectorstore = getVectoreStore(documents)
    # qa = createLangchainQA(vectorstore)

    # chain = createIndex("files")
    logger.info(
        "App init: starting HTTP server on port {port}".format(port=cfg.SLACK_PORT)
    )
    flask_app.run(host="0.0.0.0", port=cfg.SLACK_PORT, debug=cfg.FLASK_DEBUG)
    # SocketModeHandler(app, cfg.SLACK_APP_TOKEN).start()

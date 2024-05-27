##############################################
#  Implementation of the slack app using Bolt
#  Importing necessary modules
##############################################

import time
from typing import Dict, List, Optional

from flask import Flask, request
from langchain.schema import AIMessage, BaseMessage, HumanMessage
from loguru import logger
from omegaconf import OmegaConf
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slackapp.routes.whitelist import whitelist_blueprint
from slackapp.utils import get_qa_agent_from_config_file

import sherpa_ai.config as cfg
from sherpa_ai.agents import QAAgent
from sherpa_ai.config import AgentConfig
from sherpa_ai.connectors.vectorstores import get_vectordb
from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.error_handling import AgentErrorHandler
from sherpa_ai.events import EventType
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.post_processors import md_link_to_slack
from sherpa_ai.scrape.file_scraper import QuestionWithFileHandler
from sherpa_ai.scrape.prompt_reconstructor import PromptReconstructor
from sherpa_ai.task_agent import TaskAgent
from sherpa_ai.tools import get_tools
from sherpa_ai.utils import count_string_tokens, log_formatter, show_commands_only
from sherpa_ai.verbose_loggers import DummyVerboseLogger, SlackVerboseLogger
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger


#######################################################################################
# Set up Slack client and Chroma database
#######################################################################################

app = App(
    token=cfg.SLACK_OAUTH_TOKEN,
    signing_secret=cfg.SLACK_SIGNING_SECRET,
)
bot = app.client.auth_test()
ai_name = "Sherpa"
logger.info(f"App init: bot auth_test results {bot}")


###########################################################################
# usage tracker database downloader on every deployment:
###########################################################################
def before_first_request():
    usage_db = UserUsageTracker(db_name=cfg.DB_NAME)
    usage_db.download_from_s3()


if not cfg.FLASK_DEBUG:
    before_first_request()

###########################################################################
# Define Slack client functionality:
###########################################################################


@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi, <@{user_id}>!")


def convert_thread_history_messages(messages: List[dict]) -> List[BaseMessage]:
    results = []

    ai_id = bot["user_id"]
    for message in messages:
        logger.info(message)
        if message["type"] != "message" and message["type"] != "text":
            continue

        message_cls = AIMessage if message["user"] == ai_id else HumanMessage
        # replace the at in the message with the name of the bot
        text = message["text"].replace(f"@{ai_id}", f"@{ai_name}")

        text = text.split("#verbose", 1)[0]  # remove everything after #verbose
        text = text.replace("-verbose", "")  # remove -verbose if it exists
        results.append(message_cls(content=text))

    return results


def get_response(
    question: str,
    previous_messages: List[BaseMessage],
    verbose_logger: BaseVerboseLogger,
    bot_info: Dict[str, str],
    llm=None,
    user_id: Optional[str] = None,
) -> str:
    """
    Get a response from the task agent for the question.

    Args:
        question (str): The question to be answered.
        previous_messages (List[BaseMessage]): The previous messages in the thread.
        verbose_logger (BaseVerboseLogger): The verbose logger to be used.
        bot_info (Dict[str, str]): Information of the Slack bot.
        llm (SherpaChatOpenAI, optional): The LLM to be used. Defaults to None.
        user_id (str, optional): The team ID combined with the user ID of the Slack user, so that it can be a globally unique value for the usage tracker. Defaults to "".

    Returns:
        str: The response from the task agent.
    """
    ai_id = bot_info["user_id"]
    question, agent_config = AgentConfig.from_input(question)
    ai_name = "Sherpa"
    question = question.replace(f"@{ai_id}", f"@{ai_name}")
    error_handler = AgentErrorHandler()

    if not agent_config.verbose:
        verbose_logger = DummyVerboseLogger()

    memory = get_vectordb()
    tools = get_tools(memory, agent_config)

    if agent_config.use_task_agent:
        llm = SherpaChatOpenAI(
            openai_api_key=cfg.OPENAI_API_KEY,
            user_id=user_id,
            temperature=cfg.TEMPERATURE,
        )

        verbose_logger.log("⚠️🤖 Use task agent (obsolete)...")
        task_agent = TaskAgent.from_llm_and_tools(
            ai_name=ai_name,
            ai_role="assistant",
            ai_id=bot_info["user_id"],
            memory=memory,
            tools=tools,
            previous_messages=previous_messages,
            llm=llm,
            verbose_logger=verbose_logger,
            agent_config=agent_config,
        )

        response = error_handler.run_with_error_handling(task_agent.run, task=question)
    else:
        agent = get_qa_agent_from_config_file("conf/config.yaml", user_id, llm)
        for message in previous_messages:
            agent.shared_memory.add(EventType.result, message.type, message.content)
        agent.shared_memory.add(EventType.task, "human", question)
        agent.verbose_logger = verbose_logger

        error_handler = AgentErrorHandler()
        response = error_handler.run_with_error_handling(agent.run)
        response = md_link_to_slack(response)

    return response


def file_event_handler(say, files, user_id, thread_ts, question):
    if files[0]["size"] > cfg.FILE_SIZE_LIMIT:
        say(
            "Sorry, the file you attached is larger than 2mb. Please try again with a smaller file",  # noqa E501
            thread_ts=thread_ts,
        )
        return {"status": "error"}
    file_prompt = QuestionWithFileHandler(
        question=question,
        user_id=user_id,
        files=files,
        token=cfg.SLACK_OAUTH_TOKEN,
        llm=llm,
    )
    file_prompt_data = file_prompt.reconstruct_prompt_with_file()
    if file_prompt_data["status"] == "success":
        question = file_prompt_data["data"]
        return {"status": "success", "question": question}
    else:
        say(file_prompt_data["message"], thread_ts=thread_ts)
        return {"status": "error"}


@app.event("app_mention")
def event_test(client, say, event):
    question = event["text"]
    thread_ts = event.get("thread_ts", None) or event["ts"]
    replies = client.conversations_replies(channel=event["channel"], ts=thread_ts)
    previous_messages = replies["messages"][:-1]
    previous_messages = convert_thread_history_messages(previous_messages)

    input_message = replies["messages"][-1]
    slack_user_id = input_message["user"]

    # team_id is found on different places depending on the message from slack
    # if file exist it will be inside one of the files other wise on the parent message
    slack_team_id = (
        input_message["files"][0]["user_team"]
        if "files" in input_message
        else input_message["team"]
    )
    combined_id = slack_user_id + "_" + slack_team_id

    slack_verbose_logger = SlackVerboseLogger(say, thread_ts)
    if cfg.FLASK_DEBUG == True:
        can_execute = True
    else:
        user_db = UserUsageTracker(verbose_logger=slack_verbose_logger)

        usage_checker = user_db.check_usage(
            user_id=combined_id,
            token_amount=count_string_tokens(question, "gpt-3.5-turbo"),
        )

        can_execute = usage_checker["can_execute"]
        user_db.close_connection()

    # only will be executed if the user don't pass the daily limit
    # the daily limit is calculated based on the user's usage in a workspace
    # users with a daily limitation can be allowed to use in a different workspace
    llm = SherpaChatOpenAI(
        openai_api_key=cfg.OPENAI_API_KEY,
        user_id=user_id,
        team_id=team_id,
        temperature=cfg.TEMPERATURE,
    )

    if can_execute:
        if "files" in event:
            files = event["files"]
            file_event = file_event_handler(
                files=files,
                say=say,
                thread_ts=thread_ts,
                user_id=combined_id,
                question=question,
                llm=llm,
            )
            if file_event["status"] == "error":
                return
            else:
                question = file_event["question"]
        else:
            # used to reconstruct the question. if the question contains a link recreate
            # them so that they contain scraped and summarized content of the link
            reconstructor = PromptReconstructor(
                question=question, slack_message=[replies["messages"][-1]]
            )
            question = reconstructor.reconstruct_prompt(user_id=combined_id)

        results = get_response(
            question,
            previous_messages,
            verbose_logger=slack_verbose_logger,
            bot_info=bot,
            user_id=combined_id,
        )

        say(results, thread_ts=thread_ts)
    else:
        say(
            f"""I'm sorry for any inconvenience, but it appears you've gone over your daily token limit. Don't worry, you'll be able to use our service again in approximately {usage_checker['time_left']}.Thank you for your patience and understanding.""",  # noqa E501
            thread_ts=thread_ts,
        )


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
flask_app.register_blueprint(whitelist_blueprint, url_prefix="/auth")


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


def main():
    logger.info(
        "App init: starting HTTP server on port {port}".format(port=cfg.SLACK_PORT)
    )
    # SECURITY host "0.0.0.0" tells Flask to listen on all available IP addresses.
    # This is handy for development, but unsafe in production.
    # See https://bandit.readthedocs.io/en/1.7.8/plugins/b104_hardcoded_bind_all_interfaces.html.
    # In production you would typically place the Flask server behind a WSGI
    # server like Gunicorn and a reverse proxy, and implement other security measures.
    flask_app.run(
        host="0.0.0.0", port=cfg.SLACK_PORT, debug=cfg.FLASK_DEBUG  # nosec B104
    )


# Start the HTTP server
if __name__ == "__main__":
    main()

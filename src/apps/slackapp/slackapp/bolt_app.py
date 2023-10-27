##############################################
#  Implementation of the slack app using Bolt
#  Importing necessary modules
##############################################

import time
from typing import Dict, List

from flask import Flask, request
from langchain.schema import AIMessage, BaseMessage, HumanMessage
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slackapp.routes.whitelist import whitelist_blueprint

import sherpa_ai.config as cfg
from sherpa_ai.config import AgentConfig
from sherpa_ai.connectors.vectorstores import get_vectordb
from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.error_handling import AgentErrorHandler
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
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
logger.info(f"App init: bot auth_test results {bot}")

###########################################################################
# Define Slack client functionality:
###########################################################################


@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi, <@{user_id}>!")


def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
    results = []

    for message in messages:
        logger.info(message)
        if message["type"] != "message" and message["type"] != "text":
            continue

        message_cls = AIMessage if message["user"] == self.ai_id else HumanMessage
        # replace the at in the message with the name of the bot
        text = message["text"].replace(f"@{self.ai_id}", f"@{self.ai_name}")
        # added by JF
        text = text.split("#verbose", 1)[0]  # remove everything after #verbose
        text = text.replace("-verbose", "")  # remove -verbose if it exists
        results.append(message_cls(content=text))

    return results


def get_response(
    question: str,
    previous_messages: List[BaseMessage],
    user_id: str,
    team_id: str,
    verbose_logger: BaseVerboseLogger,
    bot_dict: Dict[str, str]
):
    llm = SherpaChatOpenAI(
        openai_api_key=cfg.OPENAI_API_KEY,
        request_timeout=120,
        user_id=user_id,
        team_id=team_id,
        temperature=cfg.TEMPRATURE,
    )

    memory = get_vectordb()

    question, agent_config = AgentConfig.from_input(question)
    # check if the verbose is on
    verbose_logger = verbose_logger if agent_config.verbose else DummyVerboseLogger()

    tools = get_tools(memory)
    ai_name = "Sherpa"
    ai_id = bot_dict["user_id"]

    task_agent = TaskAgent.from_llm_and_tools(
        ai_name="Sherpa",
        ai_role="assistant",
        ai_id=bot_dict["user_id"],
        memory=memory,
        tools=tools,
        previous_messages=previous_messages,
        llm=llm,
        verbose_logger=verbose_logger,
    )
    error_handler = AgentErrorHandler()

    question = question.replace(f"@{ai_id}", f"@{ai_name}")
    response = error_handler.run_with_error_handling(task_agent.run, task=question)

    return response


@app.event("app_mention")
def event_test(client, say, event):
    question = event["text"]
    thread_ts = event.get("thread_ts", None) or event["ts"]
    replies = client.conversations_replies(channel=event["channel"], ts=thread_ts)
    previous_messages = replies["messages"][:-1]
    previous_messages = process_chat_history(previous_messages)

    input_message = replies["messages"][-1]
    user_id = input_message["user"]
    team_id = input_message["team"]
    combined_id = user_id + "_" + team_id

    if cfg.FLASK_DEBUG:
        can_excute = True
    else:
        user_db = UserUsageTracker(max_daily_token=cfg.DAILY_TOKEN_LIMIT)

        usage_cheker = user_db.check_usage(
            user_id=user_id,
            combined_id=combined_id,
            token_ammount=count_string_tokens(question, "gpt-3.5-turbo"),
        )
        can_excute = usage_cheker["can_excute"]
        user_db.close_connection()

    # only will be excuted if the user don't pass the daily limit
    # the daily limit is calculated based on the user's usage in a workspace
    # users with a daily limitation can be allowed to use in a different workspace

    if can_excute:
        # used to reconstruct the question. if the question contains a link recreate
        # them so that they contain scraped and summarized content of the link
        reconstructor = PromptReconstructor(
            question=question, slack_message=[replies["messages"][-1]]
        )
        question = reconstructor.reconstruct_prompt()
        results, _ = get_response(
            question,
            previous_messages,
            user_id,
            team_id,
            verbose_logger=SlackVerboseLogger(say, thread_ts),
            bot_dict=bot,
        )

        say(results, thread_ts=thread_ts)
    else:
        say(
            f"""I'm sorry for any inconvenience, but it appears you've gone over your daily token limit. Don't worry, you'll be able to use our service again in approximately {usage_cheker['time_left']}.Thank you for your patience and understanding.""",
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
    flask_app.run(host="0.0.0.0", port=cfg.SLACK_PORT, debug=cfg.FLASK_DEBUG)


# Start the HTTP server
if __name__ == "__main__":
    main()

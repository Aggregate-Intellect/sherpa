##############################################
#  Implementation of the slack app using Bolt
#  Importing necessary modules
##############################################

from loguru import logger

from flask import Flask, request
from langchain.chat_models import ChatOpenAI
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

import config as cfg
from scrape.prompt_reconstructor import PromptReconstructor
from task_agent import TaskAgent
from tools import get_tools
from vectorstores import ConversationStore, LocalChromaStore

VERBOSE_DEFAULT = True  # set the verbose default behaviour

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


def get_response(question, previous_messages):
    llm = ChatOpenAI(openai_api_key=cfg.OPENAI_API_KEY, request_timeout=120)

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
    )

    if contains_verbosex(query=question):
        logger.info("Verbose mode is on, show all")
        question = question.replace(f"@{ai_id}", f"@{ai_name}")
        question = question.replace("-verbose", "")
        response = task_agent.run(question)
        agent_log = (
            task_agent.logger
        )  # logger is updated after running task_agent.run(question)
        try:  # in case log_formatter fails
            verbose_message = log_formatter(agent_log)
        except:
            verbose_message = str(agent_log)
        return response, verbose_message

    elif contains_verbose(query=question):
        logger.info("Verbose mode is on, commands only")
        question = question.replace(f"@{ai_id}", f"@{ai_name}")
        question = question.replace("-verbose", "")
        response = task_agent.run(question)
        agent_log = (
            task_agent.logger
        )  # logger is updated after running task_agent.run(question)
        try:  # in case log_formatter fails
            verbose_message = show_commands_only(agent_log)
        except:
            verbose_message = str(agent_log)
        return response, verbose_message

    else:
        logger.info("Verbose mode is off")
        question = question.replace(f"@{ai_id}", f"@{ai_name}")
        response = task_agent.run(question)
        return response, None

def initialize_task_agent(question, previous_messages):
    # This function copeis first section of get_response() and returns task_agent object
    llm = ChatOpenAI(openai_api_key=cfg.OPENAI_API_KEY, request_timeout=120)

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

    task_agent = TaskAgent.from_llm_and_tools(
        ai_name="Sherpa",
        ai_role="assistant",
        ai_id=bot["user_id"],
        memory=memory,
        tools=tools,
        previous_messages=previous_messages,
        llm=llm,
    )

    return task_agent

def question_reformat(question):
    # removes unnecessary words from question, like "-verbose" or "@Sherpa"
    ai_name = "Sherpa"
    ai_id = bot["user_id"]
    question = question.replace(f"@{ai_id}", f"@{ai_name}")
    question = question.replace("-verbose", "")
    question = question.replace("-verbosex", "")
    return question

@app.event("app_mention")
def event_test(client, say, event):
    question = event["text"]
    thread_ts = event.get("thread_ts", None) or event["ts"]
    replies = client.conversations_replies(channel=event["channel"], ts=thread_ts)
    previous_messages = replies["messages"][:-1]

    # used to reconstruct the question. if the question contains a link recreate
    # them so that they contain scraped and summarized content of the link
    reconstructor = PromptReconstructor(
        question=question, slack_message=[replies["messages"][-1]]
    )
    question = reconstructor.reconstruct_prompt()

    question_cleaned = question_reformat(question)
    task_agent = initialize_task_agent(question, previous_messages)

    if VERBOSE_DEFAULT: # Change this to false to revert back
        say("💡Sherpa is thinking... ", thread_ts= thread_ts)
        while True: 
            logging.info(f"Loop_count ==> {task_agent.loop_count}")
            logging.info("Calling --> loop_chain_run")

            assistant_reply = task_agent.loop_chain_run(question_cleaned)

            task_agent.update_logger(assistant_reply)

            log = task_agent.logger[task_agent.loop_count]

            if isinstance(log, dict):  # check if log is dictionary
                try:
                    command_json = log["reply"]["command"]
                except Exception as e:
                    print(f"Error in parsing log: {e}")
                    logging.error(
                        f"Try parsing log with `log['reply']['command']` \n Error: {e}"
                    )
            else:
                command_json = json.loads(log["reply"]["command"])

            # triggered when agent finished thought process before reaching max iterations
            if command_json["name"] == "finish" or "response" in command_json["args"]:
                logging.info("Thought Process Finished!")
                logging.debug(f"{command_json = }") # set logging level to DEBUG to see
                say("```Thought process finished```", thread_ts=thread_ts)
                task_agent.loop_count = task_agent.max_iterations
            else:
                try:
                    # formats the message neatly for user
                    toolname = str(command_json["name"])
                    query = str(command_json["args"]["query"])
                    command_message = (
                        f"\nCommand:\n🛠️Toolname: {toolname} \n❔Query: {query}"
                    )
                    step_counter = log["Step"]
                    verbose_message = (
                        f"```Step: {str(step_counter)} {str(command_message)}```"
                    )
                    logging.debug(verbose_message) # set logging level to DEBUG to see
                    say(verbose_message, thread_ts=thread_ts)
                except Exception as e:
                    # I find this exception never gets triggered
                    print(f"\nError in parsing log: {e}")
                    logging.error(f"Error in parsing log: {e}")

            result = ""  # This line is necessary, but I don't understand why >.<
            
            # this is triggered if the loop reaches max iteration
            if task_agent.loop_count >= task_agent.max_iterations:
                logging.debug("Calling --> Last Chain run")
                say(task_agent.last_chain_run(question_cleaned), thread_ts=thread_ts)
                break

            logging.info("Calling --> reformulate_actions")
            action = task_agent.reformulate_action(question_cleaned, assistant_reply)
            logging.info("Calling --> observations_from_actions")
            result = task_agent.observations_from_actions(action)
            task_agent.save_previous_messages(assistant_reply, result)

            task_agent.loop_count += 1

    else:
        response = task_agent.run(question_cleaned)
        say(response, thread_ts=thread_ts)

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
                            "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app.",
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


# ---- add this for verbose output --- #


def log_formatter(logs):
    """Formats the logger into readable string"""
    log_strings = []
    for log in logs:
        reply = log["reply"]
        if "thoughts" in reply:
            # reply = json.loads(reply)
            formatted_reply = (
                f"""-- Step: {log["Step"]} -- \nThoughts: \n {reply["thoughts"]} """
            )

            if "command" in reply:  # add command if it exists
                formatted_reply += f"""\nCommand: \n {reply["command"]}"""

            log_strings.append(formatted_reply)

        else:  # for final response
            formatted_reply = (
                f"""-- Step: {log["Step"]} -- \nFinal Response: \n {reply}"""
            )
            log_strings.append(formatted_reply)

    log_string = "\n".join(log_strings)
    return log_string


def show_commands_only(logs):
    """Modified version of log_formatter that only shows commands"""
    log_strings = []
    for log in logs:
        reply = log["reply"]
        if "command" in reply:
            # reply = json.loads(reply)
            formatted_reply = (
                f"""-- Step: {log["Step"]} -- \nCommand: \n {reply["command"]}"""
            )
            log_strings.append(formatted_reply)
        else:  # for final response
            formatted_reply = (
                f"""-- Step: {log["Step"]} -- \nFinal Response: \n {reply}"""
            )
            log_strings.append(formatted_reply)
    log_string = "\n".join(log_strings)
    return log_string

# llmlivebook

# Chatbot with Flask and Slack

This repository contains a chatbot implementation using Flask and Slack. The chatbot leverages the Langchain library for question-answering and text processing tasks.

## Features

- Receives events from Slack using SlackEventAdapter.
- Handles app mentions and responds with a message.
- Implements a conversational retrieval chain for question-answering.
- Integrates with OpenAI GPT-3.5 Turbo for language modeling.
- Utilizes Flask and FastAPI frameworks for building the web server.

## Preparation

1. Clone the repository:

   ```bash
   git clone <repository_url>

2.  Create new app in slack workspace by following the [setup tutorial](../../docs/Tutorials/slackbot.rst)
    
3.   Configuration: before running the code, make sure to configure all mandatory environment variables described in the 
    [setup tutorial](../../docs/Tutorials/slackbot.rst). 

4.  Add all the files which you want indexed to the `files` folder. Currently, this app can index `PDFs` and `Markdown` files. (Ignore this step if you connect with your Pinecone database instead.)

## Usage
### Run with Virtual Environment
1. Install [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) or [miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. Create a new conda environment:

   ```bash
   conda create -n slackbot python=3.9
   ```
3. Activate the environment:

   ```bash
    conda activate slackbot
    ```
4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```
5. Run the server:

   ```bash
    python bolt_app.py
    ```

### Run with docker
1.  Run the docker image:
    ```
    docker build -it slackbot .
    docker run -p 3000:3000 slackbot
    ```
2.  Expose the server to the internet using a tool like ngrok. (This step is not required if you are hosting the app on a public IP address.)

3.  Set up the Slack app's Event Subscriptions and provide the ngrok URL as the Request URL.
    * **NOTE:** When adding the url to the Slack app, make sure to append `/slack/events` at the end as this is the default path used by Slack Bolt.

## Development

### Linting and formating
This project uses `flake8` for linting, `black` and `isort` for formatting, and `pytest` for testing. To install the dependencies, run:

```bash
pip install -r dev-requirements.txt
```

To format the project, run:

```bash
make format
```

if you don't have `make` installed, you can also run the following commands:

```bash
black .
isort .
```

To lint the project, run:

```bash
make lint
```

if you don't have `make` installed, you can also run the following commands:

```bash
flake8 .
```

### Testing
To run the tests, run:

```bash
make test
```

or 

```bash
pytest .
```

### Debugging
The Slackbot is built with Flask, which provides a built-in web server and debugger suitable for development use.

When Flask debug mode is enabled, ...
- the server automatically reloads when code is changed
- http://localhost:3000/ serves a web-based debugger which displays an interactive stack trace when an exception is raised
- http://localhost:3000/test_debug raises an exception so you can try out the debugger
- http://localhost:3000/console displays a web-based console where you can execute Python expressions in the context of the application
- stack traces are also displayed in your terminal console

When Flask debug mode is disabled, ...
- you must manually restart the server to pick up code changes
- the web-based debugger and console are not available
- stack traces are only displayed in your terminal console

To enable debug mode, set `FLASK_DEBUG` to `True` in your `.env` file.
To disable debug mode, comment out `FLASK_DEBUG` or set it to any value other than `True`.

**Warning:**
Never use the development server or enable the debugger when deploying to production.
These tools are intended for use only during local development, and are not designed to
be particularly efficient, stable, or secure.

For more info on the debugger see [Werkzeug: Debugging Applications](https://werkzeug.palletsprojects.com/en/2.3.x/debug/#)
and [Flask: Debugging Application Errors](https://flask.palletsprojects.com/en/2.3.x/debugging/).

# Reference
4.  Start interacting with the chatbot by mentioning the app in a Slack channel.



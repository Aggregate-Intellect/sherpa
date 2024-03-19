# Sherpa as a Question Answering

This is a demo project of creating a simple question answering system using Sherpa， using GPT3.5 as the LLM and Google Search to search for information. See `qa.yaml` for detailed configuration.

## Usage
First, install Sherpa and its dependencies. 

Create an environment file (`.env`) similar to the one used for Sherpa. It must include the following items:
```
OPENAI_API_KEY= # Your OpenAI API key
SERPER_API_KEY= # Your Serper API key (Used to connect to Google Search)
```

Then, run the following command to start the question answering system:
```bash
python demo.py --config qa.yaml
```

Enjoy!
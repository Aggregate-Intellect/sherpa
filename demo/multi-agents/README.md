# Example on Multi-Agent Environment

This is an example of how to use the multi-agent environment of `Sherpa` using the SharedMemory and Runtime. 

## Execution
To run the example, first create a `.env` file in the folder, then add the following environment variables:

```bash
# For Google Search
SERPER_API_KEY=<your_serper_api_key>

# For LLMs
OPENAI_API_KEY=<your_openai_api_key>
```

Then, run the following command:

```bash
python main.py
```

To customize the LLMs used, change the `llms` in `main.py`.
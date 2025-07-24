import asyncio
import os
from argparse import ArgumentParser

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from sherpa_ai.actions.github import GithubAction
from sherpa_ai.actions.linear import LinearAction
from sherpa_ai.agents.mcp_agent import McpAgent


async def main():
    load_dotenv()
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="demo/mcp_agent/config.yaml")
    args = parser.parse_args()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    llm = ChatOpenAI(
        model_name="gpt-4", temperature=0, api_key=openai_api_key
    )

    linear_action = LinearAction(llm=llm, name="Linear Action")
    github_action = GithubAction(
        llm=llm, name="Github Action", linear_action=linear_action
    )

    agent = McpAgent(llm=llm, actions=[github_action, linear_action])

    # Connect to the MCP servers
    await github_action.connect_to_server("/Users/job/Desktop/mcp-servers/github-mcp-server.sh")
    await linear_action.connect_to_server()

    prompt = "Analyze the pull requests in the repository 'sherpa-ai/sherpa-ai'."
    result = await agent.run(prompt)
    print(result)

    await github_action.close()
    await linear_action.close()


if __name__ == "__main__":
    asyncio.run(main()) 
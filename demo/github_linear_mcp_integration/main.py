import asyncio
import os
from argparse import ArgumentParser

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from sherpa_ai.mcp.sherpa_mcp_adapter import MCPServerToolsToSherpaActions
from sherpa_ai.agents.pr_analyzer_agent import PRAnalyzerAgent

async def main():
    load_dotenv()
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="demo/github_linear_mcp_integration/config.yaml")
    args = parser.parse_args()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    llm = ChatOpenAI(
        model_name="gpt-4", temperature=0, api_key=openai_api_key
    )

    # Connect to GitHub MCP server
    github_wrapper = MCPServerToolsToSherpaActions(
        llm=llm,
        server_command="bash",
        server_args=["/Users/job/Desktop/mcp-servers/github-mcp-server.sh"],
    )
    github_actions = await github_wrapper.connect()

    # Connect to Linear MCP server
    linear_wrapper = MCPServerToolsToSherpaActions(
        llm=llm,
        server_command="npx",
        server_args=["-y", "mcp-remote", "https://mcp.linear.app/sse"],
        env=os.environ,
    )
    linear_actions = await linear_wrapper.connect()

    # Combine all actions
    all_actions = github_actions + linear_actions

    agent = PRAnalyzerAgent(llm=llm, actions=all_actions)

    # Run the PR analysis workflow using the agent
    print("Running PR analysis and Linear commenting workflow...")
    result = await agent.analyze_repository_prs(owner="Eyobyb", repo="scrape_Jsonify")
    print(result)

    await github_wrapper.close()
    await linear_wrapper.close()

if __name__ == "__main__":
    asyncio.run(main()) 
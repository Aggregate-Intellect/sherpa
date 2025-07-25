import asyncio
import os
import re
from argparse import ArgumentParser

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from sherpa_ai.mcp.sherpa_mcp_adapter import MCPServerToolsToSherpaActions
from sherpa_ai.agents.mcp_agent import McpAgent


def extract_linear_id(text: str):
    if not text:
        return None
    patterns = [
        r"MCP-(\d+)",
        r"\[MCP-(\d+)\]",
        r"\(MCP-(\d+)\)",
        r"MCP-(\d+):",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"MCP-{match.group(1)}"
    return None

async def pr_analysis_workflow(agent: McpAgent, llm, owner: str, repo: str):
    github_list_prs = "list_pull_requests"
    github_get_pr_files = "get_pull_request_files"
    linear_list_issues = "list_issues"
    linear_create_comment = "create_comment"

    # 1. List PRs
    prs = await agent.run(github_list_prs, owner=owner, repo=repo)
    if not isinstance(prs, list):
        print(f"Error: Unexpected PRs response: {prs}")
        return
    results = []
    for pr in prs:
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_body = pr.get("body", "")
        pr_url = pr.get("html_url", "")
        # 2. Get changed files
        files_content = await agent.run(github_get_pr_files, owner=owner, repo=repo, pull_number=pr_number)
        if isinstance(files_content, list):
            file_changes = [f.get("filename") for f in files_content]
        else:
            file_changes = files_content
        # 3. Run LLM analysis
        llm_prompt = f"""
        You are a code reviewer analyzing a pull request. Generate a helpful comment for the Linear issue based on the PR information.\n\nPR Title: {pr_title}\nPR Description: {pr_body or 'No description provided'}\nChanged Files: {file_changes}\n{f'PR URL: {pr_url}' if pr_url else ''}\n\nPlease provide:\n1. A brief summary of what the PR does\n2. Key files changed and their purpose\n3. Any observations about the scope of changes\n4. Whether the PR seems to address the issue appropriately\n\nKeep the comment professional, constructive, and focused on the technical aspects.\n"""
        llm_response = await llm.ainvoke(llm_prompt)
        comment_body = llm_response.content
        # 4. Extract Linear ID
        linear_id = extract_linear_id(pr_title) or extract_linear_id(pr_body)
        if not linear_id:
            results.append(f"PR #{pr_number}: No Linear ID found.")
            continue
        # 5. Find Linear issue internal ID
        issues = await agent.run(linear_list_issues)
        target_issue = None
        if isinstance(issues, list):
            for issue in issues:
                if issue.get("identifier") == linear_id:
                    target_issue = issue
                    break
        if not target_issue:
            results.append(f"PR #{pr_number}: Linear issue {linear_id} not found.")
            continue
        # 6. Post comment to Linear
        comment_with_pr_ref = f"## PR Update: #{pr_number}\n\n{comment_body}\n\n---\n*This comment was automatically generated based on PR #{pr_number}*"
        comment_result = await agent.run(linear_create_comment, issueId=target_issue.get("id"), body=comment_with_pr_ref)
        results.append(f"PR #{pr_number}: Comment posted to Linear {linear_id}. Result: {comment_result}")
    print("\n".join(results))

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

    agent = McpAgent(llm=llm, actions=all_actions)

    # Run the PR analysis workflow
    print("Running PR analysis and Linear commenting workflow...")
    await pr_analysis_workflow(agent, llm, owner="Eyobyb", repo="scrape_Jsonify")

    await github_wrapper.close()
    await linear_wrapper.close()

if __name__ == "__main__":
    asyncio.run(main()) 
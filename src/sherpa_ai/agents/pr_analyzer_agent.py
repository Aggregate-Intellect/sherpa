import json
import re
from transitions.extensions.asyncio import AsyncMachine
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.models.sherpa_base_chat_model import SherpaBaseChatModel
from sherpa_ai.actions.synthesize import SynthesizeOutput

class PRAnalyzerAgent(BaseAgent):
    """
    An agent specialized for analyzing GitHub pull requests and posting review comments to Linear issues using MCP server tools.

    This agent orchestrates the workflow of:
      - Listing pull requests from a GitHub repository
      - Fetching changed files for each PR
      - Using an LLM to generate review comments
      - Extracting Linear issue IDs from PRs
      - Posting comments to the corresponding Linear issues

    Attributes:
        name (str): The name of the agent.
        description (str): Description of the agent's purpose and capabilities.
        llm (BaseLanguageModel): The language model used by the agent and actions.
        actions (List[AsyncBaseAction]): List of available MCP actions.
        action_map (dict): Mapping from action name to action instance for fast lookup.
        belief (Belief): The agent's internal state and knowledge.
        state_machine (SherpaStateMachine): State machine for managing execution state.

    Example:
        >>> agent = PRAnalyzerAgent(llm, actions)
        >>> result = await agent.analyze_repository_prs(owner="repo_owner", repo="repo_name")
        >>> print(result)
    """
    name: str = "PR Analyzer Agent"
    description: str = "An agent for analyzing GitHub PRs and posting comments to Linear via MCP tools."

    def __init__(self, llm: SherpaBaseChatModel, actions: list = [], **kwargs):
        super().__init__(llm=llm, actions=actions, **kwargs)
        if self.belief is None:
            self.belief = Belief()
        self.state_machine = SherpaStateMachine(
            name="pr_analyzer_agent",
            states=["start"],
            initial="start",
            sm_cls=AsyncMachine,
        )
        self.llm = llm
        for action in actions:
            self.add_action(action)
        self.action_map = {a.name: a for a in actions}

    def add_action(self, action):
        self.state_machine.update_transition(
            trigger=action.name, source="start", dest="start", action=action
        )

    def create_actions(self):
        return self.actions

    def extract_linear_id(self, text: str):
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

    async def analyze_repository_prs(self, owner: str, repo: str) -> str:
        github_list_prs = self.action_map.get("list_pull_requests")
        github_get_pr_files = self.action_map.get("get_pull_request_files")
        linear_list_issues = self.action_map.get("list_issues")
        linear_create_comment = self.action_map.get("create_comment")

        if not (github_list_prs and github_get_pr_files and linear_list_issues and linear_create_comment):
            return "Error: Required MCP actions not found."

        # 1. List PRs
        prs = await github_list_prs.execute(owner=owner, repo=repo)
        if not isinstance(prs, list):
            return f"Error: Unexpected PRs response: {prs}"
        results = []
        for pr in prs:
            pr_number = pr.get("number")
            pr_title = pr.get("title", "")
            pr_body = pr.get("body", "")
            pr_url = pr.get("html_url", "")
            # 2. Get changed files
            files_content = await github_get_pr_files.execute(owner=owner, repo=repo, pull_number=pr_number)
            if isinstance(files_content, list):
                file_changes = [f.get("filename") for f in files_content]
            else:
                file_changes = files_content
            # 3. Run LLM analysis
            llm_prompt = f"""
            You are a code reviewer analyzing a pull request. Generate a helpful comment for the Linear issue based on the PR information.\n\nPR Title: {pr_title}\nPR Description: {pr_body or 'No description provided'}\nChanged Files: {file_changes}\n{f'PR URL: {pr_url}' if pr_url else ''}\n\nPlease provide:\n1. A brief summary of what the PR does\n2. Key files changed and their purpose\n3. Any observations about the scope of changes\n4. Whether the PR seems to address the issue appropriately\n\nKeep the comment professional, constructive, and focused on the technical aspects.\n"""
            llm_response = await self.llm.ainvoke(llm_prompt)
            comment_body = llm_response.content
            # 4. Extract Linear ID
            linear_id = self.extract_linear_id(pr_title) or self.extract_linear_id(pr_body)
            if not linear_id:
                results.append(f"PR #{pr_number}: No Linear ID found.")
                continue
            # 5. Find Linear issue internal ID
            issues = await linear_list_issues.execute()
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
            comment_result = await linear_create_comment.execute(issueId=target_issue.get("id"), body=comment_with_pr_ref)
            results.append(f"PR #{pr_number}: Comment posted to Linear {linear_id}. Result: {comment_result}")
        return "\n".join(results)

    def synthesize_output(self) -> str:
        """Generate the final answer based on the agent's actions and belief state."""
        synthesize_action = SynthesizeOutput(
            role_description=self.description,
            llm=self.llm
        )
        result = synthesize_action.execute(
            self.belief.current_task.content if self.belief.current_task else "",
            self.belief.get_context(self.llm.get_num_tokens) if self.llm else "",
            self.belief.get_internal_history(self.llm.get_num_tokens) if self.llm else "",
        )
        return result 
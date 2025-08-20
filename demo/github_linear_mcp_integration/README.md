# GitHub + Linear MCP Integration Demo

This demo shows how to use Sherpa's general-purpose MCP agent to orchestrate workflows across GitHub and Linear using MCP servers.

## Prerequisites
- Node.js (for MCP servers)
- A GitHub personal access token ([how to get one](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic))

## 1. Start the GitHub MCP Server

You need to run the GitHub MCP server locally. The recommended way is to create a shell script for it:

### Create a Shell Script for the GitHub MCP Server

1. Create a file called `github-mcp-server.sh` (or any name you like):

    ```sh
    touch github-mcp-server.sh
    ```

2. Open the file and paste the following code:

    ```sh
    GITHUB_PERSONAL_ACCESS_TOKEN=<your_token> npx -y @modelcontextprotocol/server-github
    ```

    - Replace `<your_token>` with your GitHub personal access token.

3. Use the path to this `.sh` file in the demo configuration (see `server_args` in `main.py`).

- The server will start and listen for stdio connections.

## 2. Linear MCP Server Authorization

The demo will automatically connect to the Linear MCP server via remote SSE. **The first time you run the demo, you will be prompted to authorize the Linear MCP server in your browser.**

- Follow the instructions in the terminal to complete the OAuth flow for Linear.
- Subsequent runs will use the cached credentials.
- **To remove the authenticated linear mcp server and start over use**:
   ```bash
   rm -rf ~/.mcp-auth
   ```

## 3. Prepare Your Repository and Pull Requests

- **Linear Issue ID Pattern:**
  - The demo expects your Linear issue IDs to follow the pattern `MCP-123` (e.g., `MCP-5`).
  - If your Linear workspace uses a different prefix (e.g., `ABC-123`), **edit the pattern in `pr_analyzer_agent.py` in `extract_linear_id` function to match your workspace's issue ID format**.
- **Pull Request Requirements:**
  - Make sure you have at least one pull request in your repository with a Linear issue ID in the title or description (e.g., `MCP-5: Add new feature`).

## 4. Run the Demo

From the project root, run:

```sh
python demo/github_linear_mcp_integration/main.py
```

- **Repository Configuration:**
  - Update the `owner` and `repo` variables in `main.py` to match your GitHub repository.
- Make sure to update the server path in `main.py` if your GitHub MCP server is in a different location.
- The demo will:
  - Connect to both MCP servers
  - List pull requests in the configured repo
  - Analyze each PR with an LLM
  - Post a comment to the corresponding Linear issue (if found)

## 5. Configuration

- You can change the repository and owner in the `main.py` file.
- The demo expects the GitHub MCP server path to be set in the script (see the `server_args` for the GitHub adapter).
- **Reminder:** If your Linear workspace uses a different issue prefix, update the pattern in `main.py` accordingly.
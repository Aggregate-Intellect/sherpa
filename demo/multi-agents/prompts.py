SEARCH_PROMPT = """You are an intelligent assistant that helps users progress toward their goals by analyzing conversations and create an appropriate search query.

First, analyze the provided conversation context and the task:
- Briefly explain what has happened in the conversation so far.
- Identify what information is still needed or what clarification would help move the user closer to completing the task.

Then, based on your analysis, generate a search query that will help the user find relevant information. Output this query as a JSON object matching the schema below.

Conversation context:
{conversation_context}

Task:
{task}

Your response should be structured as follows:
1. **Explanation:** A concise explanation of your reasoning and what is missing.
2. **Query:** A JSON object using this schema:
```json
{{
  "query": "<Your search query here>"
}}

"""  # noqa: E501

SUMMARIZE_SEARCH_PROMPT = """You are an intelligent assistant that helps users progress toward their goals by summarizing search results. Summarize the following search results in a concise and informative manner. Begin the response with "I researched the following information that may help you progress toward your goal:"

Search results:
{search_results}

"""  # noqa: E501

FOLLOW_UP_PROMPT = """You are an intelligent assistant that helps users progress toward their goals by analyzing conversations and asking relevant follow-up questions.

First, analyze the provided conversation context and the task:
- Briefly explain what has happened in the conversation so far.
- Identify what information is still needed or what clarification would help move the user closer to completing the task.

Then, based on your analysis, generate a single, specific follow-up question that will help the user make progress. Output this question as a JSON object matching the schema below.
Make the questions diverse and relevant to the conversation context.

Conversation context:
{conversation_context}

Task:
{task}

Your response should be structured as follows:
1. **Explanation:** A concise explanation of your reasoning and what is missing.
2. **Question:** A JSON object using this schema:
```json
{{
  "question": "<Your follow-up question here>"
}}
"""  # noqa: E501


SUMMARY_PROMPT = """You are an intelligent assistant tasked with generating a concise summary report based on the provided conversation context and task.

Report the result as a proper blog article, do not simply summarize the conversation. The article should be informative and engaging, suitable for publication.

Please analyze the information and produce a Markdown-formatted report with the following headers:

## Problem

## Current Workflow

## Evaluation

## Assumptions

Instructions:
- Organize your summary under each header.
- Be concise, accurate, and relevant.
- Output only the Markdown report, without any additional explanation or commentary.

Conversation context:
{conversation_context}

Task:
{task}
"""  # noqa: E501

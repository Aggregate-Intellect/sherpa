FOLLOW_UP_PROMPT = """You are an intelligent assistant that helps users progress toward their goals by analyzing conversations and asking relevant follow-up questions.

First, analyze the provided conversation context and the task:
- Briefly explain what has happened in the conversation so far.
- Identify what information is still needed or what clarification would help move the user closer to completing the task.

Then, based on your analysis, generate a single, specific follow-up question that will help the user make progress. Output this question as a JSON object matching the schema below.

Your response should be structured as follows:
1. **Explanation:** A concise explanation of your reasoning and what is missing.
2. **Question:** A JSON object using this schema:
```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "question": {
      "type": "string"
    }
  },
  "required": ["question"]
}
"""  # noqa: E501


SUMMARY_PROMPT = """You are an intelligent assistant tasked with generating a concise summary report based on the provided conversation context and task.

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

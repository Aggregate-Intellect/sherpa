==================
Sherpa AI Concepts
==================

This page introduces the key concepts and terminology used throughout the Sherpa AI framework.

Agents
------

Agents are the core building blocks of Sherpa AI. An agent is a specialized AI component designed to perform specific types of tasks or provide expertise in particular domains. Each agent encapsulates a language model along with the necessary logic to use that model effectively within its designated role.

Policies
--------

Policies govern how agents make decisions and process information. They define the reasoning patterns and interaction strategies agents follow when handling tasks. Different policies implement various approaches to problem-solving, such as the ReAct (Reasoning+Acting) pattern or finite state machine-based workflows. Policies determine the sequence of actions an agent should take to accomplish a goal.

Memory
------

Memory systems provide persistence of information across turns of conversation or between sessions. They allow agents to maintain context, recall previous interactions, and build up knowledge over time. Sherpa AI supports different types of memory systems, including conversation history, vector stores for semantic retrieval, and shared memory across agents.

Models
------

Models are the underlying language models that power agent capabilities. Sherpa AI provides wrappers and interfaces for working with various LLM providers, adding enhanced functionality like logging, error handling, and standardized interaction patterns. Models transform inputs into meaningful outputs based on their training.

Prompts
-------

Prompts are structured inputs that guide language models toward producing desired outputs. The prompts system in Sherpa AI includes template-based generation, variable substitution, and management of prompt collections. Well-designed prompts are crucial for effective agent behavior.

Actions
-------

Actions represent operations that agents can perform to accomplish tasks. These range from information retrieval to computation to external API interactions. Actions extend an agent's capabilities beyond just generating text, allowing it to interact with external systems and data sources.

Tools
-----

Tools are utility functions and interfaces that support agent operations. They provide capabilities like text processing, data manipulation, and other helper functionality. Tools are typically lower-level components that actions can use to achieve their goals.

Connectors
----------

Connectors enable Sherpa AI to interface with external systems and databases. They provide standardized methods for storing and retrieving data from vector databases, document stores, and other persistence mechanisms. 
======================
Sherpa AI Architecture
======================

Architecture Overview
---------------------

Sherpa AI is designed with a modular architecture that enables flexibility and extensibility. The framework consists of several key components that work together to create powerful AI agents and workflows.

.. code-block:: text

   ┌──────────────────────────────────────────────────────────────────────┐
   │                    Sherpa AI Architecture                            │
   └──────────────────────────────────────────────────────────────────────┘

   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   Agents    │    │  Policies   │    │   Memory    │    │   Models    │
   │             │    │             │    │             │    │             │
   │ QA Agent    │    │ React       │    │ Belief &    │    │ LLM         │
   │ User Agent  │    │ Policy      │    │ Shared      │    │ interfaces  │
   └─────┬───────┘    └─────┬───────┘    └─────┬───────┘    └─────┬───────┘
         │                  │                  │                  │
         └──────────────────┼──────────────────┼──────────────────┘
                            │                  │
                            ▼                  ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   Actions   │    │    Tools    │    │ Connectors  │    │   Prompts   │
   │             │    │             │    │             │    │             │
   │ Google      │    │ Search      │    │ Vector      │    │ Template    │
   │ Search      │    │ Tools       │    │ Stores      │    │ system      │
   └─────┬───────┘    └─────┬───────┘    └─────┬───────┘    └─────┬───────┘
         │                  │                  │                  │
         └──────────────────┼──────────────────┼──────────────────┘
                            │
                            ▼
          ┌──────────────┐    ┌─────────────┐
          │Output Parsers│    │    Config   │
          │              │    │             │
          │ Citation     │    │ Agent       │
          │ Validation   │    │ Config      │
          └──────────────┘    └─────────────┘

Components
----------

Agents
~~~~~~

Agents are specialized AI components designed for specific domains or tasks:

.. inheritance-diagram:: sherpa_ai.agents.qa_agent sherpa_ai.agents.user
   :parts: 1
   :caption: Agent Class Hierarchy

Agents build on a common interface while providing specialized functionality for different use cases:

* **QAAgent**: Optimized for question answering
* **Critic**: Evaluates outputs and provides feedback
* **MLEngineer**: Specialized for machine learning tasks

Policies
~~~~~~~~

Policies determine how agents make decisions and process information:

* **ReactPolicy**: Implements the Reasoning+Acting pattern
* **ChatPolicy**: Optimized for conversational interactions
* **State Machine Policies**: Use finite state machines for complex workflows

Memory
~~~~~~

Memory systems provide persistence across sessions and interactions:

* **SharedMemory**: Allows agents to share information
* **ConversationMemory**: Stores conversation history
* **VectorMemory**: Enables semantic retrieval of information

Integration
-----------

The power of Sherpa AI comes from the seamless integration of these components. The following diagram shows how data flows through a typical Sherpa AI application:

.. code-block:: text

                 ┌────────────┐
                 │   Input    │
                 │            │
                 │    User    │
                 │   Query    │
                 └─────┬──────┘
                       │
                       ▼
   ┌────────────────────────────────────────────┐
   │                 Agent                      │
   │                                            │
   │       Orchestrates all components          │
   └───┬───────────────┬──────────────────┬─────┘
       │               │                  │
       ▼               ▼                  ▼
   ┌───────┐      ┌───────────┐     ┌──────────┐
   │ Model │      │ Memory    │     │ Policy   │
   │       │      │           │     │          │
   │ LLM   │      │ Knowledge │     │ Decision │
   └───┬───┘      └───────────┘     └────┬─────┘
       │                                 │
       ▼                                 │
   ┌──────────┐                          │
   │ Prompt   │                          │
   │          │                          │
   │ Generate │                          │
   └────┬─────┘                          │
        │                                │
        ▼                                │
   ┌─────────┐                           │
   │ Actions │◄──────────────────────────┘
   │         │
   │ Execute │
   └────┬────┘
        │
        ▼
   ┌─────────┐
   │ Tools   │
   │         │
   │ Utilize │
   └─────────┘

Sequence Flow
-------------

The sequence diagram below illustrates how a user query flows through the Sherpa AI system:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────────┐
   │                    Sherpa AI Query Flow                         │
   └─────────────────────────────────────────────────────────────────┘

   ┌─────────┐    1. Query     ┌─────────┐    2. Check     ┌─────────┐
   │  User   │ ──────────────► │  Agent  │ ──────────────► │ Memory  │
   │         │                 │         │                 │         │
   │ User    │                 │ QA      │                 │ Mem     │
   │         │                 │ Agent   │                 │ ory     │
   └─────────┘                 └────┬────┘                 └────┬────┘
                                    │                           │
                                    │ 3. Return                 │
                                    │ Context                   │
                                    │ ◄─────────────────────────┘
                                    │
                                    ▼
   ┌─────────┐    4. Apply     ┌─────────┐    5. Select    ┌─────────┐
   │ Policy  │ ◄────────────── │  Agent  │ ──────────────► │ Action  │
   │         │                 │         │                 │         │
   │ React   │                 │ QA      │                 │ Search  │
   │ Policy  │                 │ Agent   │                 │ Action  │
   └─────────┘                 └────┬────┘                 └────┬────┘
                                    │                           │
                                    │ 7. Generate               │
                                    │ Response                  │
                                    │ ◄─────────────────────────┘
                                    │
                                    ▼
   ┌─────────┐    6. Get       ┌─────────┐    8. Final     ┌─────────┐
   │  LLM    │ ◄────────────── │ Action  │ ──────────────► │  User   │
   │         │                 │         │                 │         │
   │ LLM     │                 │ Search  │                 │ User    │
   │         │                 │ Action  │                 │         │
   └─────────┘                 └─────────┘                 └─────────┘

This sequence shows:

1. A user submits a query to the Agent
2. The Agent checks Memory for relevant context
3. The Agent's Policy determines the next action
4. Actions are executed to gather information
5. The Model generates a response based on all inputs
6. The final response is returned to the user 
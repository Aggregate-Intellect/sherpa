====================
Sherpa AI Architecture
====================

Architecture Overview
-------------------

Sherpa AI is designed with a modular architecture that enables flexibility and extensibility. The framework consists of several key components that work together to create powerful AI agents and workflows.

.. graphviz:: _static/architecture.dot
   :caption: **Figure 1**: Sherpa AI Architecture Overview
   :align: center
   :alt: Diagram showing Sherpa AI's component architecture and interactions

Components
---------

Orchestrator
~~~~~~~~~~~

The Orchestrator is the central coordination component of Sherpa AI. It:

* Manages the flow of information between agents
* Coordinates the execution of tasks
* Handles the overall workflow of the system

.. code-block:: python

   from sherpa_ai.orchestrator import Orchestrator
   from sherpa_ai.agents import QAAgent
   
   # Create an orchestrator with an agent
   orchestrator = Orchestrator(agents=[QAAgent()])
   
   # Process user queries
   result = orchestrator.process("How do neural networks work?")

Agents
~~~~~~

Agents are specialized AI components designed for specific domains or tasks:

.. inheritance-diagram:: sherpa_ai.agents.qa_agent sherpa_ai.agents.critic sherpa_ai.agents.ml_engineer
   :parts: 1
   :caption: Agent Class Hierarchy

Agents build on a common interface while providing specialized functionality for different use cases:

* **QAAgent**: Optimized for question answering
* **Critic**: Evaluates outputs and provides feedback
* **MLEngineer**: Specialized for machine learning tasks

Policies
~~~~~~~

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
----------

The power of Sherpa AI comes from the seamless integration of these components. The following diagram shows how data flows through a typical Sherpa AI application:

.. code-block:: text

                    ┌────────────┐
                    │   Input    │
                    └─────┬──────┘
                          │
                          ▼
   ┌───────────────────────────────────────┐
   │             Orchestrator              │
   └───┬───────────────┬──────────────┬────┘
       │               │              │
       ▼               ▼              ▼
   ┌───────┐      ┌────────┐     ┌────────┐
   │ Agent │      │ Memory │     │ Policy │
   └───┬───┘      └────┬───┘     └────┬───┘
       │               │              │
       ▼               │              │
   ┌───────┐           │              │
   │ Model │◄──────────┘              │
   └───┬───┘                          │
       │                              │
       ▼                              │
   ┌───────┐                          │
   │ Prompt│                          │
   └───┬───┘                          │
       │                              │
       ▼                              │
   ┌───────┐                          │
   │Actions│◄─────────────────────────┘
   └───┬───┘
       │
       ▼
   ┌───────┐
   │ Tools │
   └───────┘

Sequence Flow
-------------

The sequence diagram below illustrates how a user query flows through the Sherpa AI system:

.. graphviz:: _static/sequence.dot
   :caption: **Figure 2**: Sherpa AI Query Sequence Flow
   :align: center
   :alt: Diagram showing the sequence of interactions between Sherpa AI components

This sequence shows:

1. A user submits a query to the Orchestrator
2. The Orchestrator routes the query to an appropriate Agent
3. The Agent checks Memory for relevant context
4. The Agent's Policy determines the next action
5. Actions are executed to gather information
6. The Model generates a response based on all inputs
7. The final response is returned to the user through the Orchestrator 
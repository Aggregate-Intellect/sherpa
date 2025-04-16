==================
Sherpa AI Concepts
==================

This page introduces the key concepts and terminology used throughout the Sherpa AI framework. Understanding these concepts is essential for effectively using and extending the framework.

Core Components
--------------

Agents
^^^^^^
Agents are the primary actors in Sherpa AI. They are specialized AI components designed to perform specific tasks or provide expertise in particular domains. Each agent:

* Encapsulates a language model (LLM)
* Has a defined role and description
* Maintains its own belief state
* Can access shared memory
* Follows a policy for decision making
* Can execute a set of actions

Examples include the MLEngineer agent for machine learning tasks and the QAAgent for question-answering tasks.

Policies
^^^^^^^^
Policies govern how agents make decisions. They implement the reasoning patterns and strategies that agents use to select actions. Sherpa AI includes several policy types:

* **ReactPolicy**: Implements the ReAct (Reasoning + Acting) framework
* **ReactStateMachinePolicy**: Extends ReAct with state machine capabilities
* **ChatStateMachinePolicy**: Implements chat-based decision making with state management
* **AgentFeedbackPolicy**: Enables decision making based on feedback from other agents

Each policy type provides different approaches to:

* Action selection
* Context processing
* Response generation
* State management

Actions
^^^^^^^
Actions are concrete operations that agents can perform. They represent the capabilities available to agents and include:

* Information retrieval (e.g., GoogleSearch, ArxivSearch)
* Output synthesis
* Deliberation
* External API interactions

Each action has:

* A unique name
* Required arguments
* Usage description
* Optional belief state access
* Input validation logic

Memory Systems
-------------

Belief
^^^^^^
The Belief system represents an agent's understanding of its current state and context. It includes:

* Current task information
* Action history
* State machine status (if applicable)
* Internal event log
* Context management

Shared Memory
^^^^^^^^^^^^
Shared Memory enables communication and information sharing between agents. It provides:

* Cross-agent data persistence
* Observation mechanisms
* Result storage
* Context sharing

State Management
--------------

State Machines
^^^^^^^^^^^^^
State machines provide structured workflow management for agents. They:

* Define possible states
* Control state transitions
* Include state-specific behaviors
* Guide action selection

Event System
^^^^^^^^^^^
The event system manages the flow of information and state changes:

* Tracks action execution
* Records agent decisions
* Maintains history
* Enables feedback loops

Integration Components
--------------------

Models
^^^^^^
Models represent the underlying language models (LLMs) that power agent capabilities. The framework:

* Supports multiple LLM providers
* Handles response processing
* Manages token usage
* Provides standardized interfaces

Prompts
^^^^^^^
The prompt system manages structured inputs to language models:

* Template-based generation
* Variable substitution
* Version control
* Context formatting

Output Processing
^^^^^^^^^^^^^^^^
Output processors handle and validate agent responses:

* Citation validation
* Response formatting
* Error handling
* Quality checks

Best Practices
-------------

When working with Sherpa AI:

1. **Agent Design**:
   * Define clear agent responsibilities
   * Choose appropriate policies
   * Configure relevant actions

2. **Memory Management**:
   * Use shared memory for cross-agent communication
   * Maintain clean belief states
   * Handle context appropriately

3. **Action Implementation**:
   * Validate inputs thoroughly
   * Handle errors gracefully
   * Document usage clearly

4. **Policy Selection**:
   * Match policy to task requirements
   * Configure appropriate response formats
   * Handle state transitions carefully

For detailed implementation examples and API references, see the :doc:`API Documentation <API_Docs/index>`.
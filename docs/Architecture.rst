=====================
Sherpa AI Architecture
=====================

Overview
--------

Sherpa agents are built from three core, model-driven components:

- **Hierarchical State Machine (SM):** structures a task into states, transitions, guards, and actions.
- **Policy (rule-based or LLM-guided):** selects the next transition/event based on the current state and the agent’s belief.
- **Belief (memory):** maintains the trajectory of taken transitions, an execution log of actions and I/O, and a key-value context used by the policy and actions.

Multiple agents can collaborate by exchanging **events** and by reading/writing **shared memory** (e.g., shared vector or document stores). Each agent also keeps its own private belief.

Multi-Agent View
----------------

The diagram below shows several agents collaborating via events and shared memory.

.. code-block:: text

   ┌───────────────────────────────────────────────────────────────────┐
   │                         Shared Memory                             │
   │       (vector/doc stores; artifacts produced by agents)           │
   └───────────────────────────────────────────────────────────────────┘
                    ▲                                   ▲
                    │                                   │(read / write)
                    │                                   │
      ┌─────────────┴───────────┐         ┌─────────────┴───────────┐     
      │          Agent A        │         │          Agent B        │
      │        (e.g., QA)       │         │      (e.g., Critic)     │
      │                         │         │                         │
      │     ┌─────────────┐     │         │     ┌─────────────┐     │
      │     │ StateMachine│     │         │     │ StateMachine│     │
      │     └─────────────┘     │         │     └─────────────┘     │
      │           │ events      │         │           │ events      │
      │           ▼             │         │           ▼             │
      │     ┌─────────────┐     │         │     ┌─────────────┐     │
      │     │   Policy    │     │         │     │   Policy    │     │
      │     └─────────────┘     │         │     └─────────────┘     │
      │           │ selects     │         │           │ selects     │
      │           ▼             │         │           ▼             │
      │     ┌─────────────┐     │         │     ┌─────────────┐     │
      │     │   Actions   │     │         │     │   Actions   │     │
      │     └─────────────┘     │         │     └─────────────┘     │
      │           │ updates     │         │           │ updates     │
      │           ▼             │         │           ▼             │
      │     ┌─────────────┐     │         │     ┌─────────────┐     │
      │     │   Belief    │     │         │     │   Belief    │     │
      │     │(traj/log/KV)│     │         │     │(traj/log/KV)│     │
      │     └─────────────┘     │         │     └─────────────┘     │
      └─────────────────────────┘         └─────────────────────────┘
                  ▲                                   ▲
                  └───────── events/messages ─────────┘
                              (agent ↔ agent)

Inside a Sherpa Agent
---------------------

An agent’s behavior is governed by its state machine, with decisions made by a policy and all activity recorded in belief.

.. code-block:: text

   ┌──────────────────────────────────────────────────────────────────────┐
   │                            Agent Internals                           │
   └──────────────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────────────┐
   │  Hierarchical State Machine                                          │
   │  • Decomposes the task (states, transitions, guards, actions)        │
   │  • Controls execution flow                                           │
   └──────────────────────────────────────────────────────────────────────┘
                    │ available transitions + current state
                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  Policy                                                              │
   │  • Rule-based: (state, belief) → event                               │
   │  • LLM-guided: prompt includes state + transitions + recent belief   │
   │  • Fast-forward: if only one transition is available, skip selection │
   └──────────────────────────────────────────────────────────────────────┘
                    │ chosen event / parameters
                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  Actions                                                             │
   │  • Typed tool/LLM calls bound to transitions or state entry/exit     │
   │  • External inputs (from user/policy) vs internal (from belief)      │
   └──────────────────────────────────────────────────────────────────────┘
                    │ outputs / updates
                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  Belief                                                              │
   │  • Trajectory Store (states traversed)                               │
   │  • Execution Log (actions and I/O)                                   │
   │  • Key-Value Context (task data)                                     │
   │  • Read-only to the policy; updated by actions and transitions       │
   └──────────────────────────────────────────────────────────────────────┘

Execution Lifecycle
-------------------

Multi-Agent Collaboration
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Task arrival**: a user (or another agent) creates a task and initial event.
2. **Agent selection**: agents subscribe to relevant tasks or are explicitly addressed.
3. **Iteration**: agents exchange events and produce artifacts in **shared memory**.
4. **Review/critique**: peers (e.g., a critic agent) evaluate intermediate results.
5. **Aggregation**: a final response is produced and returned to the user.

Single-Agent Tick
~~~~~~~~~~~~~~~~~

1. **Event** arrives (from a user or another agent).  
2. **State Machine** evaluates guards, fires a transition, and invokes **Actions**.  
3. **Belief** is updated (trajectory, execution log, KV).  
4. **Policy** selects the next event/transition; repeat until an end state or further input is required.

Component Reference
-------------------

Agents
~~~~~~

- Role/profile (goal, constraints, method), **SM**, **Policy**, **Belief**, and **Action** set.
- Human operators can be modeled as agents that send/receive events.

Policies
~~~~~~~~

- **Rule-based**: deterministic mapping from (state, belief) → event.  
- **LLM-guided**: prompt contains *state description*, *available transitions*, and *recent belief*.  
- **Fast-forward**: when only one transition is available, selection is skipped.

Belief (Memory)
~~~~~~~~~~~~~~~

- **Trajectory store** (states traversed)  
- **Execution log** (actions and I/O)  
- **Key-value context** (task data needed by actions and the policy)

Actions & Tools
~~~~~~~~~~~~~~~

- Typed parameters: **external** (from user or policy) vs **internal** (from belief).  
- May call LLMs, retrieval, code evaluators, graph operations, etc.

Shared Memory
~~~~~~~~~~~~~

- A common store for artifacts/results used by multiple agents.  
- Each agent still maintains a **private belief** for its own execution trace.

Design Guidelines
-----------------

- Encode best practices as **hierarchical SMs**; keep actions small and composable.  
- Choose **rule vs LLM policy** per step; prefer rules when transitions are unambiguous.  
- Use **fast-forward** to reduce LLM calls when a single transition is available.  
- Add **inspection/self-critique** states when recall or quality is critical.  
- Tailor SM depth to **model capacity** and **cost** targets.

Glossary
--------

- **State Machine (SM)**: Directed graph of states and transitions with guards/actions.  
- **Policy**: Selector of the next event/transition based on state and belief.  
- **Belief**: Agent memory (trajectory, execution log, KV context).  
- **Action**: Tool or LLM call bound to transitions or state entry/exit.  
- **Shared Memory**: Common store (e.g., vector/doc) that multiple agents can use.  
- **Event**: A trigger that advances the state machine (can come from users or agents).

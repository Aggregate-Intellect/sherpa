LLM Multi-Agent Framework
=========================

RL: an agent is defined as a system that interacts with an environment (including other agents) to achieve specific objectives.
More specifically, an _agent_ can observe the _state_ of the _environment_ and uses its _policy_ to decide what the best next _action_ is to optimize a given _reward_.
In other words, a system is an agent if for any given state of the environment, it has access to multiple plausible actions, and it uses a (potentially learned and evolving) policy to get closer to a pre-determined objective.

arXiv:2308.00352v4
arXiv:2308.10848v1

**Foundational Components Layer** offers an underlying infrastructure for agents to function in assigned roles, interacting with each other and the system.

- **Environment** enables shared workspace and communications.
- **Memory** stores and retrieves historical messages including critical details extracted from environment.
- **Agent Roles** encapsulate domain-specific skills and workflows.
    - _Profile_ embodies the domain expertise of the role or job title.
    - _Goal_ represents the primary responsibility or objective that the role seeks to accomplish. 
    - _Constraints_ denote limitations or principles the role must be followed when performing actions.
    - _Description_ provides additional concrete identity to help establish a more comprehensive role.
    - _Methods_ certain key behaviors comprising workflows:
        - *Reflect* on what needs to be done and decide the next action
        - *Observe* important information from environment and incorporate it in memory 
        - *Broadcast* messages that contain details about current execution results and related action record
        - *Assess* incoming messages for relevancy and timeliness, extract relevant knowledge from messages, and maintain an internal knowledge repository to inform decisions
        - *Act* based on enriched contextual information and self-knowledge
        - *Manage State* of execution by tracking their actions by updating their working status and monitoring a to-do list
- **Actions** execute modular sub-tasks. Actions result in standardized outputs that can be easily used by other parts of the ecosystem (interoperabilty).
- **Tools** provide common services and utilities. 

NOTE: All human operators can be defined as `Agents` with the same set of metadata about them and the same processes of "expert selection" can indicate which operator should be involved in handling specific tasks or decision making.

**Execution Layer**

- **Workflows.** This mechanism leverages "standard operating procedures" to break down complex tasks into smaller, manageable components. It assigns these sub-tasks to suitable agents and supervises their performance by standardized outputs, ensuring that their actions align with the overarching objectives. It also tracks the completion status of tasks.
- **Expert Recruitment.** Selecting the right agents to involve given the current state of the problem-solving progress.
- **Evaluation** - After the execution of actions, this module evaluates the disparities between the current state and the desired goal. If the current state falls short of expectations, a feedback reward will be sent to the first stage, and the group’s composition will be dynamically adjusted to facilitate collaboration in the next round.
    - Comprehensiveness 
    - Detailedness
    - Feasibility
    - Novelty
    - Free format feedback  

**Collaboration Layer** orchestrates individual agents to collaboratively resolve complex problems.

- **Collaborative Decision-Making.** The recruited agents engage in collaborative discussions aimed at formulating strategies to solve the presented problem. Once a consensus is reached, proposed actions are put forth.
- **Action Execution** The agents interact with the environment to execute actions.
- **Knowledge Sharing.** This mechanism allows agents to exchange information effectively, contributing to a shared knowledge base. Agents can store, retrieve, and share data at different levels of granularity. It not only enhances coordination but also reduces redundant communication, increasing overall operational efficiency. This is done through a decentralized and federated knowledge ecosystem similar to how organizations maintain knowledge (central repo and personal views).
    - *Message sharing*. Whenever an agent generates a message, it is replicated to the shared environment log, creating a single source of truth.     This ensures all agents have access to the same information.
    - *Role-based subscriptions*. Agents can register subscriptions based on their roles and the types of messages that are meaningful to them. This is done based on predefined criteria that align with the agent’s responsibilities and tasks.
    - *Message dispatch*. When a new message meets the subscription criteria, it is automatically dispatched to notify the relevant agent. This active dissemination of information prevents agents from missing out on important updates.
    - *Memory caching and indexing*. Agents maintain an internal memory cache where the subscription messages are stored and indexed by their content, senders, and recipients. This allows for efficient information storage and retrieval.
    - *Contextual retrieval*. The environment maintains a shared memory pool that supports caching and indexing. Meanwhile, agents can query their internal memory as needed to obtain contextual details relevant to their current task. This helps in refining their understanding and making better decisions.
    - *Updates synchronization*. Any updates or changes made to the messages are synchronized across all linked agent memories to maintain a consistent view of the information. This ensures that all agents have access to the most up-to-date data.


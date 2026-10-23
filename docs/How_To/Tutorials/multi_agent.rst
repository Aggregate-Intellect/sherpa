Asynchronous Execution and Multi-Agent
======================================

Overview
--------

The ``ThreadedRuntime`` module wraps an agent in a Pykka actor so events can be handled in a separate thread. The examples below use a minimal agent with no actions, so they demonstrate event routing without calling an LLM or another external service. Replace it with an appropriately configured agent when your application needs model-backed actions.

.. code-block:: python

    from sherpa_ai.agents.base import BaseAgent
    from sherpa_ai.memory import Belief

    class MessageAgent(BaseAgent):
        def create_actions(self):
            return []

        def synthesize_output(self):
            return ""

    def make_agent(name, shared_memory=None):
        return MessageAgent(
            name=name,
            description="Receives messages without running model-backed actions.",
            belief=Belief(),
            shared_memory=shared_memory,
        )

ThreadedRuntime Usage
---------------------

Starting the Runtime
~~~~~~~~~~~~~~~~~~~~

Start a runtime around an agent with ``ThreadedRuntime.start()``:

.. code-block:: python

    from sherpa_ai.runtime import ThreadedRuntime

    agent = make_agent("receiver")
    runtime = ThreadedRuntime.start(agent=agent)

Sending Events
~~~~~~~~~~~~~~

Create a generic message event with ``build_event()`` and send it to the runtime. A non-blocking ``ask()`` returns a future; call ``get()`` when you need the result of that event before continuing.

.. code-block:: python

    from sherpa_ai.events import build_event

    event = build_event(
        "message", "input_message", sender="user", content="Hello, agent!"
    )
    future = runtime.ask(event, block=False)
    result = future.get()

Always stop the runtime when finished:

.. code-block:: python

    runtime.stop()

Multi-Agent Communication
-------------------------

``SharedMemory`` can route an event to subscribed runtimes. Subscribe the recipient (here, ``agent2_runtime``), not the sender. ``async_add()`` is asynchronous, so call it from an async function or use the synchronous ``add()`` method.

.. code-block:: python

    import asyncio

    from sherpa_ai.memory import SharedMemory
    from sherpa_ai.runtime import ThreadedRuntime

    shared_memory = SharedMemory()
    agent1 = make_agent("agent1", shared_memory)
    agent2 = make_agent("agent2", shared_memory)
    agent1_runtime = ThreadedRuntime.start(agent=agent1)
    agent2_runtime = ThreadedRuntime.start(agent=agent2)

    # Route messages from agent1 to agent2. Either subscription is sufficient;
    # if both are present, SharedMemory deduplicates the recipient.
    shared_memory.subscribe_event_type("message", agent2_runtime)
    shared_memory.subscribe_sender("agent1", agent2_runtime)

    async def send_message():
        await shared_memory.async_add(
            "message",
            "greeting",
            sender="agent1",
            content="Hello, agent2!",
            wait=True,
        )

    try:
        asyncio.run(send_message())
    finally:
        agent1_runtime.stop()
        agent2_runtime.stop()

``wait=True`` waits for subscribed runtimes to handle that event. Do not use ``agent_runtime.proxy().wait()`` as a queue-drain signal: the current ``ThreadedRuntime.wait()`` implementation returns immediately. For a direct ``runtime.ask(event, block=False)``, use the returned future's ``get()`` method.

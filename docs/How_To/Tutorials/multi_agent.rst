Asynchronous Execution and Multi-Agent
=============================

Overview
--------

The ``ThreadedRuntime`` module provides an asynchronous execution environment for agents, allowing them to process events concurrently in a separate thread. This runtime enables non-blocking communication with agents and handles the execution lifecycle automatically.

ThreadedRuntime Usage
-----------

Starting the Runtime
~~~~~~~~~~~~~~~~~~~~

To enable asynchronous execution, you need to wrap the agent in a ``ThreadedRuntime``. This runtime manages the agent's lifecycle and allows it to process events in a separate thread.
The ``ThreadedRuntime`` is started using the static ``start()`` method:

.. code-block:: python

    from sherpa_ai.runtime import ThreadedRuntime
    from sherpa_ai.agents import QAAgent
    from sherpa_ai.memory import Belief
    
    # Create your agent
    belief = Belief()
    agent = QAAgent(belief=belief)
    
    # Start the runtime
    runtime = ThreadedRuntime.start(agent=agent)

Sending Events
~~~~~~~~~~~~~~
``Events`` are built-in data structures that represent messages or tasks sent to the agent. You can create events using the ``build_event()`` function from the ``sherpa_ai.events`` module.
Events are sent to the runtime using the ``ask()`` method. If non-blocking, the method returns a ``Future`` object that can be used to retrieve the result later.

.. code-block:: python

    from sherpa_ai.events import build_event
    
    # Create an event
    event = build_event("message", "input_message", content="Hello, agent!")
    
    # Send event asynchronously
    future = runtime.ask(event, block=False)
    
    # Some other processing can happen here while the agent processes the event

    # Wait and get the result
    result = future.get()

Stopping the Runtime
~~~~~~~~~~~~~~~~~~~~

Always stop the runtime when finished to clean up resources:

.. code-block:: python

    runtime.stop()

Multi-Agent Communication
-------------------------
Sending an event directly to an agent is straightforward. However, if many agents exist, it will be difficult to manage all point-to-point communication. Instead, Sherpa provides a ``SharedMemory`` that allows agents to communicate indirectly through a shared space.

.. code-block:: python

    from sherpa_ai.runtime import ThreadedRuntime
    from sherpa_ai.agents import QAAgent
    from sherpa_ai.memory import Belief
    from sherpa_ai.memory import SharedMemory
    
    # Create your agent
    belief = Belief()
    agent1 = QAAgent(name="agent1", belief=belief)
    agent2 = QAAgent(name="agent2", belief=belief)
    agent1_runtime = ThreadedRuntime.start(agent=agent1)
    agent2_runtime = ThreadedRuntime.start(agent=agent2)

    shared_memory = SharedMemory()

One agent can either subscribe to a particular event type or another agent's events in the shared memory. The subscribing agent will receive events sent by other agents in the shared memory.

.. code-block:: python

  # subscribe to an "trigger" event type
  shared_memory.subscribe_event_type("trigger", agent1_runtime)

  # subscribe to events from a specific agent
  shared_memory.subscribe_sender("agent1", agent1_runtime)

Then, a event can be sent to the shared memory similar to how you would send an event to a single agent:

.. code-block:: python

    from sherpa_ai.events import build_event
    
    # Create an event
    event = build_event("trigger", "input_message", content="Hello, agent2!")
    
    # Send event to shared memory
    await shared_memory.async_add("trigger", "greeting", sender="agent1", content=event)


The base agent as a default logic for handing event, which is to send the sent to the agent's state machine if it is a "trigger" event type, and put all other events into the agent's belief. You can override this logic by implementing your own event handler in the agent class.

.. code-block:: python

  from sherpa_ai.agents.base import BaseAgent

  class CustomAgent(BaseAgent):
      async def async_handle_event(self, event: Event):
          if event.type == "custom_event":
              # Custom logic for handling this event
              pass
          else:
              # Default handling
              await super().async_handle_event(event)

Finally, you can wait for an agent to finish anything it is currently processing by calling the ``wait()`` method on the `proxy runtime <https://pykka.readthedocs.io/stable/examples/#actor-with-proxy>`_. This will block until the agent has completed its current task.

.. code-block:: python

    # Wait for agent1 to finish processing all current events
    agent1_runtime.proxy().wait()


A complete example of multi-agent communication using shared memory can be found at `demo folder <https://github.com/Aggregate-Intellect/sherpa/tree/main/demo/multi-agents>`_
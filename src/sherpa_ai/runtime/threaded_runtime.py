import asyncio
from typing import Any

from pykka import ThreadingActor

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import Event


class ThreadedRuntime(ThreadingActor):
    def __init__(self, agent: BaseAgent):
        """Initialize the ThreadingAgent with a BaseAgent instance.

        Args:
            agent (BaseAgent): The agent to be wrapped in a threading actor.
        """
        super().__init__()
        self.agent = agent

    def on_receive(self, event: Event) -> Any:
        """Handle incoming events with the agent.

        Args:
            event (Event): The event to handle.

        Returns:
            Any: The (future of) result of the event handling.
        """
        asyncio.run(self.agent.async_handle_event(event))
        return self.agent.run()

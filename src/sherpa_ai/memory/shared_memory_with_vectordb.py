"""Vector database-enhanced shared memory module for Sherpa AI.

This module extends the shared memory functionality with vector database integration
for semantic search capabilities. It defines the SharedMemoryWithVectorDB class
which combines shared memory with vector storage for context retrieval.
"""

import threading
from typing import List, Optional

from sherpa_ai.actions.planning import Plan

# from sherpa_ai.agents import AgentPool
from sherpa_ai.connectors.base import BaseVectorDB
from sherpa_ai.events import Event
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.belief import Belief


class SharedMemoryWithVectorDB(SharedMemory):
    """Shared memory with vector database integration for semantic search.

    This class extends SharedMemory to provide context retrieval capabilities
    using a vector database. It allows for semantic search of relevant context
    based on the current task.

    Attributes:
        session_id (str): Unique identifier for the current session.
        vectorStorage (BaseVectorDB): Vector database for semantic search.

    Example:
        >>> memory = SharedMemoryWithVectorDB("Complete task", "session1", vectorStorage=db)
        >>> memory.add("task", "initial_task", content="Process data")
        >>> belief = Belief()
        >>> memory.observe(belief)
        >>> print(belief.current_task.content)
        'Process data'
    """

    def __init__(
        self,
        objective: str,
        session_id: str,
        vectorStorage: BaseVectorDB = None,
    ):
        """Initialize shared memory with vector database integration.

        Args:
            objective (str): The overall objective to pursue.
            session_id (str): Unique identifier for the current session.
            vectorStorage (BaseVectorDB, optional): Vector database for semantic search.

        Example:
            >>> memory = SharedMemoryWithVectorDB("Complete task", "session1")
            >>> print(memory.session_id)
            'session1'
        """
        super().__init__(objective)
        self.current_step = None
        self.session_id = session_id
        self.vectorStorage = vectorStorage

    def observe(self, belief: Belief):
        """Synchronize agent belief with shared memory state and vector database context.

        Updates the agent's belief with the current task, relevant events from shared memory,
        and semantically relevant context from the vector database.

        Args:
            belief (Belief): Agent belief to update.

        Example:
            >>> memory = SharedMemoryWithVectorDB("Complete task", "session1", vectorStorage=db)
            >>> memory.add("task", "initial_task", content="Process data")
            >>> belief = Belief()
            >>> memory.observe(belief)
            >>> print(belief.current_task.content)
            'Process data'
        """
        tasks = super().get_by_type("task")

        task = tasks[-1] if len(tasks) > 0 else None

        # based on the current task search similarity on the context and add it as an
        # event type user_input which is going to be used as a context on the prompt
        contexts = self.vectorStorage.similarity_search(
            query=task.content, 
            number_of_results=5, 
            k=1, 
            session_id=self.session_id
        )
        # Loop through the similarity search results, add the chunks as user_input events which will be added as a context in the belief class.
        for context in contexts:
            super().add(
                name="",
                event_type="user_input",
                content=context.page_content,
            )

        belief.set_current_task(task.content)

        for event in self.events:
            if event.event_type in [
                "task",
                "result",
                "user_input",
            ]:
                belief.update(event)

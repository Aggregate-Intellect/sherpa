from typing import List

from sherpa_ai.memory.events import Event


class Belief:
    def __init__(self):
        # TODO: Handle long belief history, if it's longer than the context size
        # maybe use summarization or a vector db

        self.events: List[Event] = []

    def update(self, observation: Event):
        if observation in self.events:
            return

        self.events.append(observation)

    def get_by_type(self, event_type):
        return [event for event in self.events if event.event_type == event_type]

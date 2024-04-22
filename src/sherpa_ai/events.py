from enum import Enum


class EventType(Enum):
    planning = 1
    task = 2
    result = 3
    feedback = 4
    action = 5
    action_output = 6
    user_input = 7


class Event:
    def __init__(self, event_type: EventType, agent: str, content: str) -> None:
        self.event_type = event_type
        self.agent = agent
        self.content = content

    def __str__(self) -> str:
        return f"{self.agent}: {self.event_type} - {self.content}"

    @property
    def __dict__(self):
        return {
            "event_type": self.event_type,
            "agent": self.agent,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            event_type=data["event_type"],
            agent=data["agent"],
            content=data["content"],
        )

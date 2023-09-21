class EventType:
    def __init__(self, name: str):
        self.name = name


class Event:
    def __init__(self, event_type: EventType, content: str) -> None:
        self.event_type = event_type
        self.content = content

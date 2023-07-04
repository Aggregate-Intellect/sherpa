# from abc import ABC, abstractmethod
# from sherpa.models import Session
# from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage


# class BaseLog(ABC):
#     content: str

#     def __init__(self, content: str):
#         self.content = content

#     @property
#     @abstractmethod
#     def type(self) -> str:
#         """Type of the message, used for serialization."""

#     def to_log(self) -> str:
#         return {
#             "type": self.type,
#             "content": self.content,
#         }

#     def __repr__(self) -> str:
#         f"{self.type}: {self.content}"


# class SetUpLog(BaseLog):
#     @property
#     def type(self) -> str:
#         return "setup"


# class UserLog(BaseLog):
#     @property
#     def type(self) -> str:
#         return "user"


# class SystemLog(BaseLog):
#     @property
#     def type(self) -> str:
#         return "system"


# class AgentLog(BaseLog):
#     @property
#     def type(self) -> str:
#         return "agent"


# class FinishLog(BaseLog):
#     @property
#     def type(self) -> str:
#         return "finish"


# class UserToolLog(UserLog):
#     @property
#     def type(self) -> str:
#         return "assistant_user_tool"


# def _log_from_dict(message: dict) -> BaseLog:
#     _type = message["type"]
#     if _type == "assistant_user_tool":
#         return UserToolLog(message["content"])
#     elif _type == "user":
#         return UserLog(message["content"])
#     elif _type == "system":
#         return SystemLog(message["content"])
#     elif _type == "agent":
#         return AgentLog(message["content"])
#     elif _type == "setup":
#         return SetUpLog(message["content"])
#     else:
#         raise ValueError(f"Unknown log type: {_type}")


# def logs_from_dict(messages: list[dict]) -> list[BaseLog]:
#     return [_log_from_dict(m) for m in messages]


# def _message_from_dict(message: dict) -> BaseMessage:
#     _type = message["type"]
#     if _type == "assistant_user_tool":
#         return AIMessage(content=message["content"])
#     elif _type == "user":
#         return HumanMessage(content=message["content"])
#     elif _type == "system":
#         return SystemMessage(content=message["content"])
#     elif _type == "agent":
#         return AIMessage(content=message["content"])
#     else:
#         raise ValueError(f"Unknown log type: {_type}")


# def messages_from_dict(messages: list[dict]) -> list[BaseMessage]:
#     return [_message_from_dict(m) for m in messages]


# class AgentLogger():
#     session: Session

#     def __init__(self, session: Session, verbose: bool = False):
#         self.session = session
#         logs = self.session.context.get("logs", [])
#         self.session.context["logs"] = logs

#         full_messages = self.session.context.get("full_messages", [])
#         self.session.context["full_messages"] = full_messages

#         self.verbose = verbose

#     def log(self, log: BaseLog):
#         message = log.to_log()
#         if self.verbose:
#             print(message)

#         self.session.context["logs"].append(message)
#         self.session.save()

#     def log_full_message(self, log: BaseLog):
#         message = log.to_log()
#         self.session.context["full_messages"].append(message)
#         self.log(log)

#     def get_logs(self) -> list[BaseLog]:
#         return logs_from_dict(self.session.context["logs"])

#     def get_full_messages(self) -> list[BaseLog]:
#         return logs_from_dict(self.session.context["full_messages"])

#     def increase_count(self):
#         self.session.context['current_task']['count'] += 1
#         self.session.save()

#     def get_count(self) -> int:
#         return self.session.context['current_task']['count']

#     def set_count(self, count: int):
#         self.session.context['current_task']['count'] = count
#         self.session.save()
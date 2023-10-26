import re
from argparse import ArgumentParser
from typing import List, Optional

from pydantic import BaseModel


class AgentConfig(BaseModel):
    verbose: bool = False
    verbosex: bool = False
    gsite: Optional[str] = None
    do_reflect: bool = False

    @classmethod
    def from_input(cls, input_str: str) -> "AgentConfig":
        """
        parse input string into AgentConfig. The configurations are
        at the end of the string
        """
        parts = re.split(r"(?=--)", input_str)
        configs = []

        for part in parts[1:]:
            part = part.strip()
            configs.extend(part.split())

        return cls.from_config(configs)

    @classmethod
    def from_config(cls, configs: List[str]) -> "AgentConfig":
        parser = ArgumentParser()

        parser.add_argument("--verbose", action="store_true")
        parser.add_argument("--verbosex", action="store_true")
        parser.add_argument("--gsite", type=str, default=None)
        parser.add_argument("--do-reflect", action="store_true")

        args, unknown = parser.parse_known_args(configs)

        if len(unknown) > 0:
            raise ValueError(f"Invalid configuration, check your input: {unknown}")

        return AgentConfig(**args.__dict__)

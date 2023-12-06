import re
from argparse import ArgumentParser
from typing import List, Optional, Tuple

from pydantic import BaseModel


class AgentConfig(BaseModel):
    verbose: bool = True
    gsite: Optional[str] = None
    do_reflect: bool = False

    @classmethod
    def from_input(cls, input_str: str) -> Tuple[str, "AgentConfig"]:
        """
        parse input string into AgentConfig. The configurations are
        at the end of the string
        """
        parts = re.split(r"(?=--)", input_str)
        configs = []

        for part in parts[1:]:
            part = part.strip()
            configs.extend(part.split())

        return parts[0].strip(), cls.from_config(configs)

    @classmethod
    def from_config(cls, configs: List[str]) -> "AgentConfig":
        parser = ArgumentParser()

        parser.add_argument(
            "--not-verbose",
            action="store_true",
            help="disable verbose messaging during agent execution",
        )
        parser.add_argument(
            "--gsite",
            type=str,
            default=None,
            help="site to be used for the Google search tool.",
        )
        parser.add_argument(
            "--do-reflect",
            action="store_true",
            help="enable performing the reflection step for each agent.",
        )

        args, unknown = parser.parse_known_args(configs)

        # negate the verbose flag
        if args.not_verbose:
            args.verbose = False

        if len(unknown) > 0:
            raise ValueError(f"Invalid configuration, check your input: {unknown}")

        return AgentConfig(**args.__dict__)

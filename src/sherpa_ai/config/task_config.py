import re
from argparse import ArgumentParser
from functools import cached_property
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, computed_field, validator


class AgentConfig(BaseModel):
    verbose: bool = True
    gsite: list[str] = []
    do_reflect: bool = False
    use_task_agent: bool = False

    @validator("gsite", pre=True)
    def parse_gsite(cls, value: Optional[str]) -> list[str]:
        if value is None:
            return []
        return [url.strip() for url in value.split(",")]

    @computed_field
    @cached_property
    def search_domains(self) -> List[str]:
        return [url for url in self.gsite if validate_url(url)]

    @computed_field
    @cached_property
    def invalid_domains(self) -> List[str]:
        return [url for url in self.gsite if not validate_url(url)]

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
            if part.startswith("--gsite"):
                gsite_arg, gsite_val = part.split(maxsplit=1)
                configs.append(gsite_arg)
                urls = [url.strip() for url in gsite_val.split(",")]
                concatenated_urls = ", ".join(urls)
                configs.append(concatenated_urls)
            else:
                configs.extend(part.split())

        return parts[0].strip(), cls.from_config(configs)

    @classmethod
    def from_config(cls, configs: List[str]) -> "AgentConfig":
        parser = ArgumentParser()

        parser.add_argument(
            "--concise",
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

        parser.add_argument(
            "--use_task_agent",
            action="store_true",
            help="enable use of task agent (obsolete).",
        )

        args, unknown = parser.parse_known_args(configs)

        # negate the verbose flag
        if args.concise:
            args.verbose = False

        if len(unknown) > 0:
            raise ValueError(f"Invalid configuration, check your input: {unknown}")

        return AgentConfig(**args.__dict__)


def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

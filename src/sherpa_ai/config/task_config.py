import re
from argparse import ArgumentParser
from typing import List, Optional, Tuple

from pydantic import BaseModel
from urllib.parse import urlparse


class AgentConfig(BaseModel):
    verbose: bool = False
    gsite: Optional[str] = None
    do_reflect: bool = False
    search_domains: List[str] = None
    invalid_domain: List[str] = None

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
                concatenated_urls = ', '.join(urls)
                configs.append(concatenated_urls)
            else:
                configs.extend(part.split())

        return parts[0].strip(), cls.from_config(configs)

    @classmethod
    def from_config(cls, configs: List[str]) -> "AgentConfig":
        parser = ArgumentParser()

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="enable verbose messaging during agent execution",
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

        if len(unknown) > 0:
            raise ValueError(f"Invalid configuration, check your input: {unknown}")
        
        if args.gsite:
            gsite_list = [url.strip() for url in args.gsite.split(",")]
            args.search_domains = [url for url in gsite_list if validate_url(url)]
            args.invalid_domain = [url for url in gsite_list if not validate_url(url)]

        return AgentConfig(**args.__dict__)
    
def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

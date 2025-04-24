import re
from argparse import ArgumentParser
from functools import cached_property
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import field_validator, BaseModel, computed_field


class AgentConfig(BaseModel):
    """Configuration settings for agent behavior and capabilities.

    This class defines various configuration options that control how agents
    operate, including verbosity, search domains, reflection capabilities,
    and task agent usage.

    Attributes:
        verbose (bool): Whether to enable verbose messaging during agent execution.
            Defaults to True.
        gsite (list[str]): List of domains to be used for Google search.
            Defaults to an empty list.
        do_reflect (bool): Whether to enable the reflection step for each agent.
            Defaults to False.
        use_task_agent (bool): Whether to enable use of task agent (obsolete).
            Defaults to False.

    Example:
        >>> from sherpa_ai.config.task_config import AgentConfig
        >>> config = AgentConfig(verbose=True, gsite=["example.com"])
        >>> print(config.verbose)
        True
        >>> print(config.search_domains)
        ['example.com']
    """
    verbose: bool = True
    gsite: list[str] = []
    do_reflect: bool = False
    use_task_agent: bool = False

    @field_validator("gsite", mode="before")
    @classmethod
    def parse_gsite(cls, value: Optional[str]) -> list[str]:
        """Parse a comma-separated string of URLs into a list.

        Args:
            value (Optional[str]): A comma-separated string of URLs.

        Returns:
            list[str]: A list of stripped URL strings.

        Example:
            >>> from sherpa_ai.config.task_config import AgentConfig
            >>> result = AgentConfig.parse_gsite("example.com, test.com")
            >>> print(result)
            ['example.com', 'test.com']
        """
        if value is None:
            return []
        return [url.strip() for url in value.split(",")]

    @computed_field
    @cached_property
    def search_domains(self) -> List[str]:
        """Get a list of valid search domains.

        Returns:
            List[str]: A list of valid URLs from the gsite attribute.

        Example:
            >>> from sherpa_ai.config.task_config import AgentConfig
            >>> config = AgentConfig(gsite=["https://example.com", "invalid-url"])
            >>> print(config.search_domains)
            ['https://example.com']
        """
        return [url for url in self.gsite if validate_url(url)]

    @computed_field
    @cached_property
    def invalid_domains(self) -> List[str]:
        """Get a list of invalid search domains.

        Returns:
            List[str]: A list of invalid URLs from the gsite attribute.

        Example:
            >>> from sherpa_ai.config.task_config import AgentConfig
            >>> config = AgentConfig(gsite=["https://example.com", "invalid-url"])
            >>> print(config.invalid_domains)
            ['invalid-url']
        """
        return [url for url in self.gsite if not validate_url(url)]

    @classmethod
    def from_input(cls, input_str: str) -> Tuple[str, "AgentConfig"]:
        """Parse input string into AgentConfig.

        This method extracts configuration parameters from a string that contains
        both content and configuration options. Configuration options are expected
        to be at the end of the string, separated by '--'.

        Args:
            input_str (str): The input string containing content and configuration.

        Returns:
            Tuple[str, AgentConfig]: A tuple containing the content part and the
                parsed AgentConfig object.

        Example:
            >>> from sherpa_ai.config.task_config import AgentConfig
            >>> content, config = AgentConfig.from_input("Hello world --gsite example.com")
            >>> print(content)
            Hello world
            >>> print(config.gsite)
            ['example.com']
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
        """Create an AgentConfig from command-line style arguments.

        This method parses a list of command-line style arguments and creates
        an AgentConfig object with the appropriate settings.

        Args:
            configs (List[str]): List of command-line style arguments.

        Returns:
            AgentConfig: A new AgentConfig instance with settings from the arguments.

        Raises:
            ValueError: If invalid configuration options are provided.

        Example:
            >>> from sherpa_ai.config.task_config import AgentConfig
            >>> config = AgentConfig.from_config(["--concise", "--gsite", "example.com"])
            >>> print(config.verbose)
            False
            >>> print(config.gsite)
            ['example.com']
        """
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
    """Check if a string is a valid URL.

    This function validates a URL by checking if it has both a scheme and a netloc.

    Args:
        url (str): The URL string to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.

    Example:
        >>> from sherpa_ai.config.task_config import validate_url
        >>> print(validate_url("https://example.com"))
        True
        >>> print(validate_url("invalid-url"))
        False
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

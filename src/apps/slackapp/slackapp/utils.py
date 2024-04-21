from typing import Optional

from hydra.utils import instantiate
from langchain.base_language import BaseLanguageModel
from omegaconf import OmegaConf
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.config.task_config import AgentConfig


def get_qa_agent_from_config_file(
    config_path: str,
    user_id: Optional[str] = None,
    team_id: Optional[str] = None,
    llm: Optional[BaseLanguageModel] = None,
) -> QAAgent:
    config = OmegaConf.load(config_path)

    agent_config: AgentConfig = instantiate(config.agent_config)
    if user_id is not None:
        config["user_id"] = user_id

    if team_id is not None:
        config["team_id"] = team_id

    if llm is None:
        qa_agent: QAAgent = instantiate(config.qa_agent, agent_config=agent_config)
    else:
        qa_agent: QAAgent = instantiate(
            config.qa_agent, agent_config=agent_config, llm=llm
        )

    return qa_agent

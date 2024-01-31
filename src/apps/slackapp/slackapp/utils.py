from typing import Optional

from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf

from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.config.task_config import AgentConfig


def get_agent(config_path, user_id, team_id, llm=None) -> QAAgent:
    config = OmegaConf.load(config_path)

    agent_config: AgentConfig = instantiate(config.agent_config)
    config["team_id"] = team_id
    config["user_id"] = user_id
    if llm is None:
        qa_agent: QAAgent = instantiate(config.qa_agent, agent_config=agent_config)
    else:
        qa_agent: QAAgent = instantiate(
            config.qa_agent, agent_config=agent_config, llm=llm
        )

    return qa_agent

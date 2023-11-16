from sherpa_ai.config import AgentConfig
from sherpa_ai.tools import SearchTool


def test_search_query_includes_gsite_config():
    site = "https://www.google.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )

    assert config.gsite == site

    search_tool = SearchTool(config=config)

    query = "What is the weather today?"

    updated_query = search_tool.augment_query(query)

    assert f"site:{site}" in updated_query

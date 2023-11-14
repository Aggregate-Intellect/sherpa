from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.config import AgentConfig


def test_gsite_config_successfully():
    site = "https://www.google.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )

    assert config.gsite == site

    google_search = GoogleSearch(role_description="", task="", llm=None, config=config)

    query = "What is the weather today?"

    updated_query = google_search.config_gsite_query(query)

    assert f"site:{site}" in updated_query

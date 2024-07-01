import sys
from unittest.mock import MagicMock, patch

import pytest  # type: ignore
from langchain_openai import ChatOpenAI  # type: ignore
from langchain_core.documents import Document  # type: ignore
from loguru import logger  # type: ignore

from sherpa_ai.agents import QAAgent
from sherpa_ai.connectors.base import BaseVectorDB
from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
from sherpa_ai.events import EventType
from sherpa_ai.memory.shared_memory_with_vectordb import SharedMemoryWithVectorDB
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.utils import file_text_splitter


data = """Avocados are a fruit, not a vegetable. They're technically considered a single-seeded berry, believe it or not.
The Eiffel Tower can be 15 cm taller during the summer, due to thermal expansion meaning the iron heats up, the particles gain kinetic energy and take up more space.
Trypophobia is the fear of closely-packed holes. Or more specifically, "an aversion to the sight of irregular patterns or clusters of small holes or bumps." No crumpets for them, then.
Allodoxaphobia is the fear of other people's opinions. It's a rare social phobia that's characterised by an irrational and overwhelming fear of what other people think.
Australia is wider than the moon. The moon sits at 3400km in diameter, while Australia’s diameter from east to west is almost 4000km.
'Mellifluous' is a sound that is pleasingly smooth and musical to hear.
The Spice Girls were originally a band called Touch. "When we first started [with the name Touch], we were pretty bland," Mel C told The Guardian in 2018. "We felt like we had to fit into a mould."
Emma Bunton auditioned for the role of Bianca Butcher in Eastenders. Baby Spice already had a small part in the soap back in the 90s but tried out for a full-time role. She was pipped to the post by Patsy Palmer but ended up auditioning for the Spice Girls not long after.
Human teeth are the only part of the body that cannot heal themselves. Teeth are coated in enamel which is not a living tissue.
It's illegal to own just one guinea pig in Switzerland. It's considered animal abuse because they're social beings and get lonely.
The Ancient Romans used to drop a piece of toast into their wine for good health - hence why we 'raise a toast'.
The heart of a shrimp is located in its head. They also have an open circulatory system, which means they have no arteries and their organs float directly in blood.
Amy Poehler was only seven years older than Rachel McAdams when she took on the role of "cool mom" in Mean Girls. Rachel was 25 as Regina George - Amy was 32 as her mum.
People are more creative in the shower. When we take a warm shower, we experience an increased dopamine flow that makes us more creative.
Baby rabbits are called kits. Cute!
my dog died on march 2021.
The unicorn is the national animal of Scotland. It was apparently chosen because of its connection with dominance and chivalry as well as purity and innocence in Celtic mythology.
The first aeroplane flew on December 17,1903 and  . Wilbur and Orville Wright made four brief flights at Kitty Hawk, North Carolina, with their first powered aircraft, aka the first airplane.
Venus is the only planet to spin clockwise. It travels around the sun once every 225 Earth days but it rotates clockwise once every 243 days.
Nutmeg is a hallucinogen. The spice contains myristicin, a natural compound that has mind-altering effects if ingested in large doses.
A 73-year-old bottle of French Burgundy became the most expensive bottle of wine ever sold at auction in 2018, going for $558,000 (approx £439,300). The bottle of 1945 Romanee-Conti sold at Sotheby for more than 17 times its original estimate of $32,000."""
session_id = "6"
meta_data = {
    "session_id": f"{session_id}",
    "file_name": "rtgfqq",
    "file_type": "pdf",
    "title": "NoMeaning",
    "data_type": "user_input",
}

data2 = """
    Comets are celestial objects that orbit the sun along an elongated path. They are made up of dust, rock, and ices, and can range in width from a few miles to tens of miles. When comets get closer to the sun, they heat up and release gases and dust into a glowing head that can be bigger than a planet. Comets have two separate tails, one white and made of dust, and one bluish and made of electrically charged gas molecules, or ions.
    """
session_id2 = "5"
meta_data2 = {
    "session_id": f"{session_id}",
    "file_name": "kk",
}


def fake_embedding(input, default_dimension=1536):
    results = []
    for text in input:
        # The word comet is used to distinguish two different texts in the tests
        if "comets" in text.lower():
            results.append([1] * default_dimension)
        else:
            results.append([0] * default_dimension)
    return results


@pytest.fixture
def mock_chroma_vector_store(external_api):
    if external_api:
        yield
        return

    with patch("chromadb.api.models.Collection.validate_embedding_function"), patch(
        "chromadb.utils.embedding_functions.OpenAIEmbeddingFunction",
    ) as mock_embedding:
        mock_embedding.return_value = fake_embedding
        yield


def create_mock_vector_storage():
    mock_vector_storage = MagicMock(spec=BaseVectorDB)
    mock_vector_storage.similarity_search.return_value = [
        Document(
            page_content="'file_content': 'KKKK Avocados are a fruit, not a vegetable. They're technically considered a single-seeded berry, believe it or not.\nThe Eiffel Tower can be 15 cm taller during the summer, due to thermal expansion meaning the iron heats up, the particles gain kinetic energy and take up more space.\nTrypophobia is the fear of closely-packed holes. Or more specifically, \"an aversion to the sight of irregular patterns or clusters of small holes or bumps.\" No crumpets for them, then.\nAllodoxaphobia is the fear of other people's opinions. It's a rare social phobia that's characterised by an irrational and overwhelming fear of what other people think.\nAustralia is wider than the moon. The moon sits at 3400km in diameter, while Australia’s diameter from east to west is almost 4000km.\n'Mellifluous' is a sound that is pleasingly smooth and musical to hear.\nThe Spice Girls were originally a band called Touch. \"When we first started [with the name Touch], we were pretty bland,\" Mel C told The Guardian in 2018. \"We felt like we had to fit into a mould.\"\nEmma Bunton auditioned for the role of Bianca Butcher in Eastenders. Baby Spice already had a small part in the soap back in the 90s but tried out for a full-time role. She was pipped to the post by Patsy Palmer but ended up auditioning for the Spice Girls not long after.\nHuman teeth are the only part of the body that cannot heal themselves. Teeth are coated in enamel which is not a living tissue.\nIt's illegal to own just one guinea pig in Switzerland. It's considered animal abuse because they're social beings and get lonely.\nThe Ancient Romans used to drop a piece of toast into their wine for good health - hence why we 'raise a toast'.\nThe heart of a shrimp is located in its head. They also have an open circulatory system, which means they have no arteries and their organs float directly in blood.\nAmy Poehler was only seven years older than Rachel McAdams when she took on the role of \"cool mom\" in Mean Girls. Rachel was 25 as Regina George - Amy was 32 as her mum.\nPeople are more creative in the shower. When we take a warm shower, we experience an increased dopamine flow that makes us more creative.\nBaby rabbits are called kits. Cute!\nmy dog died on march 2021.\nThe unicorn is the national animal of Scotland. It was apparently chosen because of its connection with dominance and chivalry as well as purity and innocence in Celtic mythology.\nThe first aeroplane flew on December 17,1903 and  . Wilbur and Orville Wright made four brief flights at Kitty Hawk, North Carolina, with their first powered aircraft, aka the first airplane.\nVenus is the only planet to spin clockwise. It travels around the sun once every 225 Earth days but it rotates clockwise once every 243 days.\nNutmeg is a hallucinogen. The spice contains myristicin, a natural compound that has mind-altering effects if ingested in large doses.\nA 73-year-old bottle of French Burgundy became the most expensive bottle of wine ever sold at auction in 2018, going for $558,000 (approx £439,300). The bottle of 1945 Romanee-Conti sold at Sotheby for more than 17 times its original estimate of $32,000.' ,{'session_id': '6', 'file_name': 'rtgfqq', 'file_type': 'pdf', 'title': 'NoMeaning', 'data_type': 'user_input'}",
            metadata={
                "session_id": "6",
                "file_name": "rtgfqq",
                "file_type": "pdf",
                "title": "NoMeaning",
                "data_type": "user_input",
            },
        )
    ]
    return mock_vector_storage


def test_chroma_vector_store_from_texts(mock_chroma_vector_store):
    """
    Test to create a Chroma Vector Store from texts and
    """
    split_data = file_text_splitter(data=data, meta_data=meta_data)
    chroma = ChromaVectorStore.chroma_from_texts(
        texts=split_data["texts"], meta_datas=split_data["meta_datas"]
    )
    result = chroma.similarity_search(
        query="avocado",
    )
    result_content = result[0].page_content
    logger.debug(result_content)
    assert len(result_content) > 0, "Failed to do similarity search from text"


def test_chroma_vector_store_from_existing_store(mock_chroma_vector_store):
    """
    Test to create a Chroma Vector Store from an existing store and
    check if the similarity search is working as expected by checking where the chunk comes from
    """
    split_data = file_text_splitter(data=data2, meta_data=meta_data2)
    ChromaVectorStore.chroma_from_texts(
        texts=split_data["texts"], meta_datas=split_data["meta_datas"]
    )
    split_data_two = file_text_splitter(data=data, meta_data=meta_data)
    ChromaVectorStore.chroma_from_texts(
        texts=split_data_two["texts"], meta_datas=split_data_two["meta_datas"]
    )

    chroma = ChromaVectorStore.chroma_from_existing()
    result = chroma.similarity_search(
        query="comets",
    )

    result_content = result[0].page_content
    logger.debug(result[0])

    assert len(
        result_content) > 0, "Failed to do similarity search from exsiting store"
    assert result[0].metadata["file_name"] == "kk", "Chunk is not from the correct file"


@pytest.mark.external_api
def test_shared_memory_with_vector(get_llm, mock_chroma_vector_store):  # noqa F811
    llm = get_llm(__file__, test_shared_memory_with_vector.__name__)

    shared_memory = SharedMemoryWithVectorDB(
        objective="summerize the file rtgfqq.",
        agent_pool=None,
        session_id=session_id,
        vectorStorage=create_mock_vector_storage(),
    )

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "summerize the file rtgfqq",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    logger.debug(results[0].content)
    expected = [
        "Avocados",
        "Eiffel Tower",
        "Trypophobia",
        "Allodoxaphobia",
        "Australia",
        "Mellifluous",
        "Spice Girls",
        "Emma Bunton",
        "Human teeth",
        "guinea pig",
        "Ancient Romans",
        "shrimp",
        "Amy Poehler",
        "shower",
        "Baby rabbits",
        "unicorn",
        "aeroplane",
        "Venus",
        "Nutmeg",
        "French Burgundy",
    ]
    assert any(
        item in results[0].content for item in expected
    ), "Result does not contain any expected items"
    assert len(results) == 1

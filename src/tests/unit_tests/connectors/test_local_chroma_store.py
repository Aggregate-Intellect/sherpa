import pytest

from sherpa_ai.connectors.vectorstores import LocalChromaStore


class FakeEmbeddings:
    """Deterministic stand-in for OpenAIEmbeddings: each text maps to a
    fixed-size vector based on its length, so unrelated texts don't collide."""

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text):
        return [float(len(text)), float(sum(ord(c) for c in text) % 97)]


@pytest.fixture
def store():
    return LocalChromaStore(collection_name="test", embedding_function=FakeEmbeddings())


def test_add_texts_and_similarity_search_round_trip(store):
    store.add_texts(
        ["sherpa helps you climb mountains", "bananas are yellow"],
        metadatas=[{"topic": "sherpa"}, {"topic": "fruit"}],
    )

    results = store.similarity_search("sherpa helps you climb mountains", k=1)

    assert len(results) == 1
    assert results[0].page_content == "sherpa helps you climb mountains"
    assert results[0].metadata["topic"] == "sherpa"


def test_from_texts_builds_a_queryable_store():
    store = LocalChromaStore.from_texts(
        ["sherpa helps you climb mountains", "bananas are yellow"],
        embedding=FakeEmbeddings(),
        metadatas=[{"topic": "sherpa"}, {"topic": "fruit"}],
        index_name="test_from_texts",
    )

    results = store.similarity_search("bananas are yellow", k=1)

    assert len(results) == 1
    assert results[0].page_content == "bananas are yellow"

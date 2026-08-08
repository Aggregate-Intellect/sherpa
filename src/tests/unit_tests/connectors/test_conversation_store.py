from unittest.mock import MagicMock

from sherpa_ai.connectors.vectorstores import ConversationStore


def test_from_texts_creates_store_and_adds_texts():
    fake_db = MagicMock()
    embedding = MagicMock()
    embedding.embed_query.side_effect = [[0.1], [0.2]]

    store = ConversationStore.from_texts(
        ["hello", "world"],
        embedding,
        metadatas=[{"a": 1}, {"b": 2}],
        namespace="ns",
        db=fake_db,
    )

    assert isinstance(store, ConversationStore)
    assert fake_db.upsert.call_count == 2

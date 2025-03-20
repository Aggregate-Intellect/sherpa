import argparse
import json
import uuid

import chromadb
from chromadb.config import Settings
from loguru import logger
from tqdm import tqdm


def main(args):
    client = chromadb.HttpClient(
        host=args.chroma_host,
        port=args.chroma_port,
        settings=Settings(allow_reset=True),
    )

    collection = client.get_or_create_collection(args.chroma_index)

    with open(args.dump_path, encoding="utf8") as f:
        records = json.load(f)

    logger.info(f"Loading {len(records)} records into Chroma")
    for record in tqdm(records):
        collection.add(
            ids=[str(uuid.uuid1())],
            embeddings=record["values"],
            documents=record["metadata"]["text"],
            metadatas={
                "source": record["metadata"].get("source", ""),
            },
        )
    logger.info("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chroma_host", help="URL of Chroma instance", default="localhost"
    )
    parser.add_argument("--chroma_port", help="Port of Chroma instance", default="8000")
    parser.add_argument(
        "--chroma_index", help="Index of Chroma instance", default="langchain"
    )
    parser.add_argument(
        "--dump_path", help="Path to dump file", default="files/data.json"
    )

    args = parser.parse_args()
    main(args)

import argparse
import json
import uuid

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from loguru import logger


def main(args):
    client = chromadb.HttpClient(
        host=args.chroma_host,
        port=args.chroma_port,
        settings=Settings(allow_reset=True),
    )

    embedding_func = embedding_functions.OpenAIEmbeddingFunction(
        model_name="text-embedding-ada-002"
    )
    collection = client.get_or_create_collection(
        name=args.chroma_index, embedding_function=embedding_func
    )

    query = input("Enter query: ")
    results = collection.query(query_texts=[query], n_results=1)

    logger.info(results["documents"][0][0])

    logger.info("Done! Chroma is up and running.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chroma_host", help="URL of Chroma instance", default="localhost"
    )
    parser.add_argument(
        "--chroma_port", help="Port of Chroma instance", default="8000")
    parser.add_argument(
        "--chroma_index", help="Index of Chroma instance", default="langchain"
    )

    args = parser.parse_args()

    load_dotenv()
    main(args)

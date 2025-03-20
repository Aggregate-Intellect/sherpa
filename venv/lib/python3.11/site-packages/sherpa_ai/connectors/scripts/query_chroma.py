import argparse
import json
import uuid

import chromadb 
from chromadb.config import Settings 
from dotenv import load_dotenv 
from langchain_openai import OpenAIEmbeddings 
from langchain_community.vectorstores import Chroma 
from loguru import logger 


def main(args):
    client = chromadb.HttpClient(
        host=args.chroma_host,
        port=args.chroma_port,
        settings=Settings(allow_reset=True),
    )

    embedding_func = OpenAIEmbeddings()
    chroma = Chroma(
        client=client,
        collection_name=args.chroma_index,
        embedding_function=embedding_func,
    )

    query = input("Enter query: ")
    results = chroma.similarity_search(query)

    logger.info(results[0].page_content)

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

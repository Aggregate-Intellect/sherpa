from typing import List
from langchain.docstore.document import Document
from langchain.document_loaders import UnstructuredPDFLoader, UnstructuredMarkdownLoader


def load_files(files: List[str]) -> List[Document]:
    documents = []
    loader = None
    for f in files:
        print(f'Loading file {f}')
        if f.endswith(".pdf"):
            loader = UnstructuredPDFLoader(f)
        elif f.endswith(".md"):
            loader = UnstructuredMarkdownLoader(f)
        elif f.endswith(".gitkeep"):
            pass
        else:
            raise NotImplementedError(f"File type {f} not supported")
        if loader is not None:
            documents.extend(loader.load())
    
    print(documents)
    return documents
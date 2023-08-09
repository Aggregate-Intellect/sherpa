from typing import List
from langchain.docstore.document import Document
from langchain.document_loaders import UnstructuredPDFLoader, UnstructuredMarkdownLoader


def load_files(files: List[str]) -> List[Document]:
    documents = []
    for f in files:
        print(f'Loading file {f}')
        if f.endswith(".pdf"):
            loader = UnstructuredPDFLoader(f)
        elif f.endswith(".md"):
            loader = UnstructuredMarkdownLoader(f)
        else:
            raise NotImplementedError(f"File type {f} not supported")
        documents.extend(loader.load())
    
    print(documents)
    return documents

def contains_verbose(query: str) -> bool:
    '''looks for -verbose in the question and returns True or False \
    includes -verbosex'''
    return "-verbose" in query.lower()

def contains_verbosex(query: str) -> bool:
    '''looks for -verbosex in the question and returns True or False'''
    return "-verbosex" in query.lower()

def format_verbose(logger):
    '''Formats the logger into readable string'''
    log_strings = []
    for log in logger:
        reply = log["reply"]
        if "thoughts" in reply:
            formatted_reply = f"""-- Step: {log["Step"]} -- \nThoughts: \n {reply["thoughts"]} """
            if "command" in reply: # add command if it exists
              formatted_reply += f"""\nCommand: \n {reply["command"]}"""
            log_strings.append(formatted_reply)
        else: # for final response
            formatted_reply = f"""-- Step: {log["Step"]} -- \nFinal Response: \n {reply}"""
            log_strings.append(formatted_reply)
    log_string =  "\n".join(log_strings)
    return log_string

def show_commands_only(logger):
    '''Modified version of format_verbose that only shows commands'''
    log_strings = []
    for log in logger:
        reply = log["reply"]
        if "command" in reply:
          formatted_reply = f"""-- Step: {log["Step"]} -- \nCommand: \n {reply["command"]}"""
          log_strings.append(formatted_reply)
    log_string =  "\n".join(log_strings)
    return log_string

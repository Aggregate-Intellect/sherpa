import os
import time
import re
import json
import tiktoken

from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from langchain.text_splitter import MarkdownTextSplitter
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain.document_loaders import PDFMinerLoader
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.chroma import Chroma
from loguru import logger
from pydantic import ConfigDict

from sherpa_ai.actions.base import BaseAction


class DocumentSearch(BaseAction):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # file name of the pdf
    filename: str
    # the embedding function to use
    embedding_function: Embeddings
    # number of results to return in search
    k: int
    # the variables start with _ will not included in the __init__
    _chroma: Chroma

    # Override name and args properties from BaseAction
    # The name of the action, used to describe the action to the agent.
    name: str = "DocumentSearch"
    # The arguments that the action takes, used to describe the action to the agent.
    args: dict = {"query": "string"}

    def __init__(self, **kwargs):
        # initialize attributes using Pydantic BaseModel
        super().__init__(**kwargs)

        # load the pdf and create the vector store
        self._chroma = Chroma(embedding_function=self.embedding_function)
        documents = PDFMinerLoader(self.filename).load()
        documents = SentenceTransformersTokenTextSplitter(
            chunk_overlap=0
        ).split_documents(documents)

        logger.info(f"Adding {len(documents)} documents to the vector store")
        self._chroma.add_documents(documents)
        logger.info("Finished adding documents to the vector store")

    def execute(self, query):
        """
        Execute the action by searching the document store for the query

        Args:
            query (str): The query to search for

        Returns:
            str: The search results combined into a single string
        """

        results = self._chroma.search(query, search_type="mmr", k=self.k)
        return "\n\n".join([result.page_content for result in results])
    

class Outliner:
    def __init__(self, input_filename=None) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_folder_path = os.path.join(script_dir, 'Transcripts')
        folder_path = default_folder_path

        transcript_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

        if not transcript_files:
            raise ValueError("No transcript files found in the folder.")

        if input_filename:
            if input_filename in transcript_files:
                transcript_file_path = os.path.join(folder_path, input_filename)
            else:
                raise FileNotFoundError(f"The specified file {input_filename} does not exist in the Transcripts folder.")
        else:
            transcript_file_path = os.path.join(folder_path, transcript_files[0])

        print(f"Using transcript file: {transcript_file_path}")

        with open(transcript_file_path, "r", encoding="utf-8") as f:
            self.raw_transcript = f.read()

        self.chat = ChatOpenAI(
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0,
            model="gpt-3.5-turbo",
        )

        self.chat_4o = ChatOpenAI(
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0,
            model="gpt-4o",
        )

    def num_tokens_from_string(
        self, string: str, encoding_name="cl100k_base"
    ) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def transcript_splitter(self, chunk_size=3000, chunk_overlap=200):
        markdown_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        transcript_chunks = markdown_splitter.create_documents(
            [self.raw_transcript]
        )
        return transcript_chunks

    def transcript2insights(self, transcript):
        system_template = "You are a helpful assistant that summarizes transcripts of podcasts or lectures."
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_template = """From this chunk of a presentation transcript, extract a short list of key insights. \
            Each line of the transcript starts with the initials of the speaker, and each key insight has to preserve the attribution to speaker. \
            Skip explaining what you're doing, labeling the insights and writing conclusion paragraphs. \
            The insights have to be phrased as statements of facts with no references to the presentation or the transcript. \
            Statements have to be full sentences and in terms of words and phrases as close as possible to those used in the transcript. \
            Keep as much detail as possible. The transcript of the presentation is delimited in triple backticks.

            Desired output format:
            - [speaker initials]: [Key insight #1]
            - [speaker initials]: [Key insight #2]
            - [...]

            Transcript:
            ```{transcript}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        result = self.chat(
            chat_prompt.format_prompt(transcript=transcript).to_messages()
        )

        return result.content

    def create_essay_insights(self, transcript_chunks, verbose=True):
        response = ""
        for i, text in enumerate(transcript_chunks):
            insights = self.transcript2insights(text.page_content)
            response = "\n".join([response, insights])
            if verbose:
                print(
                    f"\nInsights extracted from chunk {i+1}/{len(transcript_chunks)}:\n{insights}"
                )
        return response

    def create_blueprint(self, statements, verbose=True):

        # Split the text into lines
        lines = statements.split('\n')
        
        # Initialize a dictionary to hold the processed lines
        processed_dict = {}
        
        # Initialize a line number counter
        line_number = 1
        
        # Iterate through each line
        for line in lines:
            # Skip lines that start with "Insights extracted from chunk"
            if line.startswith("Insights extracted from chunk"):
                continue
            # Skip empty lines
            if not line.strip():
                continue
            # Replace "- " at the beginning of the line with "- [line number] "
            processed_line = re.sub(r'^- ', '', line)  # Remove the leading "- "
            # Add the line to the dictionary with the line number as the key
            processed_dict[line_number] = processed_line
            # Increment the line number counter
            line_number += 1

            # Flatten the dictionary into a single string with the desired format
            processed_lines = [f'- [{line_number}] {statement}' for line_number, statement in processed_dict.items()]
            processed_statements = '\n'.join(processed_lines)

        system_template = """You are an experienced technical writer who is good at storytelling for technical topics."""
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """organize the following insights in a logical order. \
                keep only numbers corresponding to the key insight and not the statements of the insights. \
                cluster points that talk about the same topic. \
                only include 3-5 key insights per topic. \
                combine each 3-5 topics into a higher level topic. \
                organize the information in a json structure.

            Insights:
            ```{insights}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        outline = self.chat_4o(
            chat_prompt.format_prompt(insights=processed_statements).to_messages()
        )

        # Use regex to extract the JSON part
        json_match = re.search(r'```json(.*?)```', outline.content, re.DOTALL)

        # Check if the JSON part was found
        if json_match:
            json_str = json_match.group(1).strip()
            
            # Convert the JSON string to a JSON object
            outline_json = json.loads(json_str)
            
            # Print the JSON object
            print(json.dumps(outline_json, indent=2))
        else:
            print("No JSON part found in the outline text.")
        
        # Iterate over the JSON data to replace numbers with strings from p_dict
        for key, value in outline_json.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    outline_json[key][sub_key] = [processed_dict[item] for item in sub_value]
            elif isinstance(value, list):
                outline_json[key] = [processed_dict[item] for item in value]

        if verbose:
            print(f"\nEssay outline: {outline.content}\n")
            print(f"\nEssay outline (text): {outline_json}\n")
        return outline_json

    # @timer_decorator
    def full_transcript2outline_json(self, verbose=True):
        print("\nChunking transcript...")
        transcript_docs = self.transcript_splitter()
        t1 = time.time()
        print("\nExtracting key insights...")
        essay_insights = self.create_essay_insights(transcript_docs, verbose)
        t2 = time.time() - t1
        print("\nCreating essay outline...")
        t1 = time.time()
        blueprint = self.create_blueprint(essay_insights, verbose)
        t3 = time.time() - t1
        if verbose:
            print()
            print(f"Extracted essay insights in {t2:.2f} seconds.")
            print(f"Created essay blueprint in {t3:.2f} seconds.")
        return blueprint

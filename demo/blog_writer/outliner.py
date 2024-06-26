import os
import time

import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from langchain.text_splitter import MarkdownTextSplitter


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
            Skip explaining what you're doing, labeling the insights and writing conclusion paragraphs. \
            The insights have to be phrased as statements of facts with no references to the presentation or the transcript. \
            Statements have to be full sentences and in terms of words and phrases as close as possible to those used in the transcript. \
            Keep as much detail as possible. The transcript of the presentation is delimited in triple backticks.

            Desired output format:
            - [Key insight #1]
            - [Key insight #2]
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
        system_template = """You are a helpful AI blogger who writes essays on technical topics."""
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """Organize the following list of statements (delimited in triple backticks) to create the outline \
            for a blog post in JSON format. The highest level is the most plausible statement as the overarching thesis \
            statement of the post, the next layers are statements providing supporting arguments for the thesis statement. \
            The last layer are pieces of evidence for each of the supporting arguments, directly quoted from the provided \
            list of statements. Use as many of the provided statements as possible. Keep their wording as is without paraphrasing them. \
            Retain as many technical details as possible. The thesis statement, supporting arguments, and evidences must be \
            full sentences containing claims. Label each layer with the appropriate level title and create the desired JSON output format below. \
            Only output the JSON and skip explaining what you're doing:

            Desired output format:
            {{
            "Thesis Statement": "...",
            "Supporting Arguments": [
                {{
                "Argument": "...",
                "Evidence": [
                    "...", "...", "...", ...
                ]
                }},
                {{
                "Argument": "...",
                "Evidence": [
                    "...", "...", "...", ...
                ]
                }},
                ...
            ]
            }}

            Statements:
            ```{statements}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        outline = self.chat(
            chat_prompt.format_prompt(statements=statements).to_messages()
        )

        if verbose:
            print(f"\nEssay outline: {outline.content}\n")
        return outline.content

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

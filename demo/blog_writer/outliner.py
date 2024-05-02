import os
import time

import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.text_splitter import MarkdownTextSplitter


class Outliner:
    def __init__(self, transcript_file) -> None:
        with open(transcript_file, "r") as f:
            self.raw_transcript = f.read()
        # instantiate chat model
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
                    f"\nInsights extracted from chunk {i+1}/{len(transcript_chunks)}:\n {insights}"
                )
        return response

    def create_blueprint(self, insights, verbose=True):
        system_template = """You are a helpful AI blogger who writes essays on technical topics."""
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """Organize the following statements (delimited in triple backticks) to create the outline for \
            a blog post. Output the outline in a tree structure where the highest level is the most plausible statement \
            as the thesis statement for the post, the next layers are statements providing supporting arguments for the \
            thesis statement, and the last layer are pieces of evidence for each of the supporting arguments. Use all of \
            the provuded statements and keep them as is instead of paraphrasing them. The thesis statement, supporting argument, \
            and evidences have to be full sentences containing claims. Label each layer with the appropriate level title \
            like the desired output format below:

            Desired output format:
            - Thesis Statement: [xxx]
                - Supporting Argument: [yyy]
                    - Evidence: [zzz]

            Statements:
            ```{insights}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        outline = self.chat(
            chat_prompt.format_prompt(insights=insights).to_messages()
        )

        if verbose:
            print(f"\nEssay outline: {outline.content}\n")
        return outline.content

    def convert2JSON(self, outline):
        system_template = (
            """You are a helpful assistant that outputs JSON data from text."""
        )
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """Convert the outline below (delimited within triple backticks) to a valid JSON string. \
            Only output the JSON object and skip explaining what you're doing.

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

            Outline:
            ```{outline}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        json = self.chat(
            chat_prompt.format_prompt(outline=outline).to_messages()
        )

        return json.content

    # @timer_decorator
    def full_transcript2outline_json(self, verbose=True):
        print("\nChunking transcript...")
        transcript_docs = self.transcript_splitter()
        t1 = time.time()
        print("\nExtracting key insights...")
        essay_insights = self.create_essay_insights(transcript_docs, verbose)
        t2 = time.time() - t1
        print("\nCreating essay...")
        t1 = time.time()
        blueprint = self.create_blueprint(essay_insights, verbose)
        t3 = time.time() - t1
        print("\nCreating JSON...")
        t1 = time.time()
        blueprint_json = self.convert2JSON(blueprint)
        t4 = time.time() - t1
        if verbose:
            print()
            print(f"Extracted essay insights in {t2:.2f} seconds.")
            print(f"Created essay blueprint in {t3:.2f} seconds.")
            print(f"Created JSON in {t4:.2f} seconds.")
        return blueprint_json

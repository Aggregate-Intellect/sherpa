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

    def transcript2question(self, transcript):
        system_template = "You are a helpful assistant that reflects on a transcript of podcasts or lectures."
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_template = """From the contents and information of the presentation, extract a single, \
        succinct and clear question which the presentation attempts to answer. Write the question as though \
        the speaker wrote it himself when outlining the presentation prior to creating it. Only output the question itself and nothing else. \
        The transcript of this presentation is delimited in triple backticks:
        ```{transcript}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        result = self.chat(
            chat_prompt.format_prompt(transcript=transcript).to_messages()
        )
        return result.content

    def create_essay_questions(self, transcript_chunks):
        essay_response = ""
        for i, text in enumerate(transcript_chunks):
            essay = self.transcript2question(text.page_content)
            essay_response = f"\n\n**Question {i+1}**: ".join(
                [essay_response, essay]
            )
        return essay_response

    def organize_questions(self, questions):
        # system_template = """You are a helpful assistant that summarizes and \
        # processes large text information."""
        system_template = """You are a helpful technical writer that processes and \
        organizes large text information."""
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        # human_template = """Given the list of questions below (enclosed in triple backticks), come up \
        #     with a list of topics covered by them, and then output a valid JSON string where each key is a \
        #     topic and its value is a list of questions from the list below which are relevant to that \
        #     topic. Sort the topics in a logical order and number the topics (the JSON keys) accordingly. \
        #     Only output the final JSON object and nothing else.\n
        human_template = """Given the list of questions below (enclosed in triple backticks), come up with the list of \
            topics covered by them, sort the topics in a logical order, and then output a valid JSON string where each \
            key is an enumerated topic (e.g. "1. Topic Name") and the corresponding value is a list of questions from \
            the list below which are relevant to that topic. Only output the final JSON object and nothing else.\n
        #     ```{questions}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        outline = self.chat(
            chat_prompt.format_prompt(questions=questions).to_messages()
        )

        return outline.content

    # @timer_decorator
    def full_transcript2blueprint(self, verbose=True):
        print("Chunking transcript...")
        transcript_docs = self.transcript_splitter()
        t1 = time.time()
        print("Creating essay parts...")
        chunk_questions = self.create_essay_questions(transcript_docs)
        t2 = time.time() - t1
        print("Merging essay parts...")
        t1 = time.time()
        blueprint = self.organize_questions(chunk_questions)
        t3 = time.time() - t1
        if verbose:
            print(f"Created essay parts in {t2:.2f} seconds")
            print(f"Merged essay parts in {t3:.2f} seconds")
        return blueprint


# # """# Part 2: Extracting from essay"""


# def extract_metadata_as_json(essay, chat_model=chat):

#     system_template = """ Given the essay delimited in triple backticks, generate and extract important \
#   information such as the title, speaker, summary, a list of key topics, \
#   and a list of important takeaways for each topic. \
#   Format the response as a JSON object, with the keys 'Title', 'Topics', 'Speaker', \
#   'Summary', and 'Topics' as the keys and each topic will be keys for list of takeaways. \
#   Example of JSON output: \n \
#  {{\
#   'Title': 'Title of the presentation',\
#   'Speaker': 'John Smith',\
#   'Summary': 'summary of the presentation',\
#   'Topics': [\
#   {{\
#   'Topic': 'topic 1',\
#   'Takeaways': [\
#   'takeaway 1',\
#   'takeaway 2',\
#   'takeaway 3'\
#   ]\
#   }},\
#   {{\
#   'Topic': 'topic 2',\
#   'Takeaways': [\
#   'takeaway 1',\
#   'takeaway 2',\
#   'takeaway 3'\
#   ]\
#   }},\
#   {{\
#   'Topic': 'topic 3',\
#   'Takeaways': [\
#   'takeaway 1',\
#   'takeaway 2',\
#   'takeaway 3'\
#   ]\
#   }},\
#   {{\
#   'Topic': 'topic 4',\
#   'Takeaways': [\
#   'takeaway 1',\
#   'takeaway 2',\
#   'takeaway 3'\
#   ]\
#   }}\
#   ]\
#   }}"""

#     system_prompt = SystemMessagePromptTemplate.from_template(system_template)

#     human_template = """Essay: ```{text}```"""

#     human_prompt = HumanMessagePromptTemplate.from_template(human_template)
#     chat_prompt = ChatPromptTemplate.from_messages(
#         [system_prompt, human_prompt]
#     )

#     result = chat_model(chat_prompt.format_prompt(text=essay).to_messages())
#     try:
#         metadata_json = json.loads(result.content)
#     except Exception as e:
#         print(e)
#         metadata_json = result.content
#     return metadata_json


# def json2rst(metadata, rst_filepath):
#     if not isinstance(metadata, dict):
#         metadata = json.loads(metadata)

#     # rst_filepath = './essays/test.rst'
#     with open(rst_filepath, "a") as the_file:
#         the_file.write("\n\n")
#         for key, value in metadata.items():
#             if key == "Title":
#                 title_mark = "=" * len(f"{value}")
#                 the_file.write(title_mark + "\n")
#                 the_file.write(f"{value} \n")
#                 the_file.write(title_mark + "\n")
#             elif key == "Speaker":
#                 the_file.write("*" + f"{value}" + "* \n\n")
#             elif key == "Summary":
#                 title_mark = "-" * len(f"{key}")
#                 the_file.write("Summary \n")
#                 the_file.write(title_mark + "\n")
#                 the_file.write(f"{value} \n\n")
#             elif key == "Topics":
#                 the_file.write("Topics: \n")
#                 the_file.write(title_mark + "\n")
#                 for topic in value:
#                     the_file.write("\t" + f"{topic['Topic']} \n")
#                     for takeaway in topic["Takeaways"]:
#                         the_file.write("\t\t" + f"* {takeaway} \n")

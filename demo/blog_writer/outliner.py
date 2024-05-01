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
        human_template = """From the content of the presentation, extract at least 1 and at most 3 key insight(s). \
            If a topic is stated to be discussed in detail later on in the presentation, do not include that topic. \
            Do not explain what you're doing. Do not output anything other than the list of insights. Do not format \
            the output. The transcript of the presentation is delimited in triple backticks: \
        ```{transcript}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        result = self.chat(
            chat_prompt.format_prompt(transcript=transcript).to_messages()
        )
        return result.content

    def create_essay_insights(self, transcript_chunks):
        response = ""
        for i, text in enumerate(transcript_chunks):
            insights = self.transcript2insights(text.page_content)
            response = f"\n\n**Question {i+1}**: ".join([response, insights])
        return response

    def extract_thesis_statement(self, insights):
        system_template = """You are a helpful assistant that summarizes large text information."""
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """From the below list of key points discussed in a presentation, extract \
            a single, coherent, and succinct thesis statement that captures the essence of the \
            presentation. Your thesis statement must be the combination of a topic and a claim \
            the presenter is making about that topic. Only output the thesis statement and nothing \
            else. The list of key points is delimited between triple backticks: \
            ```{insights}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        outline = self.chat(
            chat_prompt.format_prompt(insights=insights).to_messages()
        )

        return outline.content

    def create_blueprint(self, thesis_statement, insights):
        system_template = """You are a helpful AI blogger who writes essays on technical topics."""
        system_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """Given the provided thesis statement and list of key points, reorganize \
            and condense the information into a logical, coherent blueprint for an essay. Output a \
            JSON object where each key is a section heading and each value is a list of key points \
            to cover relevant to that section. All sections must support the thesis statement. \
            Do not include any information that has little to do with the thesis statement. \
            Only output the final JSON object and nothing else. Do not format the output. \
            The thesis statement is : "{thesis_statement}" and the key insights are delimited \
            in triple backticks below: \
            ```{insights}```"""
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        outline = self.chat(
            chat_prompt.format_prompt(
                thesis_statement=thesis_statement, insights=insights
            ).to_messages()
        )

        return outline.content

    # @timer_decorator
    def full_transcript2blueprint(self, verbose=True):
        print("Chunking transcript...")
        transcript_docs = self.transcript_splitter()
        t1 = time.time()
        print("Extracting key insights...")
        essay_insights = self.create_essay_insights(transcript_docs)
        t2 = time.time() - t1
        print("Extracting thesis statement...")
        t1 = time.time()
        thesis_statement = self.extract_thesis_statement(essay_insights)
        t3 = time.time() - t1
        print("Creating essay...")
        t1 = time.time()
        essay = self.create_blueprint(thesis_statement, essay_insights)
        t4 = time.time() - t1
        if verbose:
            print(f"Extracted essay insights in {t2:.2f} seconds")
            print(f"Extracted thesis statement in {t3:.2f} seconds")
            print(f"Created essay blueprint in {t4:.2f} seconds")
        return essay


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

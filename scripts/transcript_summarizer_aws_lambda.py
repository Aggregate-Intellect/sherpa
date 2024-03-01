import json
import boto3
import os

from os import environ

from loguru import logger
# destination_bucket = "transcriptslangchain"
destination_bucket = os.environ['destination_bucket']




ACCESS_KEY = environ.get('ACCESS_KEY')  
SECRET_KEY = environ.get('SECRET_KEY') 
REGION_NAME = environ.get('REGION_NAME')
OPENAI_API_KEY = environ.get('OPENAI_API_KEY')


import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
import time
#import docx
from langchain.text_splitter import MarkdownTextSplitter
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

import json

#import api_keys

# instantiate chat model
chat = ChatOpenAI(
  openai_api_key=OPENAI_API_KEY,
  temperature=0,
  model='gpt-3.5-turbo')

"""# Part **1**: Processing raw transcript"""


def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
  """Returns the number of tokens in a text string."""
  encoding = tiktoken.get_encoding(encoding_name)
  num_tokens = len(encoding.encode(string))
  return num_tokens

"""## Splitting raw transcript
ChatGPT models have a token limit. For GPT3.5-turbo, the limit is 4096 tokens [(docs)](https://platform.openai.com/docs/models/gpt-3-5). Most transcripts exceed that, so it must be split into chunks.
"""
def transcript_splitter(raw_transcript, chunk_size=10000, chunk_overlap=200):
  markdown_splitter = MarkdownTextSplitter(
      chunk_size=chunk_size, chunk_overlap=chunk_overlap)
  transcript_docs = markdown_splitter.create_documents([raw_transcript])
  return transcript_docs


def transcript2essay(transcript, chat_model=chat):
  system_template = "You are a helpful assistant that summarizes a transcript of podcasts or lectures."
  system_prompt = SystemMessagePromptTemplate.from_template(system_template)
  # human_template = "Summarize the main points of this presentation's transcript: {transcript}"
  human_template = """Rewrite the contents and information of the presentation into a well written essay.\
  Write the essay as if the speaker wrote it himself from the same knowledge he used to create the presentation. \
  Include the speaker's full name in the essay and refer to him/her with the full name. \
  Also include the names of the people who asked questions and the questions they asked. \
  The transcript of this presentation is delimited in triple backticks:
  ```{transcript}```"""
  human_prompt = HumanMessagePromptTemplate.from_template(human_template)
  chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

  result = chat_model(chat_prompt.format_prompt(transcript=transcript).to_messages())
  return result.content



def qa2essay_bkp(transcript,summarized_essay, chat_model=chat):
  system_template = "You are a helpful assistant that summarizes a transcript of QA section of podcasts or lectures."
  system_prompt = SystemMessagePromptTemplate.from_template(system_template)
  # human_template = "Summarize the main points of this presentation's transcript: {transcript}"
#   human_template = """Rewrite the contents and information of the presentation into a well written essay.\
#   Write the essay as if the speaker wrote it himself from the same knowledge he used to create the presentation. \
#   Include the speaker's full name in the essay and refer to him/her with the full name. \
#   Also include the names of the people who asked questions and the questions they asked. \
#   The transcript of this presentation is delimited in triple backticks:
#   ```{transcript}```"""
  human_template = """Rewrite the Questions and answers section of the presentation that outputs the same number of questions and answers in a summarized way.\
  Make sure you keep the same number of question and answers. Assume that the only one asking questions is the host, and the only one answering is speakers.\
  sometimes the same answer is broken down in few lines. Below is the question and answers section \
  ```{transcript}``` The next section is the summarized section on which question and answers \
  are been discussed, use this for summarizing the question and answers \
  section """ + summarized_essay
  human_prompt = HumanMessagePromptTemplate.from_template(human_template)
  chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
  result = chat_model(chat_prompt.format_prompt(transcript=transcript).to_messages())
  return result.content

def qa2essay(transcript,summarized_essay, chat_model=chat):
  system_template = "You are a helpful assistant that summarizes a transcript of QA section of podcasts or lectures."
  system_prompt = SystemMessagePromptTemplate.from_template(system_template)
  human_template = """ You are given a transcript that is a conversation of the question and answer. \
  Create a list of question and answeres from it with the following instructions:\
  Some questions might be spread across multiple lines, so summarise them.\
  Do not use numbers instead use the format Question and Answer/speaker to list them down. \
  The transcript of this presentation is delimited in triple backticks: ```{transcript}```Use the summary to elaborate on the answers """ + summarized_essay
  human_prompt = HumanMessagePromptTemplate.from_template(human_template)
  chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
  result = chat_model(chat_prompt.format_prompt(transcript=transcript).to_messages())
  return result.content

def create_essay_parts(transcript_docs,chat_model=chat):
  essay_response = ''
  for i, text in enumerate(transcript_docs):
      essay = transcript2essay(text.page_content,chat_model=chat)
      essay_response = f'\n\n#Part {i+1}\n'.join([essay_response, essay])

  return essay_response

def create_qa_parts(transcript_docs,summarized_essay):
  essay_response = ''
  for i, text in enumerate(transcript_docs):
      essay = qa2essay(text.page_content,summarized_essay)
      essay_response = f'\n\n#Part {i+1}\n'.join([essay_response, essay])

  return essay_response

def merge_essays(essays, chat_model=chat):
  system_template = """You are a helpful assistant that summarizes and \
    processes large text information."""
  system_prompt = SystemMessagePromptTemplate.from_template(system_template)

  human_template = """Consolidate the multiple parts of the text into one \
  coherent essay or article that accurately captures the content of the multiple\
  parts without losing any information. Make sure to include the speaker's full name \
  and the questions asked by the audience as well as the response to those questions. \
  The entire text is delimited in triple backticks and the parts are divided by
  #heading:\n
  ```{essays}```"""
  human_prompt = HumanMessagePromptTemplate.from_template(human_template)
  chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

  final_essay = chat_model(chat_prompt.format_prompt(essays=essays).to_messages())

  return final_essay.content


# @timer_decorator
def full_transcript2essay(raw_transcript:str, chat_model=chat, verbose=True):
  logger.debug('Chunking transcript...')
  transcript_docs = transcript_splitter(raw_transcript)
  t1 = time.time()
  logger.debug('Creating essay parts...')
  essay_parts = create_essay_parts(transcript_docs, chat_model=chat)
  t2 = time.time()-t1
  logger.debug('Merging essay parts...')
  t1 = time.time()
  final_essay = merge_essays(essay_parts, chat_model=chat)
  t3 = time.time()-t1
  if verbose:
    logger.debug(f'Created essay parts in {t2:.2f} seconds')
    logger.debug(f'Merged essay parts in {t3:.2f} seconds')
  return final_essay


# @timer_decorator
def full_qa2essay(raw_transcript:str, summarized_essay:str,chat_model=chat, verbose=True):
  logger.debug('Chunking qa...')
  transcript_docs = transcript_splitter(raw_transcript)
  t1 = time.time()
  logger.debug('Creating qa parts...')
  qa_parts = create_qa_parts(transcript_docs,summarized_essay)#, chat_model=chat)
  t2 = time.time()-t1
#   logger.debug('Merging essay parts...')
#   t1 = time.time()
#   final_essay = merge_essays(essay_parts, chat_model=chat)
#   t3 = time.time()-t1
  if verbose:
    logger.debug(f'Created qa parts in {t2:.2f} seconds')
    #logger.debug(f'Merged essay parts in {t3:.2f} seconds')
  return qa_parts


# """# Part 2: Extracting from essay"""

def extract_qa_metadata_as_json(essay, chat_model=chat):

  system_template = """ Given the question answers section, \
  Format the response as a JSON object, with the keys 'Question, 'Answer', 'Speaker', \
  Example of JSON output: \n \
  {{\
  'Question': '',\
  'Answer': 
  }}"""
    
    
  system_prompt = SystemMessagePromptTemplate.from_template(system_template)

  human_template = """Essay: ```{text}```"""

  human_prompt = HumanMessagePromptTemplate.from_template(human_template)
  chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

  result = chat_model(chat_prompt.format_prompt(text=essay).to_messages())
  try:
    metadata_json = json.loads(result.content)
  except Exception as e:
    logger.debug(e)
    metadata_json = result.content  
  return metadata_json


# """# Part 2: Extracting from essay"""

def extract_metadata_as_json(essay, chat_model=chat):

  system_template = """ Given the essay delimited in triple backticks, generate and extract important \
  information such as the title, speaker, summary, a list of key topics, \
  and a list of important takeaways for each topic. \
  Format the response as a JSON object, with the keys 'Title', 'Topics', 'Speaker', \
  'Summary', and 'Topics' as the keys and each topic will be keys for list of takeaways. \
  Example of JSON output: \n \
 {{\
  'Title': 'Title of the presentation',\
  'Speaker': 'John Smith',\
  'Summary': 'summary of the presentation',\
  'Topics': [\
  {{\
  'Topic': 'topic 1',\
  'Takeaways': [\
  'takeaway 1',\
  'takeaway 2',\
  'takeaway 3'\
  ]\
  }},\
  {{\
  'Topic': 'topic 2',\
  'Takeaways': [\
  'takeaway 1',\
  'takeaway 2',\
  'takeaway 3'\
  ]\
  }},\
  {{\
  'Topic': 'topic 3',\
  'Takeaways': [\
  'takeaway 1',\
  'takeaway 2',\
  'takeaway 3'\
  ]\
  }},\
  {{\
  'Topic': 'topic 4',\
  'Takeaways': [\
  'takeaway 1',\
  'takeaway 2',\
  'takeaway 3'\
  ]\
  }}\
  ]\
  }}"""

  system_prompt = SystemMessagePromptTemplate.from_template(system_template)

  human_template = """Essay: ```{text}```"""

  human_prompt = HumanMessagePromptTemplate.from_template(human_template)
  chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

  result = chat_model(chat_prompt.format_prompt(text=essay).to_messages())
  try:
    metadata_json = json.loads(result.content)
  except Exception as e:
    logger.debug(e)
    metadata_json = result.content  
  return metadata_json

def json2rst(metadata, rst_filepath):
  logger.debug(metadata)
  if not isinstance(metadata, dict):
      metadata = json.loads(metadata)
  logger.debug(metadata)
  # rst_filepath = './essays/test.rst'
  with open(rst_filepath, 'a') as the_file:
      the_file.write("\n\n")
      for key, value in metadata.items():
          logger.debug("jsong2rst", key, value)
          if key == "Title":
              title_mark = "=" * len(f'{value}')
              the_file.write(title_mark + '\n')
              the_file.write(f"{value} \n")
              the_file.write(title_mark + '\n')
          elif key == "Speaker":
              the_file.write('*' + f"{value}" + '* \n\n')
          elif key == "Summary":
              title_mark = '-' * len(f'{key}')
              the_file.write("Summary \n")
              the_file.write(title_mark + '\n')
              the_file.write(f"{value} \n\n")
          elif key == "Topics":
              the_file.write("Topics: \n")
              the_file.write(title_mark + '\n')
              for topic in value:
                  the_file.write("\t" + f"{topic['Topic']} \n")
                  for takeaway in topic['Takeaways']:
                      the_file.write("\t\t" + f"* {takeaway} \n")
          elif key == "Question":
              the_file.write("Question: \n")
              the_file.write(title_mark + '\n')
              the_file.write(f"{value}\n\n")
          elif key == "Answer":
              the_file.write("Answer: \n")
              the_file.write(title_mark + '\n')
              the_file.write(f"{value}\n\n")



def lambda_handler(event,context):
  # TODO implement



     #Retrieve the source and destination bucket names from the event
    source_bucket = event['Records'][0]['s3']['bucket']['name']

    # Retrieve the key (filename) of the object that triggered the Lambda function
    source_key = event['Records'][0]['s3']['object']['key']


    # ACCESS_KEY	= os.environ['ACCESS_KEY'] 
    # SECRET_KEY	= os.environ['SECRET_KEY'] 
    #s3_client = boto3.client('s3')
    s3_client = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
    )

    logger.debug(source_bucket)
    logger.debug(source_key)


    # response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    # docx_file = response['Body'].read()

    # # Load the DOCX file using the python-docx library
    # document = Document(io.BytesIO(docx_file))

    # # Extract text from the document
    # text = '\n'.join([paragraph.text for paragraph in document.paragraphs])

    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(text)
    # }

    # Read the file content from the source bucket
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    logger.debug("Response :",response)
    #file_content = response['Body'].read().decode('utf-8')
    try:
        logger.debug("In Try")
        raw_transcript = response['Body'].read().decode('utf-8')
    except UnicodeDecodeError as e:
        logger.debug("In exception")
        raw_transcript = response['Body'].read().decode('utf-8', errors='replace')


    # qa_index = raw_transcript.find("## QUESTION ANSWERING SECTION")
    
    # Find the indices where each section starts
    talk_index = raw_transcript.find("# TALK") + len("# TALK\n")
    qa_index = raw_transcript.find("## QUESTION ANSWERING SECTION") + len("## QUESTION ANSWERING SECTION\n")
    
    # Extract each section using slicing
    first_part = raw_transcript[talk_index:qa_index].strip()
    second_part = raw_transcript[qa_index:].strip()

    # logger.debug("Raw Transcript : ",raw_transcript)
    logger.debug("----first_part : ",first_part)
    logger.debug("---- Second part : ", second_part)
    
    
        # takes about 2-3 minutes to run
    #summary= full_transcript2essay(raw_transcript)
    summary= full_transcript2essay(first_part) #considering only talk part

    logger.debug("Summary : ",summary)
    
    qa_summarized = full_qa2essay(second_part,summary)
    logger.debug("------ Second part : ",second_part)
    logger.debug("------ QA Summarized : ",qa_summarized)
    
    
     # save metadata to file
    qa_filepath = r'/tmp/test_qa_summarized.txt'
    with open(qa_filepath, 'w') as file:
        json.dump(qa_summarized, file)
    
     # 17 seconds to run
    logger.debug('Extracting metadata...')
    qa_metadata = extract_qa_metadata_as_json(qa_summarized, chat_model=chat)

    # save metadata to file
    qa_metadata_filepath = r'/tmp/test_qa_metadata.json'
    with open(qa_metadata_filepath, 'w') as file:
        json.dump(qa_metadata, file)

    logger.debug("--- qa_metadata", qa_metadata)

    logger.debug('Extracting metadata...')
    metadata = extract_metadata_as_json(summary, chat_model=chat)

    output_json = r'/tmp/output_json.json'


    # save metadata to file
    metadata_filepath = r'/tmp/test_metadata.json'
    with open(metadata_filepath, 'w') as file:
        json.dump(metadata, file)

    logger.debug(metadata)

    try:
        with open(qa_metadata_filepath, 'r') as f:
            source_data = json.load(f)

        # Read content from target JSON file
        with open(metadata_filepath, 'r') as f:
            target_data = json.load(f)

        # Merge dictionaries
        merged_data = {**target_data, **source_data}

        # Write merged data to output JSON file
        with open(output_json, 'w') as f:
            json.dump(merged_data, f, indent=4)

        logger.debug(f"Content from '{metadata}' merged to '{qa_metadata}' successfully.")
    except Exception as e:
       pass
    # convert metadata from json to rst
    rst_filepath = r'/tmp/test.rst'
    try:
      output_to_json = ''
      with open(output_json, 'r') as file:
         output_to_json = json.load(file)
      logger.debug("outputJson",output_json)
      json2rst(output_to_json, rst_filepath)
      destination_key = source_key.split(".")[0] +".rst"
      #s3_client.upload_file(rst_filepath, destination_bucket, destination_key)
      file_path = rst_filepath
    except Exception as e:
      logger.debug("Parsing error from Json to Rst for file :", source_key)
      destination_key = source_key.split(".")[0] +".json"
      file_path = metadata_filepath

    
    s3_client.upload_file(file_path, destination_bucket, destination_key)


    logger.debug(destination_key)


    return {
        'statusCode': 200,
        'body': json.dumps('Rst file comversion successful !!!')
    }

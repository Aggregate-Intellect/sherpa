import json
import boto3
destination_bucket = "transcriptslangchain"
import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain

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
imoprt config as cfg
import json

#import api_keys

# instantiate chat model
chat = ChatOpenAI(
  openai_api_key=cfg.OPENAI_API_KEY,
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

def create_essay_parts(transcript_docs):
  essay_response = ''
  for i, text in enumerate(transcript_docs):
      essay = transcript2essay(text.page_content)
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
  print('Chunking transcript...')
  transcript_docs = transcript_splitter(raw_transcript)
  t1 = time.time()
  print('Creating essay parts...')
  essay_parts = create_essay_parts(transcript_docs, chat_model=chat)
  t2 = time.time()-t1
  print('Merging essay parts...')
  t1 = time.time()
  final_essay = merge_essays(essay_parts, chat_model=chat)
  t3 = time.time()-t1
  if verbose:
    print(f'Created essay parts in {t2:.2f} seconds')
    print(f'Merged essay parts in {t3:.2f} seconds')
  return final_essay


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
    print(e)
    metadata_json = result.content  
  return metadata_json

def json2rst(metadata, rst_filepath):
  if not isinstance(metadata, dict):
      metadata = json.loads(metadata)
  
  # rst_filepath = './essays/test.rst'
  with open(rst_filepath, 'a') as the_file:
      the_file.write("\n\n")
      for key, value in metadata.items():
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



def lambda_handler(event,context):
  # TODO implement
    
     #Retrieve the source and destination bucket names from the event
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    
    # Retrieve the key (filename) of the object that triggered the Lambda function
    source_key = event['Records'][0]['s3']['object']['key']
    
    
    #s3_client = boto3.client('s3')
    s3_client = boto3.client(
      's3',
      aws_access_key_id=cfg.AWS_ACCESS_KEY,
      aws_secret_access_key=cfg.AWS_SECRET_KEY
    )
    
    print(source_bucket)
    print(source_key)
    
    # Read the file content from the source bucket
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    #file_content = response['Body'].read().decode('utf-8')
    try:
        raw_transcript = response['Body'].read().decode('utf-8')
    except UnicodeDecodeError as e:
        raw_transcript = response['Body'].read().decode('utf-8', errors='replace')
        
        # takes about 2-3 minutes to run
    summary= full_transcript2essay(raw_transcript)

    # 17 seconds to run
    print('Extracting metadata...')
    metadata = extract_metadata_as_json(summary, chat_model=chat)

    # save metadata to file
    metadata_filepath = r'/tmp/test_metadata.json'
    with open(metadata_filepath, 'w') as file:
        json.dump(metadata, file)

    print(metadata)
    # convert metadata from json to rst
    rst_filepath = r'/tmp/test.rst'
    try:
      json2rst(metadata, rst_filepath)
      destination_key = source_key.split(".")[0] +".rst"
      #s3_client.upload_file(rst_filepath, destination_bucket, destination_key)
      file_path = rst_filepath
    except Exception as e:
      print("Parsing error from Json to Rst for file :", source_key)
      destination_key = source_key.split(".")[0] +".json"
      file_path = metadata_filepath
    
    s3_client.upload_file(file_path, destination_bucket, destination_key)

    
    print(destination_key)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Rst file comversion successful !!!')
    }


def lambda_handler_bkp(event, context):
    # TODO implement
    
     #Retrieve the source and destination bucket names from the event
    source_bucket = event['Records'][0]['s3']['bucket']['name']

    
    # Retrieve the key (filename) of the object that triggered the Lambda function
    source_key = event['Records'][0]['s3']['object']['key']
    
    
    #s3_client = boto3.client('s3')
    s3_client = boto3.client(
      's3',
      aws_access_key_id=cfg.AWS_ACCESS_KEY,
      aws_secret_access_key=cfg.AWS_SECRET_KEY
    )
    
    print(source_bucket)
    print(source_key)
    
    # Read the file content from the source bucket
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    #file_content = response['Body'].read().decode('utf-8')
    try:
        raw_transcript = response['Body'].read().decode('utf-8')
    except UnicodeDecodeError as e:
        raw_transcript = response['Body'].read().decode('utf-8', errors='replace')
    
    # takes about 2-3 minutes to run
    final_essay = full_transcript2essay(raw_transcript)
    
    print('Extracting metadata...')
    metadata = extract_metadata_as_json(final_essay)
    
    print("Extracting metadata completed")
    #print(metadata)
    
    
    
     # Convert the metadata dictionary to JSON string
    metadata_json = json.dumps(metadata)
    
    # Convert the JSON string to bytes
    metadata_bytes = metadata_json.encode('utf-8')
    

    print(type(metadata_json))
    print(metadata_json)
    
    rst_filepath = r'/tmp/test.rst'
    json2rst(metadata, rst_filepath)
    

    destination_key = "transcript_" + source_key.split(".")[0] +".rst"
    print(destination_key)
    
    s3_client.upload_file(rst_filepath, destination_bucket, destination_key)
    
  
    
    return {
        'statusCode': 200,
        'body': json.dumps('Rst file comversion successful !!!')
    }

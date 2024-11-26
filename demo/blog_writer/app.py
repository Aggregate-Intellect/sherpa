from venv import logger
import chainlit as cl
import json
import os
import pypandoc
import time
from box import Box
from argparse import ArgumentParser
from hydra.utils import instantiate
from omegaconf import OmegaConf
from outliner import Outliner
from sherpa_ai.agents import QAAgent, UserAgent
from sherpa_ai.events import EventType

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_text_splitters import MarkdownTextSplitter

directory_name = "Output"
if not os.path.exists(directory_name):
    os.mkdir(directory_name)
    logger.debug(f"Directory '{directory_name}' created successfully.")
else:
    logger.debug(f"Directory '{directory_name}' already exists.")


def get_qa_agent_from_config_file(
    config_path: str,
) -> QAAgent:
    """
    Create a QAAgent from a config file.

    Args:
        config_path: Path to the config file

    Returns:
        QAAgent: A QAAgent instance
    """

    config = OmegaConf.load(config_path)

    agent_config = instantiate(config.agent_config)
    qa_agent: QAAgent = instantiate(config.qa_agent, agent_config=agent_config)

    return qa_agent


def get_user_agent_from_config_file(
    config_path: str,
) -> UserAgent:
    """
    Create a UserAgent from a config file.

    Args:
        config_path: Path to the config file

    Returns:
        UserAgent: A UserAgent instance
    """

    config = OmegaConf.load(config_path)

    user: UserAgent = instantiate(config.user)

    return user


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/terminal.svg",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/write.svg",
        )
    ]


@cl.on_chat_start
async def on_chat_start():
    elements = [
        cl.File(name='transcript.txt',
                path='./Transcripts/transcript.txt', display="inline")
    ]
    content = 'What topic would you like to write your blog about, it is required to provide the transcript file like attached below! plus you can either attach a file like above or send the content it has inside the chat'
    await cl.Message(content=content, elements=elements).send()
    return [
        cl.Starter(
            label="Generate default",
            message="Generate default",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/terminal.svg",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/write.svg",
        )
    ]


async def blog_generator(message: cl.Message):
    # parser = ArgumentParser()
    # parser.add_argument("--config", type=str, default="agent_config.yaml")
    # parser.add_argument("--transcript", type=str, default="transcript.txt")
    # parser.add_argument("--blueprint", type=str,default="blueprint_sample.json", help="Optional JSON blueprint file to use")
    args = Box({

        "config": 'agent_config.yml',
        "transcript": 'transcript.txt',
        "blueprint": 'blueprint_sample.json'
    })
    transcript_path = f"Transcripts/transcript.txt"

    if not message.elements:
        with open(transcript_path, 'w') as f:
            f.write(message.content)
    else:
        for element in message.elements:
            content = ''
            with open(element.path, 'r') as f:
                content = f.read()
            with open(transcript_path, 'w') as f:
                f.write(content)
    logger.debug(transcript_path)
    base_name = os.path.splitext(os.path.basename(transcript_path))[0]
    json_output_path = f"Output/blueprint_{base_name}.json"
    md_output_path = f"Output/blog_{base_name}.md"

    blueprint_full_path = os.path.join("Output", args.blueprint)
    outliner = Outliner(args.transcript)

    if os.path.isfile(blueprint_full_path):
        blueprint = outliner.full_transcript2outline_json(verbose=True)

        with open(blueprint_full_path, 'r') as file:
            pure_json_str = file.read()
        logger.debug(f"Using existing blueprint from {blueprint_full_path}")
    else:
        logger.debug(
            f"No blueprint found at {blueprint_full_path}, creating a new blueprint.")
        # Assume outliner creates a new blueprint if not found
        blueprint = outliner.full_transcript2outline_json(verbose=True)
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(blueprint)
        logger.debug(f"Blueprint generated and saved to {json_output_path}")

    chat = ChatOpenAI(
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        temperature=0,
        model="gpt-3.5-turbo",
    )

    writer_agent = get_qa_agent_from_config_file(args.config)
    reviewer_agent = get_user_agent_from_config_file(args.config)

    async def write_from_json2md(data):

        personality_prompt = "You are an experienced AI practitioner with initials AF writing paragraphs for an article for a technical audience on a complex topic. \
            Each new section you write should be a coherent and continuous extension of the last section you wrote. \
            Your goal is to make the subject approachable, informative, and engaging, while maintaining your authoritative voice. \
            The article should be written in the first-person perspective, especially when receiving input sentences starting with initials AF, and include parts that explain topics objectively. \
            The input prompts you receive are from conversations with others, presented by their initials at the beginning of each sentence, to add depth and authenticity. \
            Your tone is conversational and informal. \
            Your tone engages the reader as if you're having a friendly chat to create a welcoming atmosphere. \
            Your voice is authoritative yet approachable. \
            You position yourself as an expert with practical experience. \
            You use direct quotes from interactions with clients to add authenticity and show your hands-on expertise. \
            You are confident in your knowledge without being overly technical or intimidating. \
            Your style is straightforward and direct. \
            You use simple language to explain technical concepts, making them easy to understand. \
            You structure your writing to first introduce the problem, then guide the reader through the rationale behind the thesis, and finally offer practical advice. \
            Use rhetorical questions and repetition to emphasize key points and keep the reader engaged. \
            You incorporate conversations with others to add depth and different perspectives. \
            For each prompt, use Google Search to find detailed information that supports and expands on the prompt."

        system_prompt = SystemMessagePromptTemplate.from_template(
            personality_prompt
        )

        blog = ""

        caps_prompt = "Follow these best practices to craft an effective opening and closing paragraph for an article written based on the outline shown below in json. \
        Mark the opening paragraph as introduction, and the closing paragraph as conclusion. \
        Best practices for the Opening Paragraph: 1) Hook the Reader by Starting with an engaging statement, question, or statistic that grabs attention. \
        2) Set the Context by Introducing the topic and its relevance, explaining why the subject matter is important. \
        3) State the Purpose by Clearly outlining what the article will cover. \
        4) Build Credibility by Mentioning any relevant experiences or expertise any of the people whose initials are mentioned have. \
        Best practices for the Closing Paragraph: 1) Summarize Key Points by Recapping the main takeaways of the article. \
        2) Provide a Call to Action by Encouraging the reader to apply what they have learned or seek further information. \
        3) End on a Positive Note by Leaving the reader with a sense of optimism or motivation. \
        4) Offer Additional Resources by Pointing the reader to further reading materials or communities. Outline: {outline}"

        human_prompt = HumanMessagePromptTemplate.from_template(caps_prompt)

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt, human_prompt]
        )

        result = chat(
            chat_prompt.format_prompt(
                outline=json.dumps(data, indent=4)).to_messages()
        )

        blog = result.content + "\n\n"

        for first_layer_key, first_layer_value in data.items():
            # Add H1 header for the first layer key
            markdown_input = f"# {first_layer_key}\n\n"

            for second_layer_key, second_layer_value in first_layer_value.items():
                # Add H2 header for the second layer key + Join the list of strings with a space between them
                markdown_input += f"## {second_layer_key}\n\n" + \
                    ' '.join(second_layer_value) + "\n\n"

            logger.debug(">>>>> input >>>> : " + markdown_input)

            # Execute the write function on the resulting string

            body_prompt = "Write the section of an article in markdown format based on the starter section provided below. \
                Rewrite the information in the starter paragraph for better flow and readability and add support to it from information retrieved by the actions. \
                Maintain the structure of the starter paragraph. \
                Write two paragraphs per subsection and each paragraph should have 4 to 5 sentences. \
                Add one new line between section headers, subsection headers and paragraphs. \
                You may keep one of the sentences provided as a verbatim quote by attributing it to the persons's initials provided at the beginning of the sentence. \
                Starter Section: {section}"

            human_prompt = HumanMessagePromptTemplate.from_template(
                body_prompt)

            chat_prompt = ChatPromptTemplate.from_messages(
                [system_prompt, human_prompt]
            )

            # reviewer_input = (
            #     "\n"
            #     "Please review the paragraph generated below. "
            #     "Type 'yes', 'y' or simply press Enter if everything looks good. "
            #     "Else provide feedback on how you would like the paragraph changed."
            #     "\n\n" + markdown_input
            # )
            # reviewer_agent.shared_memory.add(EventType.task, "human", reviewer_input)

            # decision = reviewer_agent.run()
            # decision_event = reviewer_agent.shared_memory.get_by_type(EventType.result)
            # decision_content = decision_event[-1].content

            # if decision_content == []:
            #     break
            # #
            # if decision_content.lower() in ["yes", "y", ""]:
            #     pass
            # else:
            #     writer_agent.shared_memory.add(EventType.task, "human", decision_content)

            result = chat(
                chat_prompt.format_prompt(section=markdown_input).to_messages()
            )

            markdown_output = result.content

            blog += markdown_output + "\n\n"

        return blog

    blog = await write_from_json2md(blueprint)
    logger.debug(blog)
    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(blog)
    return blog, md_output_path


@cl.on_message
async def main(message: cl.Message):
    logger.debug("new")
    blog, md_output_path = await blog_generator(message)
    with open(md_output_path, 'r') as f:
        elements = [cl.File(name='blog_transcript.md', path='./Transcripts/blog_transcript.md', display="inline")]
     
    await cl.Message(
        content=blog,
        elements=elements
    ).send()

import json
import os
import pypandoc

from argparse import ArgumentParser
from hydra.utils import instantiate
from omegaconf import OmegaConf
from outliner import Outliner
from sherpa_ai.agents import QAAgent, UserAgent
from sherpa_ai.events import EventType

from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from langchain.text_splitter import MarkdownTextSplitter

#create Output folder
directory_name = "Output"
if not os.path.exists(directory_name):
    os.mkdir(directory_name)
    print(f"Directory '{directory_name}' created successfully.")
else:
    print(f"Directory '{directory_name}' already exists.")

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


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="agent_config.yaml")
    parser.add_argument("--transcript", type=str, default="transcript.txt")
    parser.add_argument("--blueprint", type=str, help="Optional JSON blueprint file to use")
    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.transcript))[0]
    json_output_path = f"Output/blueprint_{base_name}.json"
    md_output_path = f"Output/blog_{base_name}.md"
    
    if args.blueprint:
        blueprint_full_path = os.path.join("Output", args.blueprint)
        if os.path.isfile(blueprint_full_path):
            with open(blueprint_full_path, 'r') as file:
                pure_json_str = file.read()
            print(f"Using existing blueprint from {blueprint_full_path}")
        else:
            print(f"No blueprint found at {blueprint_full_path}, creating a new blueprint.")
            # Assume outliner creates a new blueprint if not found
            outliner = Outliner(args.transcript)
            blueprint = outliner.full_transcript2outline_json(verbose=True)
            with open(json_output_path, "w", encoding="utf-8") as f:
                f.write(blueprint)
            print(f"Blueprint generated and saved to {json_output_path}")
    else:
        # If no blueprint file is specified, proceed with creating a new one
        outliner = Outliner(args.transcript)
        blueprint = outliner.full_transcript2outline_json(verbose=True)
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(blueprint, indent=2))
        print(f"Blueprint generated and saved to {json_output_path}")


    chat = ChatOpenAI(
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0,
            model="gpt-3.5-turbo",
        )
        
    writer_agent = get_qa_agent_from_config_file(args.config)
    reviewer_agent = get_user_agent_from_config_file(args.config)

    def write_from_json2md(data):

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
            chat_prompt.format_prompt(outline=json.dumps(data, indent=4)).to_messages()
        )
        
        blog = result.content + "\n\n"

        for first_layer_key, first_layer_value in data.items():
            # Add H1 header for the first layer key
            markdown_input = f"# {first_layer_key}\n\n"
            
            for second_layer_key, second_layer_value in first_layer_value.items():
                # Add H2 header for the second layer key + Join the list of strings with a space between them
                markdown_input += f"## {second_layer_key}\n\n" + ' '.join(second_layer_value) + "\n\n"
                
            print(">>>>> input >>>> : " + markdown_input)

            # Execute the write function on the resulting string

            body_prompt = "Write the section of an article in markdown format based on the starter section provided below. \
                Rewrite the information in the starter paragraph for better flow and readability and add support to it from information retrieved by the actions. \
                Maintain the structure of the starter paragraph. \
                Write two paragraphs per subsection and each paragraph should have 4 to 5 sentences. \
                Add one new line between section headers, subsection headers and paragraphs. \
                You may keep one of the sentences provided as a verbatim quote by attributing it to the persons's initials provided at the beginning of the sentence. \
                Starter Section: {section}"
            
            human_prompt = HumanMessagePromptTemplate.from_template(body_prompt)
            
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_prompt, human_prompt]
            )

            result = chat(
                chat_prompt.format_prompt(section=markdown_input).to_messages()
            )

            markdown_output = result.content

            # reviewer_input = (
            #     "\n"
            #     "Please review the paragraph generated below. "
            #     "Type 'yes', 'y' or simply press Enter if everything looks good. "
            #     "Else provide feedback on how you would like the paragraph changed."
            #     "\n\n" + processed_string
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
            #     processed_string = writer_agent.run()


            blog += markdown_output + "\n\n"
                
        return blog

    blog = write_from_json2md(blueprint)

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(blog)

    def convert_output_file(md_output_path,desired_format="pdf"):
        pypandoc.convert(md_output_path,desired_format)

    convert_output_file(md_output_path,desired_format="pdf")

    print("\nBlog generated successfully!\n")

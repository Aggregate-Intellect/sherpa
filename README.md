# Practical Large Language Models: What can you do with LLMs at home?
This repo contains material and information from the workshop run by [Aggregate Intellect](https://ai.science) to update and educate our community about the explosive progress in language models (and generally generative models). We will continue adding material to this repository, but feel free to add any questions or suggestions through pull requests or through reporting issues. 

**Table of Contents**
Follow the gif below to find the table of contents on the top left corner of this pane. 
![Table of Contents](https://github.com/Aggregate-Intellect/practical-llms/blob/main/Peek%202023-03-10%2007-59.gif)

---

## The Emergence of KnowledgeOps

DevOps and ModelOps have transformed software development over the past two decades, but now we are seeing a further shift left with the rise of KnowledgeOps. This new era leverages tools to augment our problem-solving, planning, and critical thinking abilities, enabling us to tackle highly complex knowledge work with greater efficiency and effectiveness. KnowledgeOps promises to enhance our ability to experiment with a wider range of ideas and select the most impactful ones, similar to the benefits seen in DevOps and related methodologies.

[Amir Feizpour](https://www.linkedin.com/in/amirfzpr/) (CEO @ Aggregate Intellect)

Amir is the co-founder of Aggregate Intellect ([https://ai.science/](https://ai.science/)), a Smart Knowledge Navigator platform for R&D teams in emerging technologies like AI. Prior to this, Amir was an NLP Product Lead at Royal Bank of Canada, and held a postdoctoral position at University of Oxford conducting research on experimental quantum computing. Amir holds a PhD in Physics from University of Toronto.

---

## Integrating LLMs into Your Product: Considerations and Best Practices

The proliferation of ChatGPT and other large language models has resulted in an explosion of LLM-based projects and startups. While these models can provide impressive initial demos, integrating them into a product requires careful consideration and planning. This talk will cover key considerations for creating, testing, and optimizing prompts for LLMs, as well as how to run analytics on key user metrics to ensure success.

_Material_
- [Talk Slides](https://pitch.com/public/7fce9d3f-fec7-40f5-9273-99ff1655a4e8)
- [Prompt Engineering Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)
- [How GPT3 Works - Visualizations and Animations](https://jalammar.github.io/how-gpt3-works-visualizations-animations/)
- [Open AI Product](https://openai.com/product)

[Denys Linkov](https://www.linkedin.com/in/denyslinkov/) (ML Lead @ Voiceflow)

Denys is the ML lead at Voiceflow focused on building the ML platform and data science offerings. His focus is on realtime NLP systems that help Voiceflow’s 60+ enterprise customers build better conversational assistants. Previously he worked at large bank as a senior cloud architect.

---

## LLMOps: Expanding the Capabilities of Language Models with External Tools

This talk explores how language models can be integrated with external tools, such as Python interpreters, API's, and data stores, to greatly expand their utility. We will examine the emerging field of 'LLMOps' and review some promising tools. Additionally, we will push the boundaries of what's possible by exploring how a language model could accurately answer complex questions like, "Who was the CFO at Apple when its stock price was at its lowest point in the last 10 years?"

_Material_
- [Augmented Language Models: a Survey](https://arxiv.org/abs/2302.07842)
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- [Iterated Decomposition: Improving Science Q&A by Supervising Reasoning Processes](https://arxiv.org/abs/2301.01751)
- [Demonstrate-Search-Predict: Composing retrieval and language models for knowledge-intensive NLP](https://arxiv.org/abs/2212.14024)
- [LangChain Docs](https://langchain.readthedocs.io/en/latest/)
- [LlamaIndex (formerly GPT-Index](https://gpt-index.readthedocs.io/en/latest/index.html)

[Suhas Pai](https://www.linkedin.com/in/piesauce/) (CTO @ Bedrock AI)

Suhas is the CTO & Co-founder of Bedrock AI, an NLP startup operating in the financial domain, where he conducts research on LLMs, domain adaptation, text ranking, and more. He was the co-chair of the Privacy WG at BigScience, the chair at TMLS 2022 and TMLS NLP 2022 conferences, and is currently writing a book on Large Language Models.

---

## Leveraging Language Models for Training Data Generation and Tool Learning

An emerging aspect of large language models is their ability to generate datasets that allow them to self-improve. A fascinating recent example is Toolformer ([Schick et al.](https://arxiv.org/abs/2302.04761)) in which LLMs generate fine-tuning data that helps them learn how to use tools at run-time. In this talk, we’ll examine this trend by taking a close look at the Toolformer paper and other related research.

_Material_
- [Large Language Models Can Self-Improve](https://arxiv.org/abs/2210.11610)
- [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)

[Gordon Gibson](https://www.linkedin.com/in/gordon-gibson-874b3130/) (ML Lead @ Ada)

Gordon is the Senior Engineering Manager of the Applied Machine Learning team at Ada where he's helped lead the creation of Ada's ML engine and features. Gordon's background is in Engineering Physics and Operations Research, and he's passionate about building useful ML products.

---

## Optimizing Large Language Models with Reinforcement Learning-Based Prompts

Large language models (LLMs) have the potential to perform a wide range of tasks by understanding human queries, but they are often sensitive to the wording of the prompts, which can greatly affect the output. This talk will introduce RLPrompt, an efficient algorithm that uses reinforcement learning to systematically search for the best prompts to improve LLM performance across diverse tasks.

_Material_
- RLPrompt: Optimizing Discrete Text Prompts with Reinforcement Learning [blog](https://blog.ml.cmu.edu/2023/02/24/rlprompt-optimizing-discrete-text-prompts-with-reinforcement-learning/) | [paper](https://arxiv.org/abs/2205.12548) | [code](https://github.com/mingkaid/rl-prompt)
- [Prefix-Tuning: Optimizing Continuous Prompts for Generation](https://arxiv.org/abs/2101.00190)
- [Making Pre-trained Language Models Better Few-shot Learners](https://aclanthology.org/2021.acl-long.295.pdf)
- [Prompt Waywardness: The Curious Case of Discretized Interpretation of Continuous Prompts](https://arxiv.org/abs/2112.08348)
- [A Recipe For Arbitrary Text Style Transfer with Large Language Models](https://arxiv.org/abs/2109.03910)

[Mingkai Deng](https://www.linkedin.com/in/mingkaideng/) (PhD Student @ CMU)

Mingkai Deng is a PhD student at Carnegie Mellon University working at the intersection of machine learning, computer vision, and natural language processing. Prior to that, he was a data scientist who led award-winning projects and built analytics products that serve multiple Fortune 500 clients.

---

## Commercializing LLMs: Lessons and Ideas for Agile Innovation

In this talk, Josh, an ML expert with experience commercializing NLP-powered services, will discuss the potential for leveraging foundation models to drive agile innovation in both individual and organizational processes. He will share lessons learned from his work with a bootstrapped startup and provide insights on how LLMs can be commercialized effectively.

[Josh Seltzer](https://www.linkedin.com/in/josh-seltzer/) (CTO @ Nexxt Intelligence)

Josh is the CTO at Nexxt Intelligence, where he leads R&D on LLMs and NLP to build innovative solutions for the market research industry. He also works in biodiversity and applications of AI for conservation.

_Material_
- [Which Model Shall I Choose? Cost/Quality Trade-offs for Text Classification Tasks](https://arxiv.org/abs/2301.07006)
- [Canada Government Business Benefits Finder](https://innovation.ised-isde.canada.ca/innovation/s/?language=en_CA)
- [Understanding UK Artificial Intelligence R&D commercialisation and the role of standards](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1079959/DCMS_and_OAI_-_Understanding_UK_Artificial_Intelligence_R_D_commercialisation__accessible.pdf)

---

## Incorporating Large Language Models into Enterprise Analytics: Navigating the Landscape of In-Context Learning and Agents

Large Language Models (LLMs) have dramatically changed our expectations for AI. While a few innovators are building proof-of-concept projects using APIs, most enterprise analytic teams still need to figure out how to incorporate LLMs into their analytical toolbox. Rajiv shows the necessity of understanding the growth of "in-context learning" and agents. With these insights, he explains how LLMs will shape enterprise analytics. Along the way, he covers many practical factors, such as the different providers of LLMs, resource costs, and ethical issues.

_Material_
- [Talk Slides](https://github.com/Aggregate-Intellect/practical-llms/blob/main/Enterprise_LLMs_Shah.pdf)
- [Sentiment Spin: Attacking Financial Sentiment with GPT-3](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4337182)
- [Is ChatGPT a General-Purpose Natural Language Processing Task Solver?](https://arxiv.org/abs/2302.06476)
- [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165)
- [News Summarization and Evaluation in the Era of GPT-3](https://arxiv.org/abs/2209.12356)
- [Benchmarking Large Language Models for News Summarization](https://arxiv.org/abs/2301.13848)
- [BIG-Bench - Beyond the Imitation Game Benchmark](https://github.com/google/BIG-bench/)
- [Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them](https://arxiv.org/abs/2210.09261)
- [ChatGPT for Robotics: Design Principles and Model Abilities](https://www.microsoft.com/en-us/research/group/autonomous-systems-group-robotics/articles/chatgpt-for-robotics/)
- [Replicate MRKL chain uding LangChain](https://langchain.readthedocs.io/en/latest/modules/agents/implementations/mrkl.html)
- [Experimental Evidence on the Productivity Effects of Generative Artificial Intelligence](https://economics.mit.edu/sites/default/files/inline-files/Noy_Zhang_1.pdf)
- [The CEO’s Guide to the Generative AI Revolution](https://www.bcg.com/publications/2023/ceo-guide-to-ai-revolution)
- [A New Era of Creativity: Expert-in-the-loop Generative AI](https://multithreaded.stitchfix.com/blog/2023/03/06/expert-in-the-loop-generative-ai-at-stitch-fix/)

[Rajiv Shah](https://www.linkedin.com/in/rajistics/) (MLE @ Huggingface)

Rajiv is a machine learning engineer at Hugging Face, whose primary focus is on enabling enterprise teams to succeed with AI. He is a widely recognized speaker on enterprise AI and was part of data science teams at Snorkel AI, Caterpillar, and State Farm.

---

## Generative AI: Ethics and Accessibility

Generative AI has made impressive advances in creating music, art, and even virtual worlds that were once thought to be exclusively the domain of human creators. However, with such power comes great responsibility, and we must be mindful of the ethical implications of our creations. In this session, we will explore the intersection of generative AI, ethics, and accessibility. We will examine ethical considerations related to bias, transparency, and ownership, as well as the challenges of making generative AI accessible to individuals with disabilities and those from underrepresented communities.

[Noelle Russell](https://www.linkedin.com/in/noelleai/) (Global AI Solutions Lead @ Accenture)

Noelle Silver Russell is a multi-award-winning technologist and entrepreneur who specializes in advising companies on emerging technology, generative AI and LLMs. She is the Global AI Solutions Lead as well as the Global Industry Lead for Generative AI at Accenture. She has led teams at NPR, Microsoft, IBM, and Amazon Alexa, and is a consistent champion for AI literacy and the ethical use of AI based on her work building some of the largest AI models in the world. She is the founder of AI Leadership Institute and she was recently awarded the Microsoft Most Valuable Professional award for Artificial Intelligence as well as VentureBeat’s Women in AI Responsibility and Ethics award.

---

## Other Useful Resources
- [Aggregate Intellect Weekly Journal Club on NLP, GNN, etc](https://lu.ma/aisc-journal-club)
- [Augmented Thinking - A.I. Youtube Channel](https://www.youtube.com/@ai-science)

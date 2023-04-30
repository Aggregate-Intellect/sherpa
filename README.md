<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [PRACTICAL LARGE LANGUAGE MODELS (LLMs): AN OPEN BOOK PROJECT - INTRODUCTION](#practical-large-language-models-llms-an-open-book-project---introduction)
  - [What does "An Open Book Project" mean?](#what-does-an-open-book-project-mean)
- [KNOWLEDGE-OPS](#knowledge-ops)
  - [DevOps -> MLOps -> KnowledgeOps](#devops---mlops---knowledgeops)
  - [Rise of Autonomous Information Seeking Companions](#rise-of-autonomous-information-seeking-companions)
    - [Amir Feizpour (CEO @ Aggregate Intellect)](#amir-feizpour-ceo--aggregate-intellect)
- [LARGE LANGUAGE MODEL AGENTS - ONSET AGI?](#large-language-model-agents---onset-agi)
  - [LLMOps: Expanding the Capabilities of Language Models with External Tools](#llmops-expanding-the-capabilities-of-language-models-with-external-tools)
    - [Suhas Pai (CTO @ Bedrock AI)](#suhas-pai-cto--bedrock-ai)
  - [Leveraging Language Models for Training Data Generation and Tool Learning](#leveraging-language-models-for-training-data-generation-and-tool-learning)
    - [Gordon Gibson (ML Lead @ Ada)](#gordon-gibson-ml-lead--ada)
- [USE CASES](#use-cases)
  - [Commercializing LLMs: Lessons and Ideas for Agile Innovation](#commercializing-llms-lessons-and-ideas-for-agile-innovation)
    - [Josh Seltzer (CTO @ Nexxt Intelligence)](#josh-seltzer-cto--nexxt-intelligence)
  - [ChatGPT-like application for construction of mathematical financial models](#chatgpt-like-application-for-construction-of-mathematical-financial-models)
    - [Sina Shahandeh (Founder @ Plan with Flow)](#sina-shahandeh-founder--plan-with-flow)
- [LLM-OPS AND ENGINEERING](#llm-ops-and-engineering)
  - [Integrating LLMs into Your Product: Considerations and Best Practices](#integrating-llms-into-your-product-considerations-and-best-practices)
  - [Running LLMs in Your Environment](#running-llms-in-your-environment)
    - [Denys Linkov (ML Lead @ Voiceflow)](#denys-linkov-ml-lead--voiceflow)
- [LARGE LANGUAGE MODELS IN ENTERPRISES](#large-language-models-in-enterprises)
  - [Incorporating Large Language Models into Enterprise Analytics: Navigating the Landscape of In-Context Learning and Agents](#incorporating-large-language-models-into-enterprise-analytics-navigating-the-landscape-of-in-context-learning-and-agents)
    - [Rajiv Shah (MLE @ Huggingface)](#rajiv-shah-mle--huggingface)
- [RISK MITIGATION OF LARGE LANGUAGE MODELS](#risk-mitigation-of-large-language-models)
  - [Generative AI: Ethics, Accessibility, Legal Risk Mitigation](#generative-ai-ethics-accessibility-legal-risk-mitigation)
    - [Noelle Russell (Global AI Solutions Lead @ Accenture)](#noelle-russell-global-ai-solutions-lead--accenture)
- [LARGE LANGUAGE HANDS ON TUTORIALS AND RESOURCES](#large-language-hands-on-tutorials-and-resources)
  - [Building with LLMs Using LangChain - Hands-on](#building-with-llms-using-langchain---hands-on)
    - [Percy Chen (PhD Student @ McGill University)](#percy-chen-phd-student--mcgill-university)
- [THEORETICAL FOUNDATIONS OF LARGE LANGUAGE MDOELS](#theoretical-foundations-of-large-language-mdoels)
  - [Modern Innovations in Fine-Tuning Large Language Models](#modern-innovations-in-fine-tuning-large-language-models)
    - [Ehsan Kamalinejad (ML Scientist @ Amazon)](#ehsan-kamalinejad-ml-scientist--amazon)
  - [Optimizing Large Language Models with Reinforcement Learning-Based Prompts](#optimizing-large-language-models-with-reinforcement-learning-based-prompts)
    - [Mingkai Deng (PhD Student @ CMU)](#mingkai-deng-phd-student--cmu)
  - [Learning-free Controllable Text Generation for Debiasing](#learning-free-controllable-text-generation-for-debiasing)
    - [Fatemehsadat Mireshghallah (Post-doctoral Researcher @ UW)](#fatemehsadat-mireshghallah-post-doctoral-researcher--uw)
- [Contributions Guideline](#contributions-guideline)
  - [Making Changes through Pull Requests](#making-changes-through-pull-requests)
  - [Suggesting Changes through Issues](#suggesting-changes-through-issues)
- [Other Useful Resources](#other-useful-resources)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# PRACTICAL LARGE LANGUAGE MODELS (LLMs): AN OPEN BOOK PROJECT - INTRODUCTION

This repo contains material and information from the workshops and journal club sessions run by [Aggregate Intellect](https://ai.science) to update and educate our community about the explosive progress in language models (and generally generative models). Our vision for this repo is to be an authoritive source of information for those who want to leverage generative AI in their work and build regardless of how small or big their projects are. 

Our _mission_ is to create an ecosystem of experts, ideas, tools, and a community that build together until we get to a point where **no idea is too expensive to try**. 

## What does "An Open Book Project" mean?

We will continue adding material to this repository, but feel free to add any questions or suggestions through pull requests or through reporting issues.

Given the rapid pace of development in LLM space, we are releasing this information as an open book project which means that we welcome and encourage contributions from anyone who is interested and esp anyone who has used LLMs in production setting and wants to share their learnings with the broader community. See the bottom of this page for step by step instructions for how you can contribute.
Here are some examples of contributions you can make:

- If you are interested in this topic but you aren't an expert:
    - Fix typos or grammatical errors
    - Fix formatting issues
    - Rewords any sections to make them more understandable 
- If you are interested in this topic, and curious about how certain things can be done:
    - Provide feedback on existing content through _Issues_ (see the bottom of this page for details)
    - Ask questions or make suggestions through _Issues_ (see the bottom of this page for details)
- If you are closely familiar with the topic and / or have hands on experience:
    - Add new resources with explanation
    - Add notebooks with examples of interesting things you tried
    - Add new sections for important topics that are missing
    - Improving existing content by adding more detail or context

---

# KNOWLEDGE-OPS

## DevOps -> MLOps -> KnowledgeOps

DevOps and ModelOps have transformed software development over the past two decades, but now we are seeing a further shift left with the rise of KnowledgeOps. This new era leverages tools to augment our problem-solving, planning, and critical thinking abilities, enabling us to tackle highly complex knowledge work with greater efficiency and effectiveness. KnowledgeOps promises to enhance our ability to experiment with a wider range of ideas and select the most impactful ones, similar to the benefits seen in DevOps and related methodologies.

[SLIDES](https://github.com/Aggregate-Intellect/practical-llms/blob/main/KnowledgeOps/Knowledge-Ops.pdf) | [RECORDING](https://youtu.be/H3jZfLWpOZc)

**TWITTER THREAD SUMMARY OF THE TALK:**

- KnowledgeOps and Development Processes
    - 1/14: #KnowledgeOps is about managing an organization's or community’s knowledge assets and processes to enable reuse and collaboration. #DevOps and #ModelOps (#MLOps) are specific examples that help develop software faster and with lower chances of failure.
    - 2/14: #ShiftingLeft and #CI/CD are important #DevOps concepts that bring testing and quality assurance to the beginning of the software development process and provide tools to automate them for consistency and repeatability.
    - 3/14: Although automation has improved many parts of the development process, the step of discovering and planning is still largely manual, requiring continuous communication and collaboration with teammates, which creates a single point of failure.
    - 4/14: #ModelOps (e.g., #MLOps) has allowed for the automation of data and model handling, but the manual interpretation and decision-making steps are still present. #Automation
- Generative AI, and Continuous Exploration / Continuous Integration / Continuous Delivery 
    - 5/14: Generative AI can help us shift further left into the exploration, planning, and coding steps, significantly improving our ability to explore options and conduct experiments. #GenerativeAI #SoftwareDevelopment
    - 6/14: There will eventually be more automation in our problem-solving processes, but in the meantime, tools built with generative AI will significantly augment our ability for interpretation and decision-making in ensuring the success of the development of complex software systems. #MachineLearning #AI
    - 7/14: Emerging tools for thinking allow for a more experimental approach to knowledge-intensive work, allowing for continuous hypothesis generation and experimentation leading to CE/CI/CD. #ContinuousExploration #ContinuousIntegration #ContinuousDelivery
    - 8/14: There is a trend towards interfacing generative copilots, retrieval systems, and other knowledge-intensive systems to create thinking machines with memory and reasoning skills. #GenerativeAI #RetrievalSystems #Reasoning
    - 9/14: Language models are essential for these tools because they need to interpret users’ instructions usually provided in natural language, communicate results, and facilitate human-human communication. #LanguageModels #Communication
    - 10/14: Language models can give us the ability to articulate and communicate complex ideas effectively to stakeholders and team members enabling more efficient problem solving in communities and organizations. #LanguageModels #Communication
- Adoption of Knowledge-Ops
    - 11/14: In bigger companies, beyond technology, the biggest barriers to implementing #KnowledgeOps are cultural problems; eg. political reasons that prevent a unified and integrated knowledge and expertise system connected to knowledge bases of all teams across the enterprise. #CulturalProblems
    - 12/14: Since all #GPT can reliably provide in short term is the language skill, primarily NLU/NLG, smaller language models trained on internal knowledge can be built to avoid privacy and data access issues. #NaturalLanguageUnderstanding #NaturalLanguageGeneration
    - 13/14: Adoption of #LLM enabled thinking tools will start in smaller companies, and with improvements in corporate culture and maturing technology, we will see bigger companies joining the movement. 
    - 14/14: With these tools being able to talk to us, remember our context, and reason about the world around us without the barriers of coding and formal language, we can accelerate #KnowledgeOps to the point where no idea is too expensive to try. #Automation

## Rise of Autonomous Information Seeking Companions

We continue observing a rapid movement towards creation of agents that can _reason_ about the objectives they are given, _use tools_ to carry out related tasks using formal languages, and use _natural anguage skills_ to communicate with their operators. This trend might (and most probably will) lead into _thinking companions_ that can interact with us, seek information and insight on our behald, and synthesize artifacts towards objectives we have. The ease of interaction with these companions could (and most probably will) get to a point where we can learn / plan / build on our own terms as we commute / run / cook.

[SLIDES](#) | [RECORDING](https://youtu.be/kpDKaYRlEG4)

**SUMMARY**
_coming soon_

### Amir Feizpour (CEO @ Aggregate Intellect)

[Amir](https://www.linkedin.com/in/amirfzpr/) is the co-founder of Aggregate Intellect ([https://ai.science/](https://ai.science/)), a Smart Knowledge Navigator platform for R&D teams in emerging technologies like AI. Prior to this, Amir was an NLP Product Lead at Royal Bank of Canada, and held a postdoctoral position at University of Oxford conducting research on experimental quantum computing. Amir holds a PhD in Physics from University of Toronto.

---

# LARGE LANGUAGE MODEL AGENTS - ONSET AGI?

## Expanding the Capabilities of Language Models with External Tools

This talk explores how language models can be integrated with external tools, such as Python interpreters, API's, and data stores, to greatly expand their utility. We will examine the emerging field of 'LLMOps' and review some promising tools. Additionally, we will push the boundaries of what's possible by exploring how a language model could accurately answer complex questions like, "Who was the CFO at Apple when its stock price was at its lowest point in the last 10 years?"

[SLIDES](#) | [RECORDING](https://youtu.be/WVV-lkYVLRY)

**TWITTER THREAD SUMMARY OF THE TALK:**
* Recent Advancements in LLMs:
    * The field of NLP is rapidly evolving with new models, tools, and techniques being introduced regularly. In fact, 90% of the content in the presentation did not exist a few months ago, and the content about LangChain and LlamaIndex is set to become woefully outdated within a month or two because those libraries are coming out with so many new updates. GPT-4 is evidence of the fast pace of development in the field. #NLP #GPT4 #MachineLearning
    * Instruction tuning is a powerful technique for improving LLMs and making them more aligned with human preferences. OpenAI's Instructor-GPT paper introduced the use of reinforcement learning and human feedback to align LMs/LLMs with human preferences. #InstructionTuning #LLMs #ReinforcementLearning
    * Evaluations are ongoing to determine the full capabilities of LLMs. The speaker notes that LLMs are good at following instructions and query understanding, but their limitations are not fully understood yet, especially in their reasoning capabilities. #LLMs #Evaluations #MachineLearning
    * Being 99% accurate is not enough for many applications, especially if the failure cases are unpredictable. This is true for self-driving cars and may also be the case for a wide variety of NLP applications. #MachineLearning #NLP #Accuracy #SelfDrivingCars
* Integration of LLMs with external tools
    * Language models are being integrated with various external tools like code interpreters, search engines, APIs, databases and other kinds of datastores, facilitated by Python libraries like Llama Index and LangChain. #NLP #AI #LLMs
    * The Holy Grail we are aspiring towards involves a LLM automatically decomposing a query into manageable subtasks, and calling appropriate external services to solve the subtasks if necessary. Currently, this approach is impractical for many usecases, and a lean approach is utilized where the external service is called to fetch relevant context and the LLM acts upon that context to generate the response.  #AI #taskautomation
    * LLMs can use task decomposition and agents to dynamically determine which tool to use to answer a question, and custom agents can be created to enable LLMs to answer questions more effectively. #LLMs #AI #taskdecomposition
    * LLMs are getting closer to fulfilling the promise of cross-document information retrieval, where information needs can be satisfied by going through multiple resources. #LLMs #AI #crossdocumentIR
    * External sources of information can enhance LLMs' performance, such as using retrieval models to map a query to entries in an index and returning it with adjacent sentences to provide context. #LLMs #AI #informationretrieval
    * OpenChatKit is a new LLM toolkit containing a 20 billion instruction tuned model based on GPT-NEOX, which can be used to automate tasks like answering complex questions and filtering search results. #LLMs #AI #OpenChatKit
    * It is possible for LLMs to generate python code to perform mathematical operations and invoke a code interpreter that can execute those operations. It is also feasible for an LLM to convert natural language queries into SQL queries, provided the schema is specified in the context,  enabling them to answer aggregation-level queries. #LLMs #AI #SQL
    * LLMs can construct API calls and browse the web for answers, such as answering a natural language query about the lowest stock price of Apple in the last 10 years or the weather in Toronto. #LLMs #AI #APIcalls
    * LamaIndex provides a wide range of data connectors to import your own data like web pages, PDFs, Discord data, GitHub data, Google Docs data, notion data, Twitter data, and more. #LLMs #AI #LamaIndex
    * Different types of indices include list index, keyword table index, vector store index, tree index and more, with each having its unique advantages and limitations. The vector store index is one of the most effective versions of indices. #LLMs #AI #indices 
* Use cases of LLMs
    * Language models break down complex questions into manageable components. For example, they can answer "who was the CTO of Apple when its share price was lowest in the last 10 years?" by finding the date of the lowest share price and the CTO on that date.
    * LLMs can filter out irrelevant results and automate tasks like flight searches. They call external APIs and databases and then synthesize coherent answers based on the output.
    * LLMs can answer questions about a company's policies, product planning, or any other information stored in Google Docs or Notion by using the data connectors provided by Lama index.
    * LLMs can ensure answers don't contain personal identifiable information or misinformation using a moderation chain. Making an LLM good at a particular domain is exciting, as passing exams in a particular domain is easy due to data contamination.

_Resources_
- [Augmented Language Models: a Survey](https://arxiv.org/abs/2302.07842)
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- [Iterated Decomposition: Improving Science Q&A by Supervising Reasoning Processes](https://arxiv.org/abs/2301.01751)
- [Demonstrate-Search-Predict: Composing retrieval and language models for knowledge-intensive NLP](https://arxiv.org/abs/2212.14024)
- [LangChain Docs](https://langchain.readthedocs.io/en/latest/)
- [LlamaIndex (formerly GPT-Index](https://gpt-index.readthedocs.io/en/latest/index.html)

## Exploring the agency limits of today's LLMs

GPT-4 and similar LLMs, powered with the ability to interface with external systems, have ushered in a whole variety of use cases into the realm of possibility that were previously considered impossible. However, possibility doesn't imply feasibility, with several limiting factors like effective retrieval hindering implementation. Tools like langchain and llamaindex are possibly the most impactful libraries of the year, but they are not a panacea to all problems. We will explore some of the limiting factors, approaches to tackle them, and showcase cutting-edge use cases that make the most of current capabilities.

[SLIDES](#) | [RECORDING](https://youtu.be/7kNgnqgETGo)

**SUMMARY**
_coming soon_

### Suhas Pai (CTO @ Bedrock AI)

[Suhas](https://www.linkedin.com/in/piesauce/) is the CTO & Co-founder of Bedrock AI, an NLP startup operating in the financial domain, where he conducts research on LLMs, domain adaptation, text ranking, and more. He was the co-chair of the Privacy WG at BigScience, the chair at TMLS 2022 and TMLS NLP 2022 conferences, and is currently writing a book on Large Language Models.

---

## Leveraging Language Models for Training Data Generation and Tool Learning

An emerging aspect of large language models is their ability to generate datasets that allow them to self-improve. A fascinating recent example is Toolformer ([Schick et al.](https://arxiv.org/abs/2302.04761)) in which LLMs generate fine-tuning data that helps them learn how to use tools at run-time. In this talk, we’ll examine this trend by taking a close look at the Toolformer paper and other related research.

[SLIDES](https://github.com/Aggregate-Intellect/practical-llms/blob/main/LLM%20Foundations/Self-Improving%20LLMs.pdf) | [RECORDING](https://youtu.be/Zk_UcqvTTAA)

**TWITTER THREAD SUMMARY OF THE TALK:**

* Large Language Models and Synthetic Data
    * As AI adoption increases, the growing demand for human annotations will quickly surpass human capacity.
    * One of the interesting new areas is to use large language models to create the training data that further improve themselves.
    * These kinds of data augmentation techniques can be used to improve large language models, reducing the need for human annotation of training data. This can reserve the more expensive human labor for creating high-quality or mission critical datasets.
    * Another trend we're seeing in the industry is that human annotations will be used more for creating evaluation or quality control datasets, while LLMs will be used for generating training data. #machinelearning #datageneration #humansintheLoop
* Techniques for Filtering Data for LLM Fine-Tuning
    * Choosing the right data for fine-tuning is essential for improving LLMs' performance. Various approaches can be used to filter down the generated data for direct use, or human annotator intervention. 
    * There are multiple ways to filter a data set for LLM fine-tuning, in this talk we discuss the following four: a perplexity-based approach (Toolformer), AI annotator (RLAIF), diversity of fine-tuning samples (Self-instruct), and self-consistency.
* [Toolformer](https://arxiv.org/abs/2302.04761)
    * Toolformer splits up a set of unlabelled data set and samples API calls to generate possible inputs and outputs for different tools. It then uses the model's loss (perplexity/entropy) to predict the next words in the sequence to determine whether or not the tool has made the task easier.
* [Reinforcement learning from AI feedback](https://arxiv.org/abs/2212.08073) (RLAIF) for Harmless and Helpful Language Models
    * RLAIF is a promising application for large language models where models can edit their own mistakes and learn from this signal.
    * To train the model, harmful responses are generated through red teaming requests, and a 'Constitution' is used to guide the model's behavior and critique its responses. The model is then fine-tuned on a dataset of revisions based on its critiques. #RedTeaming #ModelTraining
    * The Constitution is created by humans as a guideline for the model's behavior, but the model is able to critique itself and generate revisions based on the Constitution. This allows for more training data to be generated using the model itself.
* [Self-Instruct: Aligning Language Model with Self Generated Instructions](https://arxiv.org/abs/2212.10560)
    * This paper discusses using a model to generate new tasks and instructions to fine-tune itself on.
    * It uses a diversity metric to choose samples - prioritizing generations that are significantly different from its current training data.
* [Fine-Tuning Language Models with Self-Consistency](https://arxiv.org/abs/2210.11610)
    *  [Self-consistency](https://arxiv.org/abs/2203.11171) is a recent concept in LLMs that involves creating multiple generations for the same input and using a form of voting to choose the most common one.
    * This technique does not require the model to know the ground truth, meaning it can be applied on unlabelled data, but as the models become larger, the most frequent output is often the correct one.
    * The model filters down data using self-consistency, and if the majority of generations produce a specific output, e.g., "nine," the model takes all the cases where "nine" was generated as the output, assuming that these are correct, and feeds them back into the model which creates a feedback loop that improves the model's performance over time.

_Resources_
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)
- [SELF-INSTRUCT: Aligning Language Model with Self Generated Instructions](https://arxiv.org/abs/2212.10560)
- [Large Language Models Can Self-Improve](https://arxiv.org/abs/2210.11610)
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171)

### Gordon Gibson (ML Lead @ Ada)

[Gordon](https://www.linkedin.com/in/gordon-gibson-874b3130/) is the Senior Engineering Manager of the Applied Machine Learning team at Ada where he's helped lead the creation of Ada's ML engine and features. Gordon's background is in Engineering Physics and Operations Research, and he's passionate about building useful ML products.

---

# USE CASES

## Commercializing LLMs: Lessons and Ideas for Agile Innovation

In this talk, Josh, an ML expert with experience commercializing NLP-powered services, will discuss the potential for leveraging foundation models to drive agile innovation in both individual and organizational processes. He will share lessons learned from his work with a bootstrapped startup and provide insights on how LLMs can be commercialized effectively.

[SLIDES](https://github.com/Aggregate-Intellect/practical-llms/blob/main/KnowledgeOps/Commercialization%20Strategy%20with%20LLMs.pdf) | [RECORDING](https://youtu.be/QfX648IZg3U)

**TWITTER THREAD SUMMARY OF THE TALK:**

* Opportunities for large language models in startups and innovation
    * 1/21: Large language models offer exciting possibilities for startups and product development. They can revolutionize the innovation process with qualitatively new ways of problem-solving. Before building a product, take a step back and see if an approach powered by these models could serve a purpose.
    * 2/21: GitHub co-pilot is a perfect example of how large language models can be used in engineering. By offering new ways of writing code, it streamlines the development process and allows engineers to focus on solving problems.
    * 3/21: Quick feedback from users is crucial for product development, even if you are one of the target users. Hackathons and accelerators can be beneficial to startups by providing access to large language models as a service and infrastructure credits.
    * 4/21: Building a lean, agile startup focused on R&D is aided by resources such as infrastructure credits, tax credits, subsidies, marketing grants, and IP support. In Canada, AI startups receive federal and provincial programs supporting R&D. Bootstrapping can sustain a company from day one.
    * 5/21: Bootstrapping can be a good way to sustain a company based on revenue from day one. It also forces you to start selling as soon as possible to get revenue and establish quick feedback for market fit. Investment is not always necessary for R&D.
* IP strategy for large language models
    * 6/21: When building large language models for commercialization, it's important to consider IP strategy and seek advice from experts.
    * 7/21: Applying large language models to improve existing capabilities may not be patentable, but rethinking the entire approach to solve a problem in a new way is more likely to be patentable. #MLdevelopment #IPstrategy
* Large language models for R&D
    * 8/21: During R&D, specify tasks, models to optimize, & create dataset to evaluate models against. Use large language models for weak label generation & data augmentation to make data set curation easier. #AI #ML #R&D
    * 9/21: R&D conversations are often open & difficult to structure, but they can still be turned into components used by large language models. For example, to create a conversational bot for Slack, modularize into 3 LLM calls for message, trigger, & audience classification. #AI #ML #chatbot
    * 10/21: With modularization & templated code repository, create conversational bot very quickly. Use LLM-generated info for message content classification, trigger classification, & audience classification. #AI #ML #chatbot #Slack
* Microservices and modularization of products based on large language models
    * 11/21: Large language models (LLMs) can be used in various stages of a project, including engineering and production. They can be leveraged to build microservices or components that work together to produce the desired output.
    * 12/21: Treating a LLM as one of the microservices of a product enables breaking down the problem into smaller and more manageable pieces. This allows for easier implementation and development, additional R&D, unit testing, and quality control.
    * 13/21: This approach also allows for easier explainability and optimization of the process. The components in the architecture of a system that leverages LLMs should interface the language skills of GPT-like models and domain-specific expertise to get the best results.
    * 14/21: In our slack app example, the LLM prompts used depend on the context and specifics of what is being done. In some cases, having a good prompt engineer is crucial, while in others, we can just pass exemplars that would have a bigger influence on the performance.
    * 15/21: We can add a dialogue analysis component to control the prompts generated by LLMs in a particular domain. This component can infer information necessary to determine the most relevant examples when generating probing questions.
    * 16/21: Another component can create dynamic prompts for in-context learning by choosing the best exemplars from a repository or by retrieving documents containing domain knowledge. This can significantly improve the performance of LLMs.
    * 17/21: Finally, a quality control component can rank generated candidates in case the LLM generates a question or answer that is not suitable. Rule-based and human-crafted questions generated using question recipes can also be used to ensure that inappropriate responses are avoided.
* Production stage of large language models
    * 18/21: In production, large language models can be optimized by combining them with other components to create an ecosystem of microservices that work together. This approach ensures better performance and improved efficiency of the overall system.
    * 19/21: When optimizing costs during a project, evaluating both performance and cost is crucial. If a cheaper model performs almost as well as a more expensive one, it's advisable to choose the former. This way, you can save money without compromising on performance.
    * 20/21: After some data is collected and the overall system performance is more well established, it's sometimes possible to replace large language models with cheaper and leaner models in production. This approach helps to reduce costs without sacrificing performance.
    * 21/21: When building a startup with large language models, it's essential to consider the service level availability uptime of cloud infrastructure. Microsoft Azure Open AI service offers 99.9% uptime, ensuring that your system will be available to users when they need it.

_Resources_
- [Which Model Shall I Choose? Cost/Quality Trade-offs for Text Classification Tasks](https://arxiv.org/abs/2301.07006)
- [Canada Government Business Benefits Finder](https://innovation.ised-isde.canada.ca/innovation/s/?language=en_CA)
- [Understanding UK Artificial Intelligence R&D commercialisation and the role of standards](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1079959/DCMS_and_OAI_-_Understanding_UK_Artificial_Intelligence_R_D_commercialisation__accessible.pdf)

### Josh Seltzer (CTO @ Nexxt Intelligence)

[Josh](https://www.linkedin.com/in/josh-seltzer/) is the CTO at Nexxt Intelligence, where he leads R&D on LLMs and NLP to build innovative solutions for the market research industry. He also works in biodiversity and applications of AI for conservation.

---

## ChatGPT-like application for construction of mathematical financial models

LLMs alone generally struggle with complex mathematical tasks. This limitation is particularly evident when a problem requires intricate simulations rather than basic arithmetic or a few simple calculations. For instance, while GPT-4 can compute the interest paid on a loan, it cannot determine the loan's duration over several years. In this talk, we show how we used ChatGPT to build an interface for a no-code financial planning application and allow users to use the chat interface to inspect and inquire about the financial projection model in the background.

[SLIDES](#) | [RECORDING](https://youtu.be/NRnjra-WGmY)

**SUMMARY**
_coming soon_

### Sina Shahandeh (Founder @ Plan with Flow)

[Sina](https://www.linkedin.com/in/sinashahandeh/) holds a PhD in scientific computing and has led data science teams at three startups in Toronto's ecosystem. Before founding Plan with Flow, Sina served as the Vice President of Data Science at ecobee Inc., leading to an exit valued at $770 million. Currently, Sina is based in Madrid.

---

## Building ResearchLLM: automated statistical research and interpretation

ResearchGPT is a natural language statistics agent. Users provide the agent with a data set and natural language queries. The agent writes code to answer their questions and provide interpretations based on its analysis. Raw data is never shared with the LLM itself, and generated code is run locally. You can see a demo video [here](https://phasellm.com/researchgpt). This session will cover the underlying architecture of ResearchGPT and how it's been tested using PhaseLLM, a developer tooling framework for testing and robustifying LLM-powered apps.

[SLIDES](#) | [RECORDING](https://youtu.be/yqmLF3a9aLM)

**SUMMARY**
_coming soon_

### Wojciech Gryc (Founder @ Phase AI)

[Wojciech](https://www.linkedin.com/in/wojciechgryc) is the co-founder and CEO of Phase AI, where he helps startups and scaleups launch AI-driven products. He is the developer behind PhaseLLM and ResearchGPT. Wojciech started his career as an AI researcher at IBM Research, and completed his graduate studies at the Oxford Internet Institute. Prior to Phase AI, he was the founder and CEO of Canopy Labs, a customer data platform funded by Y Combinator and acquired by Drop.

---

# LLM-OPS, ENGINEERING, AND ENTERPRISE CONSIDERATIONS

## Integrating LLMs into Your Product: Considerations and Best Practices

The proliferation of ChatGPT and other large language models has resulted in an explosion of LLM-based projects and startups. While these models can provide impressive initial demos, integrating them into a product requires careful consideration and planning. This talk will cover key considerations for creating, testing, and optimizing prompts for LLMs, as well as how to run analytics on key user metrics to ensure success.

[SLIDES](https://pitch.com/public/7fce9d3f-fec7-40f5-9273-99ff1655a4e8) | [RECORDING](https://youtu.be/1C3rU3fxcME)

**TWITTER THREAD SUMMARY OF THE TALK:**

* Considerations for adopting LLMs
    * 1/16: Running large language models in house can be costly, which is why many people use APIs. It's important to ensure your use case has a good ROI to avoid wasting resources.
    * 2/16: When deciding how much to invest in using LLMs, companies need to consider their bet size (level of investment) and company size (effort required to adopt LLMs). This should be done with a careful assessment of consequences on their existing customers and their product development roadmap.
    * 3/16: Therefore companies need to understand their business and customers before adopting LLMs. Voiceflow, a conversational AI platform used by various verticals, experimented with LLMs and how they should be combined with existing capabilities.
    * 4/16: Even large companies, eg. Google's Bard and Bing's demos have had instances where LLMs generated incorrect information damaging their brands. Having humans in the loop, domain experts when appropriate, is important to ensure accuracy. 
    * 5/16: UX and UI are critical for LLM adoption. Incorporating fun and natural features, such as shortcuts and accepting / declining recommendations, are important for making LLMs easy to use and understand.
    * 6/16: Human-in-the-loop performance improvements at creation time are less risky than having that kind of feature in run time. One should carefully consider the trade offs when implementing user feedback loops. 
    * 7/16: Caching might be a good way to reduce cost and improve performance. Though it has to be done in a way that context for different users is handled properly to ensure the best experience.
* Deployment methodology for LLMs
    * 8/16: When deploying large language models, there are different options to consider. Using a pre-trained model service is easier, but building and hosting your own solution gives you more control.
    * 9/16: Building a product that generates revenue is essential, but investing time in a minimally viable platform is also important. Neglecting the platform can lead to technical debt and slow down the iteration process for new models. There should be a balance in effort put in model, product, and platform development.
* Testing and Fine-Tuning for LLMs
    * 10/16: When deploying LLMs in production, testing is crucial. Denys Linkov built a test suite to check if prompts work, processing the code, running python, and documenting errors. This is on top of initial manual testing and collecting errors from the data warehouse.
    * 11/16: For example, since the output of Open AI API is probabilistic it might return poorly formatted JSON responses. This at inference time might be easy to deal with but at high volume could cause unforeseen failures in production systems. 
    * 12/16: Fine-tuning can solve formatting issues, especially for few-shot learning including desired output, examples, and chain of thought reasoning. 
* Considerations for Third-Party Providers
    * 13/16: Running a product with LLMs comes with its own set of challenges, like unpredictable response formatting, unreliable uptime, or other upstream dependencies. 
    * 14/16: When choosing NLP provider APIs or open-source libraries, it's crucial to consider their reliability and ease of integration. Companies can opt for a single or multiple NLP provider APIs based on their required uptime.
    * 15/16: While OpenAI is perceived to have the best models, other providers may offer more reliability. The trade-off between model accuracy and uptime is a critical consideration for companies depending on their service requirements.
    * 16/16: With LLM space moving quickly, it might also become easier to deploy own models instead of relying on third-party providers at least for some components of the system. 

_Resources_
- [Talk Slides](https://pitch.com/public/7fce9d3f-fec7-40f5-9273-99ff1655a4e8)
- [Prompt Engineering Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)
- [How GPT3 Works - Visualizations and Animations](https://jalammar.github.io/how-gpt3-works-visualizations-animations/)
- [Open AI Product](https://openai.com/product)

## Running LLMs in Your Environment

The availability of Large Language Models as a service (LLMaaS) has sparked a new wave of applications, use cases and companies. But what alternatives exist if you want to host your own LLMs? In this talk we’ll cover the landscape of LLMs and their deployment options. We’ll discuss the tradeoffs of hosting your own LLM vs using a commercial offering, including security, compliance, cost and delivery times. We’ll also cover a number of available open source options and how they can be hosted within your own environment whether a virtual private cloud or on prem.

[SLIDES](#) | [RECORDING](https://youtu.be/REv-GgieWto)

**SUMMARY**
_coming soon_

### Denys Linkov (ML Lead @ Voiceflow)

[Denys](https://www.linkedin.com/in/denyslinkov/) is the ML lead at Voiceflow focused on building the ML platform and data science offerings. His focus is on realtime NLP systems that help Voiceflow’s 60+ enterprise customers build better conversational assistants. Previously he worked at large bank as a senior cloud architect.

---

## Incorporating Large Language Models into Enterprise Analytics: Navigating the Landscape of In-Context Learning and Agents

Large Language Models (LLMs) have dramatically changed our expectations for AI. While a few innovators are building proof-of-concept projects using APIs, most enterprise analytic teams still need to figure out how to incorporate LLMs into their analytical toolbox. Rajiv shows the necessity of understanding the growth of "in-context learning" and agents. With these insights, he explains how LLMs will shape enterprise analytics. Along the way, he covers many practical factors, such as the different providers of LLMs, resource costs, and ethical issues.

[SLIDES](https://github.com/Aggregate-Intellect/practical-llms/blob/main/LLM%20Use%20Cases/Enterprise_LLMs_Shah.pdf) | [RECORDING](https://youtu.be/GO6l7dbZIqY)

**TWITTER THREAD SUMMARY OF THE TALK:**

* Advantages and Use Cases of Large Language Models
    * 1/14: NLP use cases in the enterprise primarily focus on text classification, summarization, question answering, and embeddings. Large language models like GPT-3 and ChatGPT can transform how enterprises approach these tasks. 
    * 2/14: LLMs offer advantages over traditional NLP models, such as better performance in classification and language generation for use cases like financial sentiment analysis and customer service bots.
    * 3/14: To leverage LLMs in enterprise workflows, companies can start by exploring pre-trained models, fine-tuning them on their data. However, LLMs are general-purpose models and adding domain-specific information might be challenging. Using dedicated models for certain tasks, combined with LLMs can be more efficient and cost-effective.
    * 4/14: LLMs can connect previously siloed domains in an enterprise, allowing for more efficient and natural language searches across multiple domains. This makes it easier to access relevant information and insights from different parts of the organization.
    * 5/14: The UI is just as important as the model in solving business problems. Therefore, it's essential to focus on UI/UX design in addition to developing models. While models can add new capabilities, the user interface plays a critical role in presenting them in a valuable way.
* Interfacing LLMs and other Enterprise Systems 
    * 6/14: LLMs can be decision-makers, but it's crucial to set them up for success by combining them with other tools. For instance, for a math question LLM could be set up to call a calculator and then show the result to prevent it from giving the wrong answer with confidence.
    * 7/14: Large Language Models can enhance information retrieval by combining classic data / knowledge bases with LLMs to provide more accurate and human-readable responses to queries. For example, LLMs were used to retrieve information on how to install Transformers from Huggingface documentation with citation to resource.
* Choosing and Keeping Up with LLMs
    * 8/14: Choosing the right LLM depends on the specific use case, and there are various options available with different licensing requirements and costs.
    * 9/14: When choosing an LLM, consider factors like availability, cost, and accuracy for the specific task at hand. Open source models like Hugging Face can provide a wide variety of models and tools leveraging the collective knowledge of the community.
    * 10/14: The field of LLMs is evolving rapidly. Staying up to date on the latest developments and trends is crucial to make the most of this technology. Keep learning to keep improving!
    * 11/14: For those looking to learn AI, OpenAI Sandbox and Hugging Face Spaces are excellent starting points. OpenAI Sandbox provides templates and examples for learning AI, while Hugging Face is a useful resource for natural language processing. LangChain and LlamaIndex are also good examples to get started.
* Democratization and Ethical Considerations in AI
    * 12/14: The democratization of AI is crucial for its widespread adoption. Co-pilots and natural language interfaces are enabling more people to experiment with AI, even those without a technical background. Lowering the barriers to entry for AI can have a significant impact on the democratization of AI.
    * 13/14: Ethical considerations are essential in the development and deployment of AI. It's crucial to include diverse voices in the design and decision-making processes, educate users on the potential dangers of generative AI, and consider the ethical implications of AI.
    * 14/14: Bias is a significant challenge in AI. Historic data used for training models can perpetuate biases and historical injustices. Therefore, it's crucial to be aware of these biases and work towards minimizing their impact.

_Resources_
- [Talk Slides](https://github.com/Aggregate-Intellect/practical-llms/blob/main/Enterprise_LLMs_Shah.pdf)
- [Sentiment Spin: Attacking Financial Sentiment with GPT-3](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4337182)
- [Is ChatGPT a General-Purpose Natural Language Processing Task Solver?](https://arxiv.org/abs/2302.06476)
- [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165)
- [Transformers learn in-context by gradient descent](https://arxiv.org/abs/2212.07677)
- [News Summarization and Evaluation in the Era of GPT-3](https://arxiv.org/abs/2209.12356)
- [Benchmarking Large Language Models for News Summarization](https://arxiv.org/abs/2301.13848)
- [BIG-Bench - Beyond the Imitation Game Benchmark](https://github.com/google/BIG-bench/)
- [Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them](https://arxiv.org/abs/2210.09261)
- [ChatGPT for Robotics: Design Principles and Model Abilities](https://www.microsoft.com/en-us/research/group/autonomous-systems-group-robotics/articles/chatgpt-for-robotics/)
- [Replicate MRKL chain uding LangChain](https://langchain.readthedocs.io/en/latest/modules/agents/implementations/mrkl.html)
- [Experimental Evidence on the Productivity Effects of Generative Artificial Intelligence](https://economics.mit.edu/sites/default/files/inline-files/Noy_Zhang_1.pdf)
- [The CEO’s Guide to the Generative AI Revolution](https://www.bcg.com/publications/2023/ceo-guide-to-ai-revolution)
- [A New Era of Creativity: Expert-in-the-loop Generative AI](https://multithreaded.stitchfix.com/blog/2023/03/06/expert-in-the-loop-generative-ai-at-stitch-fix/)

### Rajiv Shah (MLE @ Huggingface)

[Rajiv](https://www.linkedin.com/in/rajistics/) is a machine learning engineer at Hugging Face, whose primary focus is on enabling enterprise teams to succeed with AI. He is a widely recognized speaker on enterprise AI and was part of data science teams at Snorkel AI, Caterpillar, and State Farm.

---

# RISK MITIGATION OF LARGE LANGUAGE MODELS

## Generative AI: Ethics, Accessibility, Legal Risk Mitigation

Generative AI has made impressive advances in creating music, art, and even virtual worlds that were once thought to be exclusively the domain of human creators. However, with such power comes great responsibility, and we must be mindful of the ethical implications of our creations. In this session, we will explore the intersection of generative AI, ethics, and accessibility. We will examine ethical considerations related to bias, transparency, and ownership, as well as the challenges of making generative AI accessible to individuals with disabilities and those from underrepresented communities.

[SLIDES](#) | [RECORDING](https://youtu.be/TEixBW1Bnow)

**TWITTER THREAD SUMMARY OF THE TALK:**

* Use of generative AI to improve accessibility and the lives of people with disabilities
    * 1/20: When developing generative AI, ethical considerations should be at the forefront of our minds. Those of us who are building AI systems, and helping others use AI should educate everyone we interact with to build more responsibly. #AIethics #generativeAI #inclusiveAI
    * 2/20: For example, voice technology combined with generative capabilities can improve the lives of people with disabilities. Noelle has seen firsthand how these technologies helped her family members, and how much more needs to be done still.
    * 3/20: Generative AI has the potential to make conversational agents more efficient by eliminating the need for explicit mapping of intent and therefore better flexibility to various levels of need and speech / communication patterns.
    * 4/20: It is important for AI models to be flexible to accommodate new use cases and user personas over time. By incorporating flexible and inclusive design principles, AI developers can ensure that their technologies are accessible and beneficial to everyone.
    * 5/20: Inclusive engineering is crucial for building good AI solutions. It involves team building and data collection with diverse perspectives in mind. One of the best ways to achieve this is hiring diverse teams with different backgrounds, opinions, needs, and demographics.
* Managing and moderating LLMs to reduce bias, and increase fairness
    * 6/20: Deliberate choices that companies make can reduce the impact of bias, and mitigate risks. Mitigating potential issues with LLMs requires a comprehensive approach, including diverse datasets, fine-tuning foundation models, utilizing hardware resources, managing content, and continuous monitoring.
    * 7/20: LLMs are trained on data sets generated by humans, and the awareness of potential sources of bias and inaccuracies in that data is crucial. Diverse datasets are necessary when training LLMs to reduce the impact of those imperfections.
    * 8/20: LLMs make assumptions based on training data. This can result in incorrect conclusions. Noelle mentioned that a falsely attributed scholarly article was taken as true by an LLM because it was making assumptions based on the training data.
    * 9/20: There is a need for inclusive data collection to ensure that AI solutions represent end users. Inclusive data collection along with keeping track of lineage and context can help mitigate biases that may be present in training data.
    * 10/20: LLMs can amplify bias over time, but there are ways to mitigate its impact. Having a human-in-the-loop process to monitor, manage and control the LLMs is crucial. #AmplificationOfBias #HumanInLoop
    * 11/20: LLMs can speed up the process of generating content, but if not managed at scale, it can slow down the process by generating inappropriate or poor-quality content. Moderation and management of the content generated by LLMs are crucial. #ContentGeneration #Moderation
    * 12/20: Specific performance metrics for LLMs are essential to understand what is a good model and what is not. Continuous monitoring by a human team is necessary to ensure that the model is working correctly. #PerformanceMetrics #ContinuousMonitoring
* Versatility and scalability of potential LLM use cases
    * 13/20: LLMs are built on foundation models that can be fine-tuned to fit specific business needs. This allows businesses to create LLMs tailored to their specific needs and goals, making them increasingly popular with companies willing to invest in them.
    * 14/20: The demand for LLMs is growing rapidly, and ML developers need to be able to build and deploy them quickly to meet the demand. This puts a premium on rapid development and deployment processes.
    * 15/20: LLMs can do more than just conversation. They can generate natural language requests and responses from various sources, including customer signals, website data, and ticketing systems. They can even be used to automatically formulate human questions and generate Power BI dashboards.
    * 16/20: Next generations of LLMs might be multi-modal which means that they can combine different types of input, such as images and text, to generate output. This makes them valuable in a variety of contexts and use cases.
    * 17/20: LLMs require significant hardware resources to operate, and only a few labs in the world can support the required hardware. A balance has to be made between building internally, using offerings from mainstream vendors, and ones from emergent providers. 
* Challenges and Risks of LLMs
    * 18/20: Organizations have a responsibility to guard against potential legal issues when using LLMs. Noelle emphasized the responsibility of organizations to think through potential legal issues and approach projects with an awareness of the risks involved.
    * 19/20: Evaluating risks and mitigating them in the solution is important. There are use cases for LLMs that are relatively easy to approach and mitigate risks, such as customer call centers and customer service ticketing. However, more rigor and discipline are required for projects using codex, which were trained on Github repos.
    * 20/20: Indemnification is important when using LLMs to protect against ownership challenges that may arise in the future. Enterprise level solutions provide more indemnification than research models like Dalle, especially if the model is not custom trained on your own art.

### Noelle Russell (Global AI Solutions Lead @ Accenture)

[Noelle Silver Russell](https://www.linkedin.com/in/noelleai/) is a multi-award-winning technologist and entrepreneur who specializes in advising companies on emerging technology, generative AI and LLMs. She is the Global AI Solutions Lead as well as the Global Industry Lead for Generative AI at Accenture. She has led teams at NPR, Microsoft, IBM, and Amazon Alexa, and is a consistent champion for AI literacy and the ethical use of AI based on her work building some of the largest AI models in the world. She is the founder of AI Leadership Institute and she was recently awarded the Microsoft Most Valuable Professional award for Artificial Intelligence as well as VentureBeat’s Women in AI Responsibility and Ethics award.

---

# LLM HANDS ON TUTORIALS AND RESOURCES

## Building with LLMs Using LangChain - Hands-on

This workshop focuses on Large Language Models (LLMs) and their capabilities in language understanding and generation. Despite their impressive performance, LLMs still face challenges in tasks like retrieval and math reasoning. Fortunately, several tools are available for these tasks. LangChain is a Python library that enables the integration of LLMs with external tools to accomplish a wide range of tasks. The workshop will provide an overview of LangChain's basics and demonstrate how it can interface with external tools. Additionally, we will create a simple system using LangChain to answer questions about itself LangChain itself.

[SLIDES](#) | [RECORDING](https://youtu.be/MGB2uahuX_o)

**SUMMARY**
_coming soon_

### Percy Chen (PhD Student @ McGill University)

[Percy](https://www.linkedin.com/in/boqi-chen/) is a PhD student at McGill University. His research interests include model-driven software engineering, trustworthy AI, verification for ML systems, Graph Neural Networks, and Large Language Models. Percy leads R&D collaboration between McGill University and Aggregate Intellect. 

---

# THEORETICAL FOUNDATIONS OF LARGE LANGUAGE MDOELS


## Modern Innovations in Fine-Tuning Large Language Models

In this presentation, we will explore the latest breakthroughs in fine-tuning large language models. Our conversation will encompass various fine-tuning techniques, including instruction following fine-tuning and reinforcement learning through human feedback (RLHF). Additionally, we will delve into computational aspects like scaling laws, parameter-efficient fine-tuning (PEFT), and the zero redundancy optimizer (ZeRO).

[SLIDES](#) | [RECORDING](https://youtu.be/Bn2ZK_ctPbo)

**SUMMARY**
_coming soon_

### Ehsan Kamalinejad (ML Scientist @ Amazon)

[Ehsan](https://www.linkedin.com/in/ehsan-kamalinejad/) is a machine learning scientist. He is currently a lead scientist working on NLP developments at Amazon. Previously he co-founded Visual One which was a YCombinator startup in computer vision. Before that he was working at Apple for several years as a tech-lead machine learning scientist working on projects such as Photos Memories. Ehsan is also an associate professor at California State University. He got his PhD from the University of Toronto in applied mathematics.

---

## Optimizing Large Language Models with Reinforcement Learning-Based Prompts

Large language models (LLMs) have the potential to perform a wide range of tasks by understanding human queries, but they are often sensitive to the wording of the prompts, which can greatly affect the output. This talk will introduce RLPrompt, an efficient algorithm that uses reinforcement learning to systematically search for the best prompts to improve LLM performance across diverse tasks.

[SLIDES](https://github.com/Aggregate-Intellect/practical-llms/blob/main/LLM%20Foundations/RLPrompt%20Presentation.pdf) | [RECORDING](https://youtu.be/SGInyKjzF7A)

**TWITTER THREAD SUMMARY OF THE TALK:**
* LLMs Capabilities and Prompt Sensitivity
    * Large language models (LLMs) are versatile and can perform tasks like summarization, code generation, sentiment analysis, dialogue, translation, and storytelling depending on the prompt.
    * The wording of the prompt can significantly affect LLMs' performance, making it challenging to find the best prompt for a given task. Two prompts with the same meaning can lead to different outcomes. 
* Prompt Design Approaches
    * Designing the best prompt can be time-consuming and repetitive. But it's a great way to get started. The speaker suggests tweaking the prompt or trying different options based on intuition. #NLP #machinelearning #promptdesign
    * Another way to find the best prompt is to use a machine to generate options. The speaker suggests paraphrasing or editing the original prompt and scoring each candidate through the LLM. #NLP #machinelearning #promptdesign
    * Numerical tuning is a third approach to exploring prompt options. Instead of tweaking words, numerical tuning involves passing the numbers that represent the words into the LLM. This method can help explore all possible options without the limitations of human space. #NLP #machinelearning #numericaltuning
* Reinforcement Learning-based Prompt Optimization
    * Prompt optimization is a challenging problem due to the large number of candidates. One way to address it is to formulate it as a reinforcement learning problem. This allows for more effective identification of the best prompts.
    * The reinforcement learning approach involves training a prompt policy to learn correlations between words and their underlying score or reward. It is a powerful way to optimize prompts for large language models.
    * Optimized prompts for RL problems can perform better than human-written prompts, even if they don't follow human language. This utility of RL prompts is important to understand.
    * The optimized prompts can transfer well across models, and the reinforcement learning-based optimization allows for more effective identification of the best prompts. Careful optimization is key for large language models.
* Framework for Prompt Optimization
    * I developed a framework that combines a smaller language model for word correlations and a larger model for tasks. It can perform few-shot text classification and unsupervised control text generation. #MachineLearning #NLP
    * Optimized prompts for the framework are consistently among the best performers, unlike manual prompts, which can vary widely in performance. Check out my graph comparing their performance across different models. #AI #NLP
    * Shorter optimized prompts lead to faster model runs and lower costs. I found that optimized prompts trained on one model can also be applied to other models with similar or even better performance. #MachineLearning #Optimization
    * My framework is better than human-written prompts at capturing how language models respond to prompts. See the graph comparing the performance of manual prompts vs. optimized prompts. #NLP #DataScience
    * I made sure to package my framework code well and make it easy to set up. You can find it on GitHub. For instance, running a test style transfer experiment requires only 51 lines of code. #OpenSource #Python
    * Optimized prompts from my framework can even turn negative sentences into more positive ones while preserving the original meaning. Want to see a demo? #AI #NLP #SentimentAnalysis 
* Future of Language Models
    * Language models can recognize patterns beyond just human language. This means there may be prompts that work when prompt engineering fails. #LanguageModels #AI #PromptEngineering
    * To use language models for more than a single query, we need to develop new ways of interacting with them that differ from how humans talk. #AI #NLP #LanguageModels
    * Words are better than vectors for prompt optimization. They're transferable and can be applied to different models with similar performance. Also, word-based prompts are less sensitive to model parameter changes than vector-based ones. #AI #NLP #PromptOptimization  

_Resources_
- RLPrompt: Optimizing Discrete Text Prompts with Reinforcement Learning [blog](https://blog.ml.cmu.edu/2023/02/24/rlprompt-optimizing-discrete-text-prompts-with-reinforcement-learning/) | [paper](https://arxiv.org/abs/2205.12548) | [code](https://github.com/mingkaid/rl-prompt)
- [Prefix-Tuning: Optimizing Continuous Prompts for Generation](https://arxiv.org/abs/2101.00190)
- [Making Pre-trained Language Models Better Few-shot Learners](https://aclanthology.org/2021.acl-long.295.pdf)
- [Prompt Waywardness: The Curious Case of Discretized Interpretation of Continuous Prompts](https://arxiv.org/abs/2112.08348)
- [A Recipe For Arbitrary Text Style Transfer with Large Language Models](https://arxiv.org/abs/2109.03910)

### Mingkai Deng (PhD Student @ CMU)

[Mingkai Deng](https://www.linkedin.com/in/mingkaideng/) is a PhD student at Carnegie Mellon University working at the intersection of machine learning, computer vision, and natural language processing. Prior to that, he was a data scientist who led award-winning projects and built analytics products that serve multiple Fortune 500 clients.

---

## Learning-free Controllable Text Generation for Debiasing

Large language Models (LLMs, e.g., GPT-3, OPT, TNLG,…) are shown to have a remarkably high performance on standard benchmarks, due to their high parameter count, extremely large training datasets, and significant compute. Although the high parameter count in these models leads to more expressiveness, it can also lead to higher memorization, which, coupled with large unvetted, web-scraped datasets can cause different negative societal and ethical impacts such as leakage of private, sensitive information and generation of harmful text. In this talk, we introduce a global score-based method for controllable text generation that combines arbitrary pre-trained black-box models for achieving the desired attributes in generated text from LLMs, without involving any fine-tuning or structural assumptions about the black-box models.

[SLIDES](#) | [RECORDING](https://youtu.be/r8pAP9zMM_4)

**SUMMARY**
_coming soon_

### Fatemehsadat Mireshghallah (Post-doctoral Researcher @ UW)

[Fatemeh](https://twitter.com/limufar) received her Ph.D. from the CSE department of UC San Diego and will join UW as a post-doctoral fellow. Her research interests are Trustworthy Machine Learning and Natural Language Processing. She is a recipient of the National Center for Women & IT (NCWIT) Collegiate award in 2020 for her work on privacy-preserving inference, a finalist of the Qualcomm Innovation Fellowship in 2021 and a recipient of the 2022 Rising star in Adversarial ML award.

---

# Contributions Guideline

## Making Changes through Pull Requests

To make changes to this project, you will need to fork the repository to your own GitHub account, make the changes to your forked repository, and then submit a pull request to our main repository. Here are the steps:

1. Fork the repository to your own GitHub account by clicking the "Fork" button on the top right of the repository page.
2. Clone the forked repository to your local machine by running the following command in your terminal: `git clone https://github.com/your-username/repo-name.git`
3. Create a new branch for your changes by running the following command: `git checkout -b your-branch-name`
4. Make the desired changes to the book.
5. Commit your changes with a descriptive commit message by running the following command:`git commit -m "your commit message"`
6. Push your changes to your forked repository by running the following command: `git push origin your-branch-name`
7. Go to the main repository and submit a pull request with a description of your changes.

Once your pull request is submitted, it will be reviewed by our team and either merged or commented on for further changes.

NOTE: If the change you are considering is fairly major, please suggest it as an issue first so that we can coordinate before you put in the effort. 

## Suggesting Changes through Issues
If you would like to suggest changes to the book without making direct changes, you can create an issue in our repository. Here are the steps:

1. Go to the repository and click on the "Issues" tab.
2. Click on the "New Issue" button.
3. Provide a descriptive title and description of your suggested change.
4. Optionally, you can label your issue to make it easier to categorize.
5. Submit the issue.

Our team will review the issue and either implement the suggested change or respond with feedback.

---

# Other Useful Resources
- [Aggregate Intellect Weekly Journal Club on NLP, GNN, etc](https://lu.ma/aisc-journal-club)
- [Augmented Thinking - A.I. Youtube Channel](https://www.youtube.com/@ai-science)
- [LangChain Tutorials](https://github.com/gkamradt/langchain-tutorials)

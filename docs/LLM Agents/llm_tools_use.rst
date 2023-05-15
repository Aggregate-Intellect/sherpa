## Expanding the Capabilities of Language Models with External Tools

This talk explores how language models can be integrated with external tools, such as Python interpreters, API's, and data stores, to greatly expand their utility. We will examine the emerging field of 'LLMOps' and review some promising tools. Additionally, we will push the boundaries of what's possible by exploring how a language model could accurately answer complex questions like, "Who was the CFO at Apple when its stock price was at its lowest point in the last 10 years?"

[SLIDES](#) | [RECORDING](https://youtu.be/WVV-lkYVLRY)

**TWITTER THREAD SUMMARY OF THE TALK:**

- Recent Advancements in LLMs:
  - The field of NLP is rapidly evolving with new models, tools, and techniques being introduced regularly. In fact, 90% of the content in the presentation did not exist a few months ago, and the content about LangChain and LlamaIndex is set to become woefully outdated within a month or two because those libraries are coming out with so many new updates. GPT-4 is evidence of the fast pace of development in the field. #NLP #GPT4 #MachineLearning
  - Instruction tuning is a powerful technique for improving LLMs and making them more aligned with human preferences. OpenAI's Instructor-GPT paper introduced the use of reinforcement learning and human feedback to align LMs/LLMs with human preferences. #InstructionTuning #LLMs #ReinforcementLearning
  - Evaluations are ongoing to determine the full capabilities of LLMs. The speaker notes that LLMs are good at following instructions and query understanding, but their limitations are not fully understood yet, especially in their reasoning capabilities. #LLMs #Evaluations #MachineLearning
  - Being 99% accurate is not enough for many applications, especially if the failure cases are unpredictable. This is true for self-driving cars and may also be the case for a wide variety of NLP applications. #MachineLearning #NLP #Accuracy #SelfDrivingCars
- Integration of LLMs with external tools
  - Language models are being integrated with various external tools like code interpreters, search engines, APIs, databases and other kinds of datastores, facilitated by Python libraries like Llama Index and LangChain. #NLP #AI #LLMs
  - The Holy Grail we are aspiring towards involves a LLM automatically decomposing a query into manageable subtasks, and calling appropriate external services to solve the subtasks if necessary. Currently, this approach is impractical for many usecases, and a lean approach is utilized where the external service is called to fetch relevant context and the LLM acts upon that context to generate the response. #AI #taskautomation
  - LLMs can use task decomposition and agents to dynamically determine which tool to use to answer a question, and custom agents can be created to enable LLMs to answer questions more effectively. #LLMs #AI #taskdecomposition
  - LLMs are getting closer to fulfilling the promise of cross-document information retrieval, where information needs can be satisfied by going through multiple resources. #LLMs #AI #crossdocumentIR
  - External sources of information can enhance LLMs' performance, such as using retrieval models to map a query to entries in an index and returning it with adjacent sentences to provide context. #LLMs #AI #informationretrieval
  - OpenChatKit is a new LLM toolkit containing a 20 billion instruction tuned model based on GPT-NEOX, which can be used to automate tasks like answering complex questions and filtering search results. #LLMs #AI #OpenChatKit
  - It is possible for LLMs to generate python code to perform mathematical operations and invoke a code interpreter that can execute those operations. It is also feasible for an LLM to convert natural language queries into SQL queries, provided the schema is specified in the context, enabling them to answer aggregation-level queries. #LLMs #AI #SQL
  - LLMs can construct API calls and browse the web for answers, such as answering a natural language query about the lowest stock price of Apple in the last 10 years or the weather in Toronto. #LLMs #AI #APIcalls
  - LamaIndex provides a wide range of data connectors to import your own data like web pages, PDFs, Discord data, GitHub data, Google Docs data, notion data, Twitter data, and more. #LLMs #AI #LamaIndex
  - Different types of indices include list index, keyword table index, vector store index, tree index and more, with each having its unique advantages and limitations. The vector store index is one of the most effective versions of indices. #LLMs #AI #indices
- Use cases of LLMs
  - Language models break down complex questions into manageable components. For example, they can answer "who was the CTO of Apple when its share price was lowest in the last 10 years?" by finding the date of the lowest share price and the CTO on that date.
  - LLMs can filter out irrelevant results and automate tasks like flight searches. They call external APIs and databases and then synthesize coherent answers based on the output.
  - LLMs can answer questions about a company's policies, product planning, or any other information stored in Google Docs or Notion by using the data connectors provided by Lama index.
  - LLMs can ensure answers don't contain personal identifiable information or misinformation using a moderation chain. Making an LLM good at a particular domain is exciting, as passing exams in a particular domain is easy due to data contamination.

_Resources_

- [Augmented Language Models: a Survey](https://arxiv.org/abs/2302.07842)
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)
- [Iterated Decomposition: Improving Science Q&A by Supervising Reasoning Processes](https://arxiv.org/abs/2301.01751)
- [Demonstrate-Search-Predict: Composing retrieval and language models for knowledge-intensive NLP](https://arxiv.org/abs/2212.14024)
- [LangChain Docs](https://langchain.readthedocs.io/en/latest/)
- [LlamaIndex (formerly GPT-Index](https://gpt-index.readthedocs.io/en/latest/index.html)

**Suhas Pai (CTO @ Bedrock AI)**

[Suhas](https://www.linkedin.com/in/piesauce/) is the CTO & Co-founder of Bedrock AI, an NLP startup operating in the financial domain, where he conducts research on LLMs, domain adaptation, text ranking, and more. He was the co-chair of the Privacy WG at BigScience, the chair at TMLS 2022 and TMLS NLP 2022 conferences, and is currently writing a book on Large Language Models.
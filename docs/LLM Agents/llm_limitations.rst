Exploring the agency limits of today’s LLMs
===========================================

GPT-4 and similar LLMs, powered with the ability to interface with
external systems, have ushered in a whole variety of use cases into the
realm of possibility that were previously considered impossible.
However, possibility doesn’t imply feasibility, with several limiting
factors like effective retrieval hindering implementation. Tools like
langchain and llamaindex are possibly the most impactful libraries of
the year, but they are not a panacea to all problems. We will explore
some of the limiting factors, approaches to tackle them, and showcase
cutting-edge use cases that make the most of current capabilities.

`SLIDES <#>`__ \| `RECORDING <https://youtu.be/7kNgnqgETGo>`__

**SUMMARY**

1.  The talk explores the extreme limits and limitations of using LLMs
    in production, as well as how to address these limitations.
2.  Evaluating LLMs is challenging, especially when dealing with the
    strongest performing model like Gp4, which could be updated at any
    time without knowledge of the training process.
3.  Retrieval is often the limiting factor in startups that use a
    combination of LangChain, LammaIndex, vector databases, and GPT4.
4.  Context size limitations are also a concern, with 32,000 tokens not
    being enough and the way context is used being inefficient.
5.  Other limitations discussed include calibration and factuality.
6.  LLMs can be difficult to use in production, especially for use cases
    where the threshold for accuracy is high.
7.  Custom models can be better for domain-specific data than large
    language models.
8.  LLMs are good at code generation, summarization, instruction
    following, tuning, and reinforcement learning.
9.  There is a debate about whether LLMs truly understand language,
    especially in the context of reasoning tasks.
10. Evaluating LLMs can involve comparing them to smaller models and
    being aware of their limitations in terms of bias amplification and
    memorization.
11. Inverse scaling prize is a method for evaluating LLMs that compares
    their performance to their size.
12. Bias amplification and overconfidence can be concerns when using
    larger language models.
13. U-shaped performance can occur with LLMs, where performance
    initially decreases as the model size increases, but then improves
    at larger sizes.
14. Some tasks, such as algebra questions and directional orientation,
    can be challenging for LLMs to solve.
15. The frequency of certain terms in the input can impact LLMs’
    performance on certain tasks.
16. Tools such as Snoopy and Koala can be used to evaluate LLMs and
    identify test set contamination.
17. Test set contamination can amplify reasoning errors and should be
    avoided.
18. Consolidation towards a generalist model that can solve multiple
    tasks is a driving force, but it may not be appropriate for all use
    cases.
19. Smart product design may involve not relying on language models for
    tasks they are not currently good at.
20. Prompt engineering can be used to limit the context and prevent the
    model from fetching information from memory.
21. Tasks decomposition is important when asking LLMs to answer complex
    questions.
22. LLMs may need to leverage external tools to answer certain
    questions, such as APIs or search engines.
23. Tool integration paradigms include asking user queries and
    decomposing queries into a set of tasks.
24. Strategies for task decomposition include matching the description
    of a tool with the user query and chaining services together.
25. There are projects working on packaging everything into a single
    tool for user queries, but they are not yet production-ready.
26. Vector stores are being used for retrieval augmented LLMs.
27. Cosine similarity is a measure of geometric distance between two
    vectors in an embedding space, but it underestimates the similarity
    of frequent words.
28. Sentences can have multiple facets and can be interpreted
    differently depending on the context.
29. Instruction fine-tune text embeddings can be used to create
    embeddings tailored to solving specific tasks.
30. Faceted embeddings can be used to focus on particular facets of an
    input.
31. Query expansion and chaining of thought can help increase the
    likelihood of finding the right cosine similarity, but fundamental
    limitations still remain.
32. Precision versus recall is important in answering questions within a
    context window.
33. Production readiness of a tool depends on the complexity of user
    queries and the distribution of relevant information across the
    corpus.
34. Fine-tuning models for specific problems works better than general
    large language models, especially if they are domain-adapted and
    continue to be pre-trained.
35. In-house instruction tuning can be promising for domain-specific
    data sets.
36. The prompt strategy for fine-tuning models can be promising,
    especially with prompt compression during instruction tuning.

**Suhas Pai (CTO @ Bedrock AI)**

`Suhas <https://www.linkedin.com/in/piesauce/>`__ is the CTO &
Co-founder of Bedrock AI, an NLP startup operating in the financial
domain, where he conducts research on LLMs, domain adaptation, text
ranking, and more. He was the co-chair of the Privacy WG at BigScience,
the chair at TMLS 2022 and TMLS NLP 2022 conferences, and is currently
writing a book on Large Language Models.

.. image:: https://github.com/Aggregate-Intellect/practical-llms/blob/main/docs/img/SuhasP.jpg
  :width: 600
  :alt: Suhas Pai Headshot
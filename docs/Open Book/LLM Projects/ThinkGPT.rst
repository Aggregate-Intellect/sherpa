
=========================================================
​ThinkGPT: Agent and Chain of Thought techniques for LLMs
=========================================================
*Alaeddine Abdessalem* 

Summary 
-------
ThinkGPT is a Python library designed to empower Large Language Models (LLMs) with advanced thinking and reasoning capabilities and to allow developers to create agents with LLMs. This talk will provide an overview of ThinkGPT's key features and how it addresses challenges such as limited context, one-shot reasoning, and decision-making. The library offers thinking building blocks like memory, self-refinement, knowledge compression, and natural language conditions. We will explore examples demonstrating ThinkGPT's applications, including teaching new languages to LLMs and enabling them to understand and generate code using new libraries. Additionally, we'll discuss the concept of generative agents and how they can be implemented with ThinkGPT. Join this talk to unlock the potential of ThinkGPT and leverage thinking abilities in your language models.

Alaeddine Abdessalem introduces Think GPT, a library designed to build AI projects with large language models (LLMs) and overcome their limitations. The library offers features such as long memory, self-refinement, compression, and natural language conditions to enhance LLM applications. It provides an easy-to-use API and leverages Dockery as an intermediate layer for vector database interactions. The library supports code generation and the implementation of generative agents in video games. Minimal infrastructure is required to get started, and the library currently supports OpenAI models. 

`RECORDING <https://youtu.be/hhX8b_jVvQI>`__

Topics: 
-------
Overview of LLMs and their limitations 
	* LLMs have thinking capabilities but limited knowledge and context size 
	* Think GPT aims to leverage LLM advantages while addressing limitations 
Features of Think GPT 
	* Long memory: inject external knowledge into LLM 
	* Self-refinement: fix code or output based on previous criticism 
	* Compression: samurai and summarize methods for fitting knowledge into limited context 
	* Natural language conditions: make decisions using LLMs instead of heuristics 
Demonstration of Think GPT 
	* Model initialization and injecting knowledge into LLM 
	* Usage of long memory, self-refinement, natural language conditions, and compression in practical examples 
Comparison with other libraries 
	* Chainline focuses on language model interface, while Think GPT offers additional functionalities like self-refinement and generative agents 
	* AllenNLP specializes in NLP tasks, while Think GPT's strength lies in integration with LLMs 
	* Choose library based on specific project needs and requirements 
Dockery and its role in Think GPT 
	* Dockery simplifies usage of vector databases and provides a unified API 
	* Dockery is not a competitor to other vector databases but a library that simplifies their usage 
Business use cases of Think GPT 
	* Code generation: LLMs can generate code with external memory augmentation 
	* Generative agents in video games: Unity platform enables communication with players using natural language 
Infrastructure requirements 
	* Minimal infrastructure needed to get started with Think GPT 
	* OpenAI API key and library installation are sufficient 
	* Dockery and memory store implementation eliminate initial need for vector database 
	* Scaling and GPU usage might be required for larger projects or on-premises servers 
Future developments and community involvement 
	* Token usage tracking might be added in the future 
	* Think GPT is an open-source project and welcomes contributions 
	* Users can raise issues, submit pull requests, and suggest important features or use cases 

----

**Alaeddine Abdessalem (MLE @ Jina AI)**

`Alaeddine Abdessalem <https://www.linkedin.com/in/alaeddine-abdessalem-549b65169/>`__ is a Machine Learning Engineer at Jina AI. At Jina AI, he contributes to open source projects like DocArray, a library for multimodal data and vector search and Jina, a framework for AI applications and services. He is also the author of ThinkGPT, a library for Chain of Thought techniques for LLMs.

.. image:: ../_imgs/alaeddina.jpeg
  :width: 400
  :alt: Alaeddine Abdessalem Headshot
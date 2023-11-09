

======================================
Building a Topic Modeling Model: Ernie 
======================================
*Richie Youm* 

Summary 
-------
LLM is a powerful tool, yet not a silver bullet to replace all traditional ML models. At Wealthsimple, we leveraged LLM to accelerate processes of model development that would have previously taken months, to just a couple of weeks. We will discuss the development process of our topic model, ERNIE, and how LLM was used for the project.

Richie Youm, a data scientist at WealthSimple, shared the experiences of building a topic modeling model called Ernie. The goal of the Ernie model was to provide a smoother experience for clients and improve service level agreements. They explored techniques like LDA and BERTopic but faced challenges with inconsistent results and noisy data. They rebuilt the taxonomy using GPT models and developed an efficient routing system for improved customer service. The presentation also discussed the potential for an automated customer service system and the importance of data privacy and security. 

`RECORDING <https://youtu.be/g9dSt1cCW5k>`__

Topics: 
-------
Exploring GPT Models 
	* GPT models were considered for direct classification but faced challenges with hallucination and domain knowledge 
	* Prompt engineering on the ChatGPT API showed promising results but was not sufficient 
Rebuilding the Taxonomy 
	* GPT was used as a tool to assist in taxonomy development 
	* The existing taxonomy had limitations and GPT was used to address them 
Efficient Routing and Data Labeling for Improved Customer Service 
	* Challenges faced in handling sensitive customer data and the need for efficient routing and data labeling 
	* Development of a PII remover using `Presidio <https://github.com/microsoft/presidio>`__ and Transformers to anonymize sensitive data 
	* LLM used for topic and subtopic taxonomy extraction 
	* Ernie, Efficient Routing for New and Improved Efficinecy system, built for topic and subtopic predictions 
Output and Examples of a Topic Modeling Project 
	* Examples of the output of the topic modeling project highlighting the accuracy of predictions 
	* Importance of context in improving predictions 
	* High accuracy of subtopic predictions 
Potential for Automated Customer Service System 
	* Discussion on the potential for the project to lead to an automated customer service system 
	* Other projects being worked on, including a research AI project for trading 
	* Possibility of adding knowledge base into a chatbot for better customer service 
Follow-up Questions
	* Discussion on creating a tool that asks follow-up questions based on user input and system analysis 
	* Interest in formal formats like ontologies and knowledge graphs 
	* Discussions with the builder of `taxGPT <https://taxgpt.ca/pages/about>`__ 
Data Privacy and Security 
	* Importance of data privacy and measures taken to ensure it 
	* Open-source library for LLM Gateway and different levels of PII removal 
	* Plan to open-source a PII remover 
Conclusion 
	* Importance of improving the taxonomy and incorporating domain knowledge 
	* Potential for automated customer service systems 
	* Importance of data privacy and security 
	* User feedback and potential use of formal formats in the future 

----

**Richie (Seongmin) Youm (Data Scientist @ Wealthsimple)**

`Richie <https://www.linkedin.com/in/richieyoum/>`__ is a full-stack data scientist specializing in Natural Language Processing. At Wealthsimple, Richie dedicates his expertise to integrating cutting-edge NLP technology across the company's products. Notably, he plays a pivotal role in leading implementation of LLM across the company’s products. His responsibilities encompass all aspects of productionalizing LLM, from developing various Proof-of-Concepts and leading discussions, to developing internal LLM guidelines, ensuring responsible usage, and providing education to colleagues in data science and engineering.

.. image:: ../_imgs/RichieY.png
  :width: 400
  :alt: Richie Youm Headshot
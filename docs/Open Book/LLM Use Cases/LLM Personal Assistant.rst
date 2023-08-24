
======================
LLM Personal Assistant
======================
*Denys Linkov* 

Summary 
-------
We’ve seen the demos on how to answer questions from a document, but how does it work behind the scenes? In this talk we’ll focus on how embeddings and LLMs work for information retrieval tasks, and how to measure their effectiveness. We’ll also describe some the UX challenges when exposing these natural language retrieval systems to end users.

Denys Linkov discusses the use case of conversational AI and information retrieval, the emergence of information retrieval tasks, benchmarking retrieval systems, combining document retrieval with personas, proof of concept for instant assistance through information retrieval, retrieval system and embeddings, design choices and considerations in LLM development, challenges of enterprise search, and the current state of the generative AI industry. 

`SLIDES <https://pitch.com/public/a81ef407-e7de-487d-89b8-e4765625b3fc>`__
\| `RECORDING <https://youtu.be/w9Wt-4MMl8c>`__

Topics: 
-------
Emergence of Information Retrieval Tasks 
	* Information retrieval tasks gained popularity after 2023 
	* Open domain question answering (ODQA) models were not widely explored or demonstrated on social media platforms 
Benchmarking Retrieval Systems 
	* The 'beer' benchmark incorporates various datasets to evaluate retrieval system performance 
	* Benchmarking is important to accurately evaluate retrieval system effectiveness 
Combining Document Retrieval with Personas 
	* Project 'Get Darth' demonstrates combining document retrieval with personas 
	* Large language models make it easy to implement this concept 
Proof of Concept 
	* Proof of concept 'You Q&A Test' explores instant assistance through information retrieval 
	* Architecture involves connecting front end to API deployed on Google Cloud Run 
	* Utilizes embeddings and large language models for retrieval and preprocessing 
Retrieval System and Embeddings 
	* Retrieval system compares similarity between questions and potential answers 
	* Providing useful and conversational responses is important 
	* Choosing the right embedding model is crucial 
Design Choices and Considerations in LLM Development 
	* Consider cost and latency when using powerful models 
	* Select the optimal model for the platform 
	* Develop a testing framework to validate parameters, models, and prompts 
Challenges of Enterprise Search 
	* Determining relevance of documents and chunks in search queries is complex 
	* Consider simplicity in building and deploying assistants 
	* Human validation and feedback are important 
	* Address uptime and response time challenges 
Current State of the Generative AI Industry 
	* Generative AI companies have received significant funding 
	* Different companies offer different advantages and integration options 
	* Voiceflow simplifies conversational design without coding 
	* Consider user perspectives and the difficulty of determining importance in a document 
Considerations in Working with Large Language Models 
	* Balance uptime and service availability 
	* Implement synchronous processes for higher priority tasks 
	* Consider simplicity, user experience, and streaming in chatbot interfaces 
	* Understand functional and non-functional requirements 
	* Focus on accomplishing the intended task before experimenting with new models 

----

**Denys Linkov (ML Lead @ Voiceflow)**

`Denys <https://www.linkedin.com/in/denyslinkov/>`__ is the ML lead at
Voiceflow focused on building the ML platform and data science
offerings. His focus is on realtime NLP systems that help Voiceflow’s
60+ enterprise customers build better conversational assistants.
Previously he worked at large bank as a senior cloud architect.

.. image:: ../_imgs/denysl.jpeg
  :width: 400
  :alt: Denys Linkov Headshot
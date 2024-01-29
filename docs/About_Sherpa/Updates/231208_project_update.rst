

===========================================================
Testing Strategies for Large Language Models: Sherpa Update 
===========================================================
*Percy Chen* 

Summary 
-------
​In this session, we explored the unique challenges and methods of testing for Large Language Model- (LLM)-based systems, contrasting them with traditional software testing approaches. Using our open-source Sherpa project as a case study, we demonstrated practical implementations of these testing strategies, highlighting how they ensure robustness and reliability of the components interacting with LLMs. The session also included the latest updates to the Sherpa project, ending with some open questions and challenges we will tackle next.

`RECORDING <https://youtu.be/g1CHPoFKGt4>`__

Topics: 
-------
Overview of the Sherpa Project 
	* The Sherpa project aims to create a collaborative multi-agent framework that allows human interaction. 
	* The project includes a question answering agent in the Slack workspace and integrates various tools via APIs. 
	* The goal of the current sprint is to test the functionality of these components and ensure the system's robustness. 
Testing Roadmap 
	* The testing roadmap progresses from limited functionality to a more comprehensive system-level testing framework. 
	* Efforts have been made to set up a suitable testing environment using GitHub Actions. 
	* The roadmap aims to establish a reasonable testing approach that enables continuous integration and intervention. 
Testing Objectives 
	* The system should be able to handle different types of responses and provide relevant links and references to the user (citation verification). 
	* Even in cases of incorrect results, the system should notify the user and suggest alternative actions. 
	* The impact of updates from Open AI APIs on Sherpa's performance needs to be assessed and mitigated. 
	* The interactions between agents in the multi-agent framework need to be tested and their sequential dependencies maintained. 
	* The cost of using open APIs must be considered to avoid unnecessary expenses during testing. 
Separation of Testing Concerns 
	* Tests have to handle the diversity and variations of the model's responses. 
	* Frequent and more deterministic software testing should ensure that the rest of the system functions as expected. 
	* Given that most prompts are crafted on the fly by the system, structure and correctness of prompts have to be tested. 
Testing Strategies for Large Models 
	* Unit testing focuses on testing specific functionalities within the system to ensure their correctness for example to ensure a model response has the correct format. 
	* Integration testing examines the interactions between different components for example to ensure the output of one model fed into another constructs the right prompt. 
	* Having a robust testing system ensures that issues can be identified and resolved at an early stage given the experimental and in-progress nature of the project. 
	* Use case testing ensures that the model performs correctly in real-world scenarios. 
	* Acceptance criteria for tests requires a certain level of determinism which is a challenge for LLMs. That is addressed by categorizing test runs into frequent and infrequent categories. 
	* For frequent ones, "mock testing" simulates the behavior of LLM components without actually calling external APIs (costly).
	* Infrequently, tests are done by calling third party APIs and the system utilizes caching to store input and response for each test case for mock testing. 
Unified Testing Approach 
	* A unified testing approach combines mock testing and real testing to save time and effort. 
	* During frequent test runs, the cached responses are loaded, simulating the behavior of the large model. 
	* This approach ensures consistency and efficiency in testing. 

----

**Percy Chen (PhD Student @ McGill University)**

`Percy <https://www.linkedin.com/in/boqi-chen/>`__ is a PhD student at
McGill University. His research interests include model-driven software
engineering, trustworthy AI, verification for ML systems, Graph Neural
Networks, and Large Language Models. Percy leads R&D collaboration
between McGill University and Aggregate Intellect.

.. image:: ../_imgs/percyc.jpeg
  :width: 400
  :alt: Percy Chen Headshot
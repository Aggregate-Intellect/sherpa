

==========================================================================
Introducing Council: A Framework for Developing Generative AI Applications 
==========================================================================
*Daniel Kur* 

Summary 
-------
Daniel Kur provides an overview of the open source project called Council, a framework for developing generative AI applications using collaborative agents. He discusses the key concepts of control flow and evaluation, as well as the importance of constraints and integration with existing tools. Kur also addresses audience questions regarding parallel execution, hallucination, and the role of the controller. Overall, Council offers advanced control and predictability for creating reliable and accurate generative AI applications. 

Topics: 
-------
Control Flow and Evaluation 
	* Control flow determines how user messages are routed to different parts of the software 
	* Evaluation component assesses the success and relevance of agent responses 
	* Control flow and evaluation enable the creation of sophisticated agents 
Constraints and Integration 
	* Council prioritizes constraints such as budget and time limitations 
	* Supports multi-threading and parallel execution for improved efficiency 
	* Integrates with existing tools and ecosystems 
Components of Council 
	* Controller handles control flow and selects chains of skills to execute 
	* Chains are sequences of skills that perform specific tasks 
	* Evaluator assesses the results of executed chains and provides the final response 
	* State management facilitates development by providing access to conversational history and previous chain iterations 
Parallel Execution and Agent-to-Agent Work Allocation 
	* Currently, chains are executed sequentially but skills within chains can be executed in parallel 
	* Future work aims to enable parallel execution of chains and agent-to-agent work allocation 
Addressing Hallucination 
	* Council provides mechanisms to address hallucination through the evaluator 
	* Fact tracking and real-time information retrieval skills help avoid providing inaccurate responses 


=======================================
Reflexion - A Reflection-Based Approach 
=======================================
*Noah Shinn* 

Summary 
-------
Noah Shinn discussed the progress made in large language models (LLMs) and machine learning research. He highlighted the development of a self-reflective agent that can learn from its mistakes and improve its performance. Challenges remain in defining rewards for subjective scenarios. This research has the potential to revolutionize various applications, including question answering and task completion. 

Topics: 
-------
	Motivation and Approach 
		* The initial goal was to solve complex problems that cannot be easily solved using an auto-regressive approach. 
		* The react prompting approach was found to be the best method for enabling foresight in decision-making. 
		* A reflection-based approach built on top of react was proposed to allow the agent to reflect on its mistakes and optimize future actions. 
	Self-Reflection and Heuristic Design 
		* Self-reflection involves the agent analyzing its past trials and providing criticism and instructions for future attempts. 
		* Generating natural language self-reflections allows the agent to gain insights into its behavior and identify key errors. 
		* A heuristic was designed to detect hallucination and inefficient behavior by checking for repeated actions and observations. 
	Role of Rewards and Challenges 
		* The reward function is kept simple, with a binary classification of success or failure. 
		* Defining rewards for subjective scenarios, such as question answering, is challenging and requires further research. 
	Comparison to Auto GPT and Future Directions 
		* Auto GPT performs well on complex tasks but is subject to hallucination. 
		* Future work may involve exploring critic models further to improve error identification. 


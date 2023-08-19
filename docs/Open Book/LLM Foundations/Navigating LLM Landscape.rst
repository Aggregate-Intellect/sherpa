
========================
Navigating LLM Landscape
========================
*Suhas Pai* 

Summary 
-------
The presentation discussed the selection and evaluation of Large-Language Models (LLMs). It covered topics such as the challenges of determining beneficial LLMs, the evaluation and selection process, the complexities of calculating evaluation metrics, the use of Elo ratings for evaluation, the limitations and challenges of LLMs, their applications in various domains, the importance of choosing the right language model, the relevance of pre-training data sets, and the impact of data duplication. The presentation also touched on working with long context, the importance of evaluation in practical use cases, the distinction between chat tuning and instruction fine-tuning, and the interaction between small and large models in creating specific use cases. 

Topics: 
-------
	Determining Beneficial LLMs 
		* There is no straightforward answer to determining beneficial LLMs. 
		* Consider factors such as model architecture, tokenization, vocabulary, learning objective, pretraining dataset, cost, and inference latency. 
		* Pai's own thought process involved using 90% of their own models and 10% of GPT. 
	Evaluation and Selection of LLMs 
		* Consider different types of LLMs and the necessity of fine-tuning for various tasks. 
		* Be cautious of relying solely on rankings and metrics from sources like the Open LLM Leaderboard. 
		* Elo ratings, based on human-rated evaluation, provide a more reliable measure of model performance. 
	Challenges of Evaluating LLMs 
		* Human bias can affect the evaluation of LLMs. 
		* Test benches can be used to evaluate LLMs for specific tasks. 
		* Augmentations like instruction tuning can improve LLM performance. 
		* Different LLM models have varying training methods and datasets for instruction tuning. 
	Limitations and Challenges of LLMs 
		* LLMs have limited context and can struggle with complex tasks and hallucinations. 
		* Smaller models like BERT have limitations in abstract reasoning and certain writing styles. 
		* Choosing the right language model involves considering factors like latency, flexibility, uncertainty estimates, and debugability. 
		* Pre-training data sets and data cleaning are important for model performance. 
		* Data duplication and its impact on model training are subjects of ongoing debate. 
	Working with Long Context 
		* Working with long context in LLMs presents challenges in retrieving information. 
		* Analogous to having multiple tabs open in a browser, the ability to retrieve information becomes more challenging as the number of tabs increases. 
	Importance of Evaluation in Practical Use Cases 
		* Evaluation datasets used in the field can be easily gamed and may not showcase the true capabilities of LLMs. 
		* Building internal evaluation test benches tailored to specific industries or use cases is important. 
		* Jumping from one model to another may not necessarily lead to significant improvements. 
	Distinction Between Chat Tuning and Instruction Fine-Tuning 
		* Smaller models handle decision-making, while larger models excel in extreme summarization. 
		* Instruction fine-tuning helps models follow human instructions more easily. 
	Interaction Between Small and Large Models 
		* Tasks should be divided into subtasks based on the capabilities of the models. 
		* Determining which model is better suited for a particular task requires intuition and a deep understanding of the models' capabilities. 


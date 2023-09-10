
=========================================================================
Navigating LLM Landscape: ​Which open-source LLM to choose for your task?
=========================================================================
*Suhas Pai* 

Summary 
-------
Dozens of open-source LLMs have pounced on the scene in the last several months. Can you actually replace chat-gpt/gpt-4 with them? What are they useful for and how can you use them in production? How do you select one from dozens of available models? What are LLM evaluation measures actually measuring? In this talk, we will explore these questions and try to provide a framework to resolve the build vs buy conundrum that many individuals and organizations find themselves in.

The presentation discussed the selection and evaluation of Large-Language Models (LLMs). It covered topics such as the challenges of determining beneficial LLMs, the evaluation and selection process, the complexities of calculating evaluation metrics, the use of Elo ratings for evaluation, the limitations and challenges of LLMs, their applications in various domains, the importance of choosing the right language model, the relevance of pre-training data sets, and the impact of data duplication. The presentation also touched on working with long context, the importance of evaluation in practical use cases, the distinction between chat tuning and instruction fine-tuning, and the interaction between small and large models in creating specific use cases. 

`SLIDES <#>`__ \| `RECORDING <https://youtu.be/6PPZwwgfbMY>`__

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

----

**Suhas Pai (CTO @ Bedrock AI)**

`Suhas <https://www.linkedin.com/in/piesauce/>`__ is the CTO &
Co-founder of Bedrock AI, an NLP startup operating in the financial
domain, where he conducts research on LLMs, domain adaptation, text
ranking, and more. He was the co-chair of the Privacy WG at BigScience,
the chair at TMLS 2022 and TMLS NLP 2022 conferences, and is currently
writing a book on Large Language Models.

.. image:: ../_imgs/SuhasP.jpg
  :width: 400
  :alt: Suhas Pai Headshot
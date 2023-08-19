
===========================================
Designing Large Language Model Applications 
===========================================
*Suhas Pai* 

Summary 
-------
Suhas Pai discusses various aspects of large language models and machine learning research, including prompt engineering, model selection, prompting in deployed applications, challenges in deploying GPT-based tasks, estimating token probabilities, determining correctness of answers, token frequency in pre-training data sets, limitations of retrieval models, vocabulary sizes, calibration in practical use cases, and the underlying architecture and training process of large language models. 

Topics: 
-------
	Prompt Engineering 
		* Prompt engineering may not be as crucial in the future as models improve and become more aligned with human performance. 
		* Certain prompt engineering techniques, such as chain of thought prompting, have proven to be impactful and useful. 
	Model Selection 
		* Augmented models, which include instruction tuning, reinforcement learning, and multitask training, are more suitable for human use. 
		* Smaller models may be sufficient for specific use cases. 
	Prompting in Deployed Applications 
		* Both hard prompts and soft prompts are used in applications. 
		* Prompt tuning is still more of an intuitive process rather than a scientific one. 
	Challenges in Deploying GPT-based Tasks 
		* Uncertainty estimates, particularly in the finance industry, are important for trust and predictability. 
		* Model calibration can address the challenge of unreliable outputs, but it can be more challenging for large language models like GPT. 
	Estimating Token Probabilities and Determining Correctness of Answers 
		* Heuristics and scoring methods like Blue and ROUGE are not effective in solving these problems. 
		* Asking for multiple generations and using heuristics or smaller models can improve the accuracy of answers. 
		* Decoding strategies used in LLMs, especially with external APIs like OpenAI, are limited. 
	Token Frequency in Pre-training Data Sets 
		* Tokens with higher frequency in the data set are more likely to produce accurate results when used in prompts. 
		* The quality of the retrieval model is crucial in determining the accuracy of the language model's responses. 
		* Using a retrieval or embedding model trained on abstracts could be a more effective approach. 
	Vocabulary Sizes 
		* Models like Bloom, which are multilingual, have larger vocabulary sizes to accommodate different languages. 
		* Additional tokens in the vocabulary could be for special processing, such as code snippets or comments. 
	Integration between Search Engines and Large Language Models 
		* Leveraging ideas and optimization techniques from search engines could improve retrieval in language models. 
		* Optimizing search engines is a challenging task, and finding a relevant metric for ranking is complex. 
	Calibration in Practical Use Cases 
		* Calibration is more useful when you have access to your own models and can adjust the output probabilities. 
		* Calibration becomes more challenging when language models are part of a larger system with external models. 
	Underlying Architecture and Training Process of Large Language Models 
		* Large language models are typically built using deep neural networks with multiple layers of interconnected nodes. 
		* Training involves feeding the model with a large corpus of text data and adjusting the weights of the network. 
		* The size and diversity of the training data play a crucial role in the performance of large language models. 


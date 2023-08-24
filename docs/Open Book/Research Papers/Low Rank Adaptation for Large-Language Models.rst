
=============================================
Low Rank Adaptation for Large-Language Models
=============================================
*Yujing Yang* 

Summary 
-------
This presentation introduces the concept of low-rank adaptation for large language models as an alternative to fine-tuning. The methods, Laura and the factorization approach, reduce the number of trainable parameters and resource requirements while maintaining or improving performance. They are applicable to various neural network architectures and have the potential to revolutionize the field of language model adaptation. 

Topics: 
-------
	Increasing size of large language models 
		* Large language models like GPT-3 have billions of parameters 
		* Adapting these models using fine-tuning is not feasible due to resource requirements 
		* Alternative methods are needed for achieving similar performance with lower resource requirements 
	Existing solutions: adapter layers and prefix tuning 
		* Adapter layers allow training specific layers for different tasks but introduce inference latency and increase parameters 
		* Prefix tuning keeps most parameters frozen and introduces a small task-specific vector, but it is difficult to operate and optimize 
	Introduction of low-rank adaptation method (Laura) 
		* Laura injects trainable rank decomposition matrices into each layer of the transformer architecture 
		* Reduces trainable parameters by up to 10,000 times and GPU memory requirements by three times 
		* Performance is comparable or better than full fine-tuning 
		* Feature selection process improves results 
	Applicability of Laura 
		* Suitable for any neural network with weight matrices 
		* Focused on transformer architecture, applied to models like BERT, RoBERTa, and GPT 
	Advantages of Laura 
		* Achieves similar performance to fine-tuning 
		* Reduces resource requirements 
		* No additional inference latency 
	Factorization technique used in the paper 
		* Utilizes the idea of factorization by training two small matrices (A and B) to approximate the large matrix 
		* Reduces the number of parameters that need to be learned 
		* Takes advantage of sparsity or low rank of the large matrix 
		* Smaller rank size (R) leads to faster training and reduced computational requirements, but may decrease adaptation quality 
	Practical benefits of low-rank adaptation 
		* Require less memory and reduce RAM consumption during training 
		* Smaller checkpoint sizes 
		* Allow for training with fewer GPUs and lower hardware requirements 
		* No additional latency during inference 
	Discussion and Q&A 
		* Attendees asked questions about the popularity of large-language models, absence of additional latency, necessity of pre-trained models, and applying the technique to the entire network 
		* Speaker provided explanations and clarifications 


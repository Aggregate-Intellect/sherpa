
=================================================
Understanding Compositionality in Language Models
=================================================
*Percy Chen* 

Summary 
-------
The presentation discussed the compositionality in language models, focusing on the performance of large language models in question-answering tasks. It explored the concept of compositionality and its significance in evaluating the model's ability to combine information from sub-questions to answer the overall question. The presentation also discussed the use of self-ask and external tools to improve the model's reasoning and composition abilities. 

Topics: 
-------
	Compositionality Gap 
		* The compositionality gap measures the model's ability to compose answers from sub-questions accurately. 
		* It focuses on the model's ability to combine evidence to derive the final answer accurately. 
		* The compositionality gap does not significantly decrease as the model size increases, indicating that models' ability to memorize facts surpasses their ability to answer more complex questions. 
	Experimental Results 
		* Experiments conducted on GPT-3 and DaVinci models showed that self-ask significantly increased the performance of the models. 
		* Using a search engine for sub-question handling further improved the performance in some cases. 
		* Further research is needed to address the limitations and challenges in handling more complex questions. 
	Challenges and Limitations 
		* Large language models lack theoretical guarantees and are often treated as black boxes, limiting our understanding of their inner workings. 
		* Using smaller models alongside large language models can optimize performance and reduce computational resources. 
		* Prompt tuning has limitations, particularly in accessing gradients in black box models. 
		* As the number of hops and inferences increases, the computational costs and latency also increase. 
	Q&A Session 
		* Attendees raised concerns about the lack of transparency in large language models and the need for more scientific research. 
		* The distinction between reasoning and composition in language models was discussed. 
		* Saving reasoning plans in large language models and the dissectability of questions were also mentioned. 


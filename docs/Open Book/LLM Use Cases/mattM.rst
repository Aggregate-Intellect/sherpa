

==================================================================
Maximizing Impact through Synthetic Data and Large Language Models 
==================================================================
*Matt McInnis* 

Summary 
-------
This talk details Typist's journey of building a popular feature in our upcoming product by leveraging LLM services and the resulting impact on their business. Matt shares examples of their initial exploratory analysis using ChatGPT's web UI through to our final API-driven pipeline using gpt-3.5-turbo and lessons learned along the way.

Matt's presentation showcases the use of large language models and synthetic data sets to address the digital divide and create inclusive educational tools. He highlights the challenges faced during implementation and the improvements made through a multi-step pipeline. The benefits of using large language models, such as explainability and increased productivity, are emphasized. The speaker's work at Typist aims to bridge the gap between technology access and education, ultimately making a difference in the lives of those they serve. 

`RECORDING <https://youtu.be/lQWQ4JROH3w>`__

Topics: 
-------
Addressing the Digital Divide 
	* Typist's mission is to reduce the digital divide by providing easy-to-use technology solutions 
	* Large language models are important in creating a medical office educational simulator 
	* The simulator requires the construction of complex synthetic data sets 
Ensuring Representation and Diversity 
	* Generated names in the synthetic data sets were not representative of the student population or the community they serve 
	* Ontario census data was used as a benchmark for ethnic and cultural diversity 
	* OpenAI's GPT 3.5 turbo was used to predict the ethnic or cultural origins associated with each name 
Implementation Challenges and Improvements 
	* Initial approach using AI labeler and GPT 3.5 turbo had limitations in determining name origins accurately 
	* Response times were longer than desired 
	* Multi-step pipeline incorporating generative knowledge prompting and chain of thought prompting techniques improved accuracy 
Benefits of Large Language Models 
	* Explainability provided by LLMs allows for backing up generated data with reasoning 
	* LLMs are cost-effective and easy to implement, improving development velocity and productivity 
	* LLMs have the potential to improve the efficiency of medical clinics and reduce negative patient outcomes 

**Matt McInnis (Founder @ Typist)**

`Matt McInnis <https://www.linkedin.com/in/mattmcinnis/>`__ is the Founder of Typist, an educational technology company aiming to help reduce the digital divide, a mathematician, programmer, data scientist and entrepreneur. Previously, he spent 7+ years as a college mathematics professor at Saskatchewan Polytechnic (sessional) and later Centennial College where he was the recipient of the 2012 Top Academic Faculty Member as awarded by the Centennial College Board of Governors'. In 2016 he was recruited to IBM Canada as one of the Ai leads on the North American Open Source Team where he helped large enterprises develop their strategy around machine learning and build out their fist use cases, and later joined Microsoft as an Ai lead in the customer success unit working with top Microsoft clients to build and scale their Ai efforts. He is an active mentor, speaker, former member of the steering committee for the annual Toronto Machine Learning Summit (TMLS), and volunteer on academic program advisory committees (PACs). He holds a BSc Mathematics, MSc Statistics.

.. image:: ../_imgs/MattM.png
  :width: 400
  :alt: Matt McInnis Headshot
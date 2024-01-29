

===============================================
Automatic Evaluation of Dialogue Systems at Ada 
===============================================
*Benedicte Pierrejean* 

Summary 
-------
Ada, a customer support company, has been working on automatic evaluation of dialogue systems. Their goal is to deliver an AI platform that enables businesses to automatically resolve customer service conversations with minimal effort. They have expanded their services beyond chatbots to include other channels like social media, SMS, and emails. To evaluate the performance of dialogue systems built using language models (LMs), Ada faces challenges with traditional evaluation metrics like BLEU and ROUGE, which limit creativity and do not account for scenarios that don't exist in historical datasets. 

`RECORDING <https://youtu.be/S9rkMqK3YNE>`__

Topics: 
-------
Recent Developments 
	* University of Stanford's health dataset and Chatbot Arena are recent developments in the field of evaluating dialogue systems.
	* Focus of this work is on enabling users to achieve their goals and evaluating the overall conversation between the LM and the user 
The BotvBot Testing Framework 
	* This work proposes the BotvBot testing framework for evaluating dialogue systems 
	* The framework consists of an offline phase and a test phase 
	* The offline phase of the BotvBot framework involves generating scenarios using a dialogue generator and assigning different personalities and occupations to simulated users
	* Simulated users are created using a dialogue generator and assigned different personalities and occupations 
	* Performance is evaluated using metrics like safety, accuracy, relevance, and trust 
	* Safety and accuracy of generated conversations are ensured by using an LM to simulate the user's responses and criteria to guide the LM's behavior
Automated Resolution Rate 
	* This framework measures the success rate of resolving customer inquiries without human involvement 
	* The automated resolution rate helps clients identify areas for improvement and can be applied to various customer support tasks   

----

**​Bénédicte Pierrejean (Sr. ML Scientist @ Ada)**

`​Bénédicte Pierrejean <https://www.linkedin.com/in/benedicte-pierrejean-25666b5a/>`__ is a Senior ML Scientist in the Applied Machine Learning team at Ada. She has a PhD in Natural Language Processing and is passionate about improving customer's experiences using ML.

.. image:: ../_imgs/BeneP.jpg
  :width: 400
  :alt: Bene Pierrejean Headshot